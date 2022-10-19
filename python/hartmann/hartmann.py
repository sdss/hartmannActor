#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-23
# @Filename: hartmann.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
import logging
import multiprocessing
import os
import pathlib
from dataclasses import dataclass
from functools import partial

from typing import TYPE_CHECKING

import numpy
import numpy.typing
import scipy.ndimage
from astropy.io import fits

from hartmann import config as default_config
from hartmann import log
from hartmann.exceptions import HartmannError


if TYPE_CHECKING:
    from clu.command import Command

    from hartmann.actor.actor import HartmannCommandType


__all__ = ["CameraResult", "HartmannCamera", "Hartmann", "HartmannResult"]


def nslice(i0: int, i1: int, j0: int, j1: int):
    """Returns a Numpy slice."""

    return numpy.s_[i0:i1, j0:j1]


def _shift_product(data1, data2, shift, order=3, mask=None, prefilter=False):
    """Shifts ``data2`` by ``shift`` pixels in the first axis
    and computes the sum of the product of the images.

    """

    if mask is None:
        mask = numpy.ones(data1.shape)

    shifted = scipy.ndimage.shift(data2, [shift, 0], order=order, prefilter=prefilter)

    return (data1 * shifted * mask).sum()


@dataclass
class HartmannResult:
    """Results for the Hartmann collimation."""

    spec: str
    camera_results: list[CameraResult]
    move: float
    rres: int
    bres: float
    bres_min: float
    residual_message: str
    success: bool


@dataclass
class CameraResult:
    """Result of processing Hartmann files for a camera."""

    camera: str
    success: bool = False
    focused: bool = False
    piston: float = 0.0
    ishifts: numpy.ndarray = numpy.array([])
    coeffs: numpy.ndarray = numpy.array([])
    best: int = 0
    offset: float = 0.0
    bsteps: float = 1.0


