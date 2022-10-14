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
from matplotlib.markers import MarkerStyle
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

from hartmann import HartmannCamera
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
    regions: list | None = None,
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
        and ``exposure_1`` are ignored. It is expected that the first and second
        exposures are hartmanns with the same collimator position and different
        doors, and that that continues for the remaining exposures.
    mjd
        The MJD of the frames. To be used with ``exposure_0`` and ``exposure_1``.
        Assumes the frames can be found in ``/data/spectro/<mjd>`` or
        ``/data/spectro/<observatory>/<mjd>``.
    exposure_0
        The first frame to consider.
    exposure_1
        The last frame to consider.
    collimator_key
        The header keyword for the collimator position.
    regions
        A list of regions on the image to analyse. If provided, it must be a
        list of tuples in which each tuple contains the (y0, y1, x0, x1) vertices
        of the regions to select. If not supplied, the default region for each
        camera is used.
    output
        The path where to save the plots.

    """

    if regions is not None and len(regions) > 8:
        raise ValueError("A maximim of 8 regions are allowed.")

    seaborn.set_palette("deep")
    seaborn.set_color_codes(palette="deep")

    MARKERS: list[MarkerStyle] = [".", "v", "^", "s", "x", "D", "<", ">"]  # type:ignore
    COLOURS: list[str] = ["b", "r", "g", "k", "m", "c", "y", "b"]

    if not files:
        assert mjd is not None and exposure_0 is not None and exposure_1 is not None

        files = []
        spectro_path = pathlib.Path(f"/data/spectro/{mjd}")
        if not spectro_path.exists():
            spectro_path = pathlib.Path(f"/data/spectro/{observatory.lower()}/{mjd}")
            if not spectro_path.exists():
                raise FileExistsError("Path to images does not exist.")

        for expno in range(exposure_0, exposure_1 + 1):
            files += list(spectro_path.glob(f"sdR-*-{expno:08d}.fit*"))

    output = pathlib.Path(output or pathlib.Path(".").parent)

    if isinstance(cameras, str):
        cameras = [cameras]

    processed: list[str] = []
    raw_data = []

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        transient=True,
    ) as progress:
        for camera in cameras:

            camera_files = sorted([file_ for file_ in files if camera in str(file_)])

            task = progress.add_task(camera, total=len(camera_files))

            for ifile in range(len(camera_files) - 1):

                file1 = pathlib.Path(camera_files[ifile])
                file2 = pathlib.Path(camera_files[ifile + 1])

                file_not_found: bool = False
                for file_ in [file1, file2]:
                    if not file_.exists():
                        warnings.warn(
                            f"File {str(file_)} not found.", HartmannUserWarning
                        )
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

                hc = HartmannCamera(observatory, camera, m=1, b=0)

                regions = regions or [None]

                for ii, region in enumerate(regions):

                    try:
                        result = hc(file1, file2, analysis_region=region)
                    except Exception as err:
                        warnings.warn(
                            f"Exception processing files {file1!s} "
                            f"and {file2!s}, region {ii+1}: {err}",
                            HartmannUserWarning,
                        )
                        continue

                    raw_data.append(
                        (
                            expno_1,
                            expno_2,
                            ii + 1,
                            camera,
                            coll_1,
                            result.offset,
                        )
                    )

                processed.append(str(file1))
                processed.append(str(file2))

                progress.update(task, advance=2)

    # for camera in cameras:
    #     progress.remove_task(progress_tasks[camera])

    data = pandas.DataFrame(
        data=raw_data,
        columns=["expno_1", "expno_2", "region", "camera", "collimator", "offset"],
    )

    # Plot data and output the updated coefficients. Since we are using the
    # piston factor (although I think we could get away with it) to convert from
    # pixel offset to collimator offset around zero, we first convert the collimator
    # units to pixels.
    for camera in cameras:

        data_cam = data.loc[data.camera == camera]

        n_regions = len(data_cam.region.unique())

        with plt.ioff():
            with seaborn.axes_style("darkgrid"):

                fig, ax = plt.subplots()

                m = b = None

                for nr, ir in enumerate(data_cam.region.unique()):

                    # Calculate the fit coefficients using a polynomial fit.
                    dr = data_cam.loc[data_cam.region == ir]
                    m, b = numpy.polyfit(dr.offset, dr.collimator, 1)

                    colour = COLOURS[nr]
                    marker = MARKERS[nr]

                    ax.scatter(
                        dr.offset,
                        dr.collimator,
                        marker=marker,
                        c=colour,
                        fc=colour,
                        ec=colour,
                    )

                    xplot = numpy.linspace(dr.offset.min(), dr.offset.max(), 2)
                    yplot = m * xplot + b

                    ax.plot(
                        xplot,
                        yplot,
                        f"{colour}-",
                        label=rf"${nr+1}: y={m:.3f}x+{b:.3f}$",
                    )

                    print(f"{camera} ({nr+1}): m={m:.3f} b={b:.3f} [pixels]")

                ax.legend()
                ax.set_xlabel("Offset [pixels]")
                ax.set_ylabel(r"Collimator [$\mu\, {\rm m}$]")

                if n_regions == 1 and m and b:
                    ax.set_title(f"{camera}: m={m:.3f} b={b:.3f}")
                else:
                    ax.set_title(camera)

                if mjd is not None:
                    fig.savefig(str(output / rf"hartmann_{mjd}_{camera}.pdf"))
                else:
                    fig.savefig(str(output / rf"hartmann_{camera}.pdf"))

                plt.close("all")

    if mjd is not None:
        data.to_csv(str(output / f"hartmann_{mjd}.csv"))
    else:
        data.to_csv(str(output / "hartmann.csv"))

    return data
