#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-08-08
# @Filename: calibration.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import pathlib
import warnings

import matplotlib.pyplot as plt
import numpy
import pandas
import seaborn
from astropy.io import fits

from hartmann import HartmannCamera, config
from hartmann.exceptions import HartmannUserWarning


__all__ = ["calibrate"]


def calibrate(
    cameras: str | list[str],
    observatory: str,
    files: list[str | pathlib.Path] | None = None,
    mjd: int | None = None,
    exposure_0: int | None = None,
    exposure_1: int | None = None,
    collimator_key: str = "COLLA",
    output: str | pathlib.Path | None = None,
):
    """Runs the calibration process and outputs new coefficients.

    Parameters
    ----------
    cameras
        Cameras to process.
    observatory
        Observatory at which the data was taken.
    files
        A list of Hartmann frames taking with different collimator positions.
        Invalid frames are automatically ignored. If defined, ``mjd``, ``exposure_0``,
        and ``exposure_1`` are ignored.
    mjd
        The MJD of the frames. To be used with ``exposure_0`` and ``exposure_1``.
        Assumes the frames can be found in ``/data/spectro/<MJD>``.
    exposure_0
        The first frame to consider.
    exposure_1
        The last frame to consider.
    collimator_key
        The header keyword for the collimator position.
    output
        The path where to save the plots.

    """

    if not files:
        assert mjd is not None and exposure_0 is not None and exposure_1 is not None

        files = []
        spectro_path = pathlib.Path(f"/data/spectro/{observatory.lower()}/{mjd}")
        for expno in range(exposure_0, exposure_1 + 1):
            files += list(spectro_path.glob(f"sdR-*-{expno:08d}.fit*"))

    if isinstance(cameras, str):
        cameras = [cameras]

    processed: list[str] = []
    raw_data = []

    for camera in cameras:

        camera_files = sorted([file_ for file_ in files if camera in str(file_)])

        for ifile in range(len(camera_files) - 1):

            file1 = pathlib.Path(camera_files[ifile])
            file2 = pathlib.Path(camera_files[ifile + 1])

            file_not_found: bool = False
            for file_ in [file1, file2]:
                if not file_.exists():
                    warnings.warn(f"File {str(file_)} not found.", HartmannUserWarning)
                    file_not_found = True
                    break

            if file_not_found:
                continue

            if str(file1) in processed:
                continue

            header_1 = fits.getheader(str(file1))
            header_2 = fits.getheader(str(file2))

            expno_1 = header_1.get("EXPOSURE", -999)
            expno_2 = header_2.get("EXPOSURE", -999)

            hartmann_position_1 = header_1.get("HARTMANN", "?").lower()
            hartmann_position_2 = header_2.get("HARTMANN", "?").lower()

            h1_valid = hartmann_position_1 in ["left", "right"]
            h2_valid = hartmann_position_2 in ["left", "right"]

            if not h1_valid or not h2_valid:
                continue

            if hartmann_position_1 == hartmann_position_2:
                continue

            mjd = header_1.get("MJD", -999)

            coll_1 = header_1[collimator_key]
            coll_2 = header_2[collimator_key]

            if coll_1 != coll_2:
                warnings.warn(f"{str(file1)}: collimator positions do not match.")
                continue

            hc = HartmannCamera(observatory, camera)

            try:
                result = hc(file1, file2)
            except Exception as err:
                warnings.warn(
                    f"Exception processing files {file1!s} and {file2!s}: {err}",
                    HartmannUserWarning,
                )
                continue

            raw_data.append((expno_1, expno_2, camera, coll_1, result.offset))
            print((expno_1, expno_2, camera, coll_1, result.offset))

            processed.append(str(file1))
            processed.append(str(file2))

    data = pandas.DataFrame(
        data=raw_data,
        columns=["expno_1", "expno_2", "camera", "collimator", "offset"],
    )

    # Plot data and output the updated coefficients. Since we are using the
    # piston factor (although I think we could get away with it) to convert from
    # pixel offset to collimator offset around zero, we first convert the collimator
    # units to pixels.
    for camera in cameras:

        data_cam = data.loc[data.camera == camera]

        piston_factor = config["coefficients"]["piston_factor"][camera]
        piston_factor *= config["constants"]["pixscale"]

        # Calculate the fit coefficients using a polynomial fit.
        valid = (data_cam.offset >= -2) & (data_cam.offset <= 2)
        m, b = numpy.polyfit(
            data_cam.offset.loc[valid],
            data_cam.collimator.loc[valid],
            1,
        )

        # Coeffs go in the other direction.
        m_pix = -m / piston_factor
        b_pix = -b / piston_factor

        with plt.ioff():
            with seaborn.axes_style("darkgrid"):

                seaborn.set_palette("deep")

                fig, ax = plt.subplots()

                ax.scatter(data_cam.offset, data_cam.collimator)

                xplot = numpy.linspace(data_cam.offset.min(), data_cam.offset.max(), 2)
                yplot = m * xplot + b
                ax.plot(xplot, yplot, "r-", label=rf"$y={m:.3f}x+{b:.3f}$")

                ax.legend()
                ax.set_xlabel("Offset [pixels]")
                ax.set_ylabel(r"Collimator [$\mu\, {\rm m}$]")

                ax.set_title(f"{camera}: m={m_pix:.3f} b={b_pix:.3f}")

                print(f"{camera}: m={m_pix:.3f} b={b_pix:.3f} [pixels]")

                output = pathlib.Path(output or pathlib.Path(".").parent)
                fig.savefig(str(output / rf"hartmann_{camera}.pdf"))

                plt.close("all")

    return data