class HartmannCamera:
    """Processes Hartmann files for a given camera.

    Parameters
    ----------
    observatory
        The observatory in which the data was taken.
    camera
        The name of the camera to process.
    m, b
        Collimator motion constants.
    bsteps
        Steps per degree for the blue ring.
    focustol
        Allowable focus tolerance in pixels.
    piston_factor
        Factor used to calculate the piston move. The piston move is calculated
        as the measured offset times the piston factor times the pixel size in
        microns.
    config
        The configuration dictionary. If `None`, uses the default product one.
    command
        A CLU command object to use to output information to the users.

    """

    def __init__(
        self,
        observatory: str,
        camera: str,
        m: float | None = None,
        b: float | None = None,
        bsteps: float | None = None,
        focustol: float | None = None,
        piston_factor: float | None = None,
        config: dict | None = None,
        command: HartmannCommandType | None = None,
    ):

        self.observatory = observatory.upper()
        self.camera = camera.lower()
        self.is_blue = self.camera[0] == "b"

        self.config = config or default_config

        coefficients = self.config["coefficients"]
        constants = self.config["constants"]

        self.m = m or coefficients["m"][self.camera]
        self.b = b or coefficients["b"][self.camera]

        self.bsteps: float = 1.0
        if bsteps is not None:
            self.bsteps = bsteps
        else:
            if coefficients["bsteps"][self.camera] is not None:
                self.bsteps = coefficients["bsteps"][self.camera]

        self.focustol = focustol or constants["focustol"]

        self.pixscale = constants["pixscale"]

        self.piston_factor = piston_factor or coefficients["piston_factor"][self.camera]
        self.piston_factor *= self.pixscale

        self.maxshift = constants["maxshift"]

        self.command = command

    def reset(self, **kwargs):
        """Resets the parameters."""

        self.__init__(self.observatory, self.camera, **kwargs)

    def set_command(self, command: HartmannCommandType):
        """Sets a command for output."""

        self.command = command

    def log(self, level: int, message: str):
        """Logs a message, optionally also writing to the command user."""

        log.log(level, message)

        if self.command:
            self.command.write(level, text=message)

    def __call__(
        self,
        image1: str | pathlib.Path,
        image2: str | pathlib.Path,
        no_check_image: bool = False,
        analysis_region: list | tuple | None = None,
    ) -> CameraResult:
        """Processes two images and returns the result of the Hartmann analysis.

        Parameters
        ----------
        image1
            The path to the first image, corresponding taken with one of the
            Hartmann doors in and the other out.
        image2
            Same as ``image1`` but with the Hartmann door positions changed.
        no_check_image
            Skip the header and variance calculation check for whether there
            is light in the camera (useful for sparse pluggings).
        analysis_region
            The region of the image on which to run the Hartmann analysis.
            If provided it must be a tuple with the format
            ``(y0, y1, x0, x1)`` describing the vertices of the analysis
            region. If not provided, the analysis region defined in
            the configuration file will be used.

        """

        # Placeholder result.
        camera_result = CameraResult(self.camera, bsteps=self.bsteps)

        try:

            proc1, side1 = self.prepare_image(
                str(image1),
                no_check_image=no_check_image,
            )
            proc2, side2 = self.prepare_image(
                str(image2),
                no_check_image=no_check_image,
            )

            if side1 == side2:
                raise HartmannError(f"Both images were taken with the {side1} door.")

            ishifts, coeffs, best, offset = self.calculate_shift(
                proc1,
                proc2,
                no_check_image=no_check_image,
                analysis_region=analysis_region,
            )

            # We assume the order is left-right, if it's actually right-left then
            # the offset is the opposite.
            if side1 == "right":
                offset = -offset

            piston, focused = self.find_collimator_motion(offset)

            # Update result.
            camera_result.ishifts = ishifts
            camera_result.coeffs = coeffs
            camera_result.best = best
            camera_result.offset = offset
            camera_result.piston = piston
            camera_result.focused = focused
            camera_result.success = True

        except HartmannError as err:
            raise HartmannError(f"Found error: {err}")

        except Exception as err:
            raise HartmannError(f"Unexpected exception: {err}")

        return camera_result

    def prepare_image(self, image: str, no_check_image: bool = False):
        """Applies bias and gain and extracts the analysis region.

        Parameters
        ----------
        image
            The path to the image to process.
        no_check_image
            Do not check the validity of the header.

        Returns
        -------
        data,side
            The extracted data, as a Numpy array, and the Hartmann side of the
            image as ``"left"`` or ``"right"``.

        Raises
        ------
        HartmannError
            If image does not exists, header data is missing or the image
            is not a Hartmann.

        """

        if not os.path.exists(image):
            raise HartmannError(f"The file {image} does not exist.")

        header: fits.Header = fits.getheader(image)

        if no_check_image is False and self._check_header(header):
            raise HartmannError(f"Failed verifying image {image}.")

        # OBSCOMM only exists in dithered flats taken with "specFlats"
        obscomm: str | None = header.get("OBSCOMM")
        hartmann: str | None = header.get("HARTMANN")

        if obscomm == "{focus, hartmann l}":
            side = "left"
        elif obscomm == "{focus, hartmann r}":
            side = "right"
        elif hartmann and hartmann.strip() == "Left":
            side = "left"
        elif hartmann and hartmann.strip() == "Right":
            side = "right"
        else:
            raise HartmannError(f"Cannot determine Hartmann side for image {image}.")

        # Get image data
        data = fits.getdata(image).astype(numpy.float32)

        # Raw data regions for quadrants 1 through 4. Apply gain and reconstruct.
        # Quadrants are 1 to 4
        #   [ 3  4 ]
        #   [ 1  2 ]

        proc_quads: list[numpy.ndarray] = []

        for qq in range(1, 5):
            q_slice = nslice(*self.config["regions"]["data"][qq])
            q_raw = data[q_slice]

            gain = self.config["gain"][self.camera][qq - 1]

            bias_slice = nslice(*self.config["regions"]["bias"][qq])
            q_bias = numpy.median(data[bias_slice])

            q_proc = gain * (q_raw - q_bias)
            proc_quads.append(q_proc)

        bottom = numpy.hstack((proc_quads[0], proc_quads[1]))
        top = numpy.hstack((proc_quads[2], proc_quads[3]))
        proc = numpy.vstack((bottom, top))

        return proc, side

    def _check_header(self, header: fits.Header):
        """Checks a header. Returns `True` if the image should not be used."""

        def sum_string(string_field):
            return sum([int(x) for x in string_field.split()])

        is_bad: bool = False
        ffs = header.get("FFS", None)

        # 8 flat field screens: 0 for open, 1 for closed
        if ffs:
            try:
                ffs_sum = sum_string(ffs)
                if ffs_sum < 8:
                    self.log(
                        logging.WARNING,
                        f"{self.camera}: only {ffs_sum} of 8 "
                        f"flat-field petals closed: {ffs}",
                    )
                if ffs_sum == 0:
                    is_bad = True
            except BaseException:
                self.log(logging.WARNING, f"{self.camera}: failed reading FFS info")
                is_bad = True
        else:
            self.log(logging.WARNING, f"{self.camera}: FFS not in FITS header!")
            is_bad = True

        # TODO: add the option of bypassing FFS, maybe.
        # if "ffs" in self.bypass and is_bad:
        #     self.log(logging.WARNING, 'text="FFS check failed but FFS are bypassed."')
        #     is_bad = False

        Ne = header.get("NE", None)
        HgCd = header.get("HGCD", None)
        HeAr = header.get("HEAR", None)

        # 4 of each lamp: 0 for off, 1 for on
        for lamp, name, observatory in [
            (Ne, "Ne", None),
            (HgCd, "HgCd", "APO"),
            (HeAr, "HeAr", "LCO"),
        ]:
            if observatory is not None and observatory != self.observatory:
                continue
            if lamp is not None:
                lamp_sum = sum_string(lamp)
                if lamp_sum < 4:
                    self.log(
                        logging.WARNING,
                        f"{self.camera}: {lamp_sum} of 4 {name} lamps are on: {lamp}",
                    )
                    is_bad = True
            else:
                self.log(logging.WARNING, f"{self.camera}: {name} not in FITS header.")
                is_bad = True

        return is_bad

    def calculate_shift(
        self,
        data1: numpy.typing.NDArray[numpy.float32],
        data2: numpy.typing.NDArray[numpy.float32],
        no_check_image: bool = False,
        analysis_region: list | tuple | None = None,
    ):
        """Checks the data and calculates the shift, in pixels.

        The shift is determined by applying a shift interpolation filter
        to one of the images and then calculating the sum of the product
        of the two images. We repeat this for an array of shifts and the
        optimum shift should be the one that maximises the product.

        The shift occurs inthe spectral direction which in the BOSS images
        is the y-axis (i.e., the first axis in the Numpy arrays).

        Parameters
        ----------
        data1
            An array with the analysis region from the first image in the
            Hartmann sequence.
        data2
            As ``data1``, for the second image in the Hartmann sequence.
        no_check_image
            Skip the variance calculation check for whether there is light
            in the camera (useful for sparse pluggings).
        analysis_region
            The region of the image on which to run the Hartmann analysis.
            If provided it must be a tuple with the format
            ``(y0, y1, x0, x1)`` describing the vertices of the analysis
            region. If not provided, the analysis region defined in
            the configuration file will be used.

        Returns
        -------
        ishifts,coeffs,best,offset
            The array of shifts tested in the y direction, the estimator used to
            determine the shift (larger number means a best match), the index
            of the best shift, and the calculated offset. All values are in
            pixels.

        Raises
        ------
        HartmannError
            If the arrays do not contain data.

        """

        ishifts: numpy.typing.NDArray[numpy.float32]

        # Select the region for analysis.
        if analysis_region is not None:
            analysis_slice = nslice(*analysis_region)
        else:
            analysis_slice = nslice(*self.config["regions"]["analysis"][self.camera])

        analysis1 = data1.copy()[analysis_slice]
        analysis2 = data2.copy()[analysis_slice]

        # First we check if there's actually light on the images.
        # The core of the idea here is to find the variance of a region with
        # several bright lines. Low variance means no light.
        # We clip all values > 1000 to 1000 before we compute the variance,
        # to reduce the impact of a handful of bright pixels.

        check1 = analysis1.copy()
        check2 = analysis2.copy()
        check1[check1 > 1000] = 1000
        check2[check2 > 1000] = 1000

        # ddof=1 for consistency with IDL's variance() which has denominator (N-1)
        var1 = numpy.var(check1, ddof=1)
        var2 = numpy.var(check2, ddof=1)

        if no_check_image is False and (var1 < 100 or var2 < 100):
            raise HartmannError("There does not appear to be any light from the arcs!")

        # Check the size of the images.
        if analysis1.shape != analysis2.shape:
            raise HartmannError("The data arrays shapes do not match.")

        # Now we proceed to calculate the shift. First create a mask for
        # the edges of the data to avoid problems with the splines.
        mask = numpy.zeros(analysis1.shape)
        mask[10:-10, 10:-10] = 1

        # Create an array of shifts that we will test with resolution 0.05 pixels.
        dx = 0.05
        nshift = int(numpy.ceil(2 * self.maxshift / dx))
        ishifts = -self.maxshift + dx * numpy.arange(nshift, dtype="f8")

        # Apply an spline filter to the input data on each axis. This smooths
        # the data and makes the comparison more reliable.
        filtered1 = scipy.ndimage.spline_filter(analysis1, order=3)
        filtered2 = scipy.ndimage.spline_filter(analysis2, order=3)

        # Apply the shift filter and calculate the product of the shifted images
        # for each shift value in ishift.
        with multiprocessing.Pool(4) as pool:
            func = partial(_shift_product, filtered1, filtered2, mask=mask)
            coeffs = pool.map(func, ishifts)

        best = numpy.argmax(coeffs)
        offset: float = ishifts[best]

        return ishifts, numpy.array(coeffs), int(best), offset

    def find_collimator_motion(self, offset: float):
        """Compute the required collimator movement."""

        if abs(offset) < self.focustol:
            focus = "In Focus"
            focused = True
            msglvl = "i"
        else:
            focus = "Out of focus"
            focused = False
            msglvl = "w"

        if self.command:
            self.command.write(
                msglvl,
                **{f"{self.camera}MeanOffset": [round(offset, 2), focus]},
            )

        m = self.m
        piston = -int(m * offset)

        if self.command:
            if "r" in self.camera:
                self.command.info(**{f"{self.camera}PistonMove": piston})
            else:
                self.command.info(
                    **{f"{self.camera}RingMove": round(-piston * self.bsteps, 1)}
                )

        return piston, focused


class Hartmann:
    """Calculate and apply Hartmann corrections.

    Parameters
    ----------
    observatory
        The observatory in which the data was taken.
    spec
        The spectrograph to collimate.
    cameras
        The cameras to collimate. If `None`, collimates all the cameras.
    config
        The configuration dictionary. If `None`, default to the product one.
    command
        The currently active command, for passing info/warn messages.

    """

    def __init__(
        self,
        observatory: str,
        spec: str,
        cameras: list[str] | None = None,
        config: dict | None = None,
        command: HartmannCommandType | None = None,
    ):

        self.observatory = observatory.upper()
        self.config = config or default_config

        self.spec = spec
        self.cameras = cameras = cameras or self.config["specs"][spec]["cameras"]

        if self.cameras is None or len(self.cameras) == 0:
            raise ValueError("No cameras defined.")

        self.command: Command | None = command

        self.result: HartmannResult | None = None

        self.log(logging.INFO, status="idle")

    def log(self, level: int, *args, **kwargs):
        """Logs a message, optionally also writing to the command user."""

        text: str | None = None

        if len(args) > 0 and isinstance(args[0], str):
            text = args[0]

        if text:
            log.log(level, text)

        if self.command:
            if text:
                self.command.write(level, text=text)
            if len(kwargs) > 0:
                self.command.write(level, message=kwargs)

    async def take_hartmanns(
        self,
        sub_frame: bool | list = False,
        exp_time: float | None = None,
        lamps: bool = True,
        keep_lamps: bool = False,
    ) -> list[str]:
        """Takes a pair of Hartmann exposures.

        Parameters
        ----------
        sub_frame
            Only readout a part of the chip.
        exp_time
            The exposure time for the Hartmanns.
        keep_lamps
            Do not turn off the lamps after the Hartmann.

        Returns
        -------
        exposures
            A list of the paths to the two exposures corresponding to Hartmann
            arcs with left and right doors closed, respectively, for each camera.

        """

        if self.command is None:
            raise HartmannError("A command is needed to take Hartmann exposures.")

        LAMPS = self.config["specs"][self.spec].get("lamps", [])

        # Turn lamps on
        if lamps is True:
            self.command.info("Turning lamps on.")
            for ll in LAMPS:
                result = await self.command.send_command("lcolamps", f"on {ll}")
                if result.status.did_fail:
                    raise HartmannError(
                        f"Failed turning on lamp {ll}. Some lamps may still be on."
                    )

        cams = ", ".join(self.cameras)
        self.command.info(f"Taking Hartmann exposures with cameras: {cams}")

        self.log(logging.INFO, status="exposing")

        # TODO: we may need to allow to select what cameras to expose.
        exp_time = exp_time or self.config["specs"][self.spec]["exp_time"]
        assert isinstance(exp_time, (float, int))

        command_str = "hartmann"
        if sub_frame:
            command_str += " --sub-frame"
        command_str += f" {exp_time}"

        hartmann_command = await self.command.send_command("yao", command_str)

        if hartmann_command.status.did_fail:
            raise HartmannError("Failed taking Hartmann exposures.")

        # Turn lamps off
        if lamps is True:
            if keep_lamps is False:
                self.command.info("Turning lamps off.")
                for ll in LAMPS:
                    result = await self.command.send_command("lcolamps", f"off {ll}")
                    if result.status.did_fail:
                        raise HartmannError(
                            f"Failed turning off lamp {ll}. Some lamps may still be on."
                        )

            else:
                self.command.warning("Keeping lamps on.")

        # Get all the filenames output by the command, unsorted for now.
        filenames: list[str] = []
        for reply in hartmann_command.replies:
            if "filename" in reply.message:
                filenames.append(reply.message["filename"][0])

        return filenames

    async def collimate(
        self,
        filenames: list[str] | list[pathlib.Path],
        no_check_image: bool = False,
        ignore_residuals: bool = False,
        min_blue_correction: bool = False,
        move_motors: bool = False,
    ) -> HartmannResult:
        """Runs the collimation calculation and determines the moves to apply.

        Parameters
        ----------
        filenames
            List of filenames with all exposures (left and right Hartmann) for
            all the cameras.
        no_check_image
            Skip the header and variance calculation check for whether there
            is light in the camera (useful for sparse pluggings).
        ignore_residuals
            Apply red moves regardless of resulting blue residuals.
        min_blue_correction
            Calculates only the minimum blue ring correction needed to
            get the focus within the tolerance level.
        move_motors
            On a successful focus determination, moves the collimator.

        """

        filenames = [str(file_) for file_ in filenames]
        filenames_camera = {c: [f for f in filenames if c in f] for c in self.cameras}

        for camera in self.cameras:
            if camera not in filenames_camera or len(filenames_camera[camera]) != 2:
                raise HartmannError(f"Failed retrieving some files for camera {camera}")

        self.log(logging.INFO, status="processing")

        loop = asyncio.get_running_loop()

        camera_exs = []
        for camera in self.cameras:
            obj = HartmannCamera(
                self.observatory,
                camera,
                config=self.config,
                command=self.command,
            )
            im1, im2 = filenames_camera[camera]
            camera_exs.append(
                loop.run_in_executor(
                    None,
                    obj.__call__,
                    im1,
                    im2,
                    no_check_image,
                )
            )

        camera_results: list[CameraResult] = await asyncio.gather(*camera_exs)

        for result in camera_results:
            if result.success is False:
                raise HartmannError("Failed processing Hartmann images.")

        hartmann_result = self._mean_moves(
            camera_results,
            ignore_residuals=ignore_residuals,
            min_blue_correction=min_blue_correction,
        )

        if move_motors:
            if abs(hartmann_result.bres) > self.config["constants"]["badres"]:
                if ignore_residuals is False:
                    self.log(
                        logging.ERROR,
                        "Not moving collimator until the blue ring has been adjusted.",
                    )
                    return hartmann_result
                else:
                    self.log(
                        logging.WARNING,
                        "Adjusting collimator because ignore_residuals=True.",
                    )

            hartmann_result.success = await self.move_motors(hartmann_result.move)

        return hartmann_result

    def _mean_moves(
        self,
        results: list[CameraResult],
        ignore_residuals: bool = False,
        min_blue_correction: bool = False,
    ):
        """Compute the mean movement after r and b moves have been determined."""

        spec_id = self.spec[-1]

        if len(results) == 0:
            raise HartmannError("The list of results is empty.")
        elif len(results) == 1:
            camera = results[0].camera
            self.log(logging.WARNING, f"Calculating collimator move for {camera} only.")
            self.result = HartmannResult(
                spec=self.spec,
                camera_results=results,
                move=results[0].piston,
                rres=0,
                bres=numpy.nan,
                bres_min=numpy.nan,
                residual_message="",
                success=True,
            )
            return self.result

        r_result, b_result = results
        if r_result.camera != f"r{spec_id}":
            r_result, b_result = b_result, r_result

        avg: float = float(numpy.nanmean([res.piston for res in results]))
        bres: float = -(b_result.piston - avg) * b_result.bsteps
        rres: float = int(r_result.piston - avg)

        if numpy.any(numpy.isnan([res.piston for res in results])):
            self.log(
                logging.WARNING,
                "bres cannot be calculated, skipping blue ring correction.",
            )
            bres = rres = 0

        # Calculates the minimum blue ring correction needed to get in the
        # focus tolerance.
        badres = self.config["constants"]["badres"]

        # Move to get exactly into tolerance.
        if abs(bres) >= badres:
            bres_min = 2 * (bres - numpy.sign(bres) * badres)
        else:
            bres_min = 0.0

        success: bool = True
        if abs(bres) < badres:
            resmsg = "OK"
            msglvl = logging.INFO
        elif ignore_residuals:
            if not min_blue_correction:
                resmsg = f"Move blue ring {bres * 2:.1f} degrees."
            else:
                resmsg = (
                    f"Move blue ring {bres_min:.1f} degrees. "
                    "This is the minimum move needed to "
                    "get in focus tolerance."
                )
            msglvl = logging.WARNING
        else:
            if not min_blue_correction:
                resmsg = (
                    f"Bad angle: move blue ring {bres*2:.1f} degrees then rerun "
                    "gotoField with Hartmanns checked."
                )
            else:
                resmsg = (
                    "Bad angle: move blue ring {bres_min:.1f} degrees then "
                    "rerun gotoField with Hartmanns checked. This is the "
                    "minimum move needed to get in focus tolerance."
                )

            msglvl = logging.WARNING
            success = False

        residuals = [int(rres), round(bres, 1), resmsg]
        self.log(msglvl, **{f"{self.spec}Residuals": residuals})

        self.log(logging.INFO, **{f"{self.spec}AverageMove": int(avg)})

        self.result = HartmannResult(
            spec=self.spec,
            camera_results=results,
            move=avg,
            rres=rres,
            bres=bres,
            bres_min=bres_min,
            residual_message=resmsg,
            success=success,
        )

        return self.result

    async def move_motors(self, move: float | int):
        """Moves the motors."""

        if self.command is None:
            raise HartmannError("Cannot move the collimator without an active command.")

        move = int(move)

        if move > self.config["max_collimator_move"]:
            self.command.error(
                "Move is larger than allowed move. "
                "If you are sure, move the collimator manually "
                "with yao mech move <MOVE>.",
            )
            return False

        self.command.info(text=f"Adjusting collimator by {move} steps.")

        move_command = await self.command.send_command("yao", f"mech move {move}")
        if move_command.status.did_fail:
            self.command.error(error="Failed adjusting collimator.")
            return False

        return True
