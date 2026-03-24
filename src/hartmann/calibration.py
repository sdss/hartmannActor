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
import polars
import seaborn
from astropy.io import fits
from numpy.exceptions import RankWarning
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

from hartmann import HartmannCamera, config, console, log
from hartmann.exceptions import HartmannUserWarning


__all__ = ["calibrate"]


SLICE_T = tuple[int, int, int, int]


# A list of good quadrant regions for each camera.
QUADRANT_REGIONS: dict[str, list[SLICE_T]] = {
    "r1": [
        (1020, 1300, 700, 2000),
        (1020, 1300, 2400, 3800),
        (2200, 2700, 700, 2000),
        (2200, 2700, 2400, 3800),
    ],
    "b1": [
        (1000, 2090, 700, 2000),
        (1000, 2090, 2400, 3800),
        (2800, 3450, 700, 2000),
        (2800, 3450, 2400, 3800),
    ],
    "r2": [
        (1020, 1300, 700, 2000),
        (1020, 1300, 2400, 3800),
        (2200, 2700, 700, 2000),
        (2200, 2700, 2400, 3800),
    ],
    "b2": [
        (1000, 2090, 700, 2000),
        (1000, 2090, 2400, 3800),
        (2800, 3450, 700, 2000),
        (2800, 3450, 2400, 3800),
    ],
}


def calibrate(
    cameras: str | list[str],
    observatory: str,
    files: list[str | pathlib.Path | int] | None = None,
    path: str | pathlib.Path | None = "/data/spectro",
    mjd: int | None = None,
    exposure_0: int | None = None,
    exposure_1: int | None = None,
    collimator_key: str = "COLLA",
    regions: list[SLICE_T] | dict[str, list[SLICE_T]] | None = None,
    ignore_invalid_paths: bool = False,
    output: str | pathlib.Path | None = None,
    plot: bool = True,
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
        Invalid frames are automatically ignored. If defined, ``path``, ``mjd``,
        ``exposure_0``, and ``exposure_1`` are ignored. It is expected that the
        first and second exposures are Hartmanns with the same collimator
        position and different doors, and that that continues for the remaining
        exposures.
    path
        The path to the directory containing the Hartmann frames.
    mjd
        The MJD of the exposures to process. If defined, it is appended to
        the ``path`` as ``{path}/{mjd}``.
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
        camera is used. If a dictionary is supplied, the keys must be camera names
        and the values must be lists of tuples as described above.
    ignore_invalid_paths
        If `True`, invalid paths are ignored with a warning. If `False`, an error
        is raised.
    output
        The path where to save the plots and data.
    plot
        If `True`, plots of the data and fits are generated and saved to the output
        directory. If `False`, no plots are generated.

    """

    if regions is not None and len(regions) > 8:
        raise ValueError("A maximum of 8 regions are allowed.")

    seaborn.set_palette("deep")
    seaborn.set_color_codes(palette="deep")

    MARKERS = [".", "v", "^", "s", "x", "D", "<", ">"]
    COLOURS = ["b", "r", "g", "k", "m", "c", "y", "b"]

    if isinstance(cameras, str):
        cameras = [cameras]

    if files is None:
        if exposure_0 is None or exposure_1 is None:
            raise ValueError(
                "`exposure_0` and `exposure_1` must be defined "
                "if `files` is not provided."
            )

        # For now create the list as a sequence of exposure numbers.
        files = list(range(exposure_0, exposure_1 + 1))

    # Loop over the list and check if the items are paths or exposure numbers.
    file_paths: list[pathlib.Path] = []
    for file in files:
        if isinstance(file, (str, pathlib.Path)):
            pp = pathlib.Path(file)
            if (not pp.exists() or not pp.is_file()) and not ignore_invalid_paths:
                raise FileExistsError(f"Path {pp!s} does not exist.")
            file_paths.append(pp)
            continue

        # If the file is a number, build the full path.

        if path is None:
            raise ValueError("`path` must be defined when using exposure numbers.")

        spectro_path = pathlib.Path(path)
        if mjd is not None:
            spectro_path /= str(mjd)

        if not spectro_path.exists() or not spectro_path.is_dir():
            if ignore_invalid_paths:
                continue
            raise FileExistsError(f"Path {spectro_path!s} does not exist.")

        expno = file
        expno_files: list[pathlib.Path] = []

        for camera in cameras:
            expno_files += list(spectro_path.glob(f"sdR-{camera}-{expno:08d}.fit*"))

        if len(expno_files) == 0:
            if ignore_invalid_paths:
                continue
            raise FileExistsError(f"No files found for {expno} in {spectro_path!s}.")

        file_paths.extend(expno_files)

    # Check that we actually have some files
    if len(file_paths) < 2:
        raise ValueError("Not enough valid files to process.")

    output = pathlib.Path(output or pathlib.Path(".").parent)

    processed: list[str] = []
    raw_data = []

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        transient=True,
        console=console,
    ) as progress:
        for camera in cameras:
            camera_files = sorted([pp for pp in file_paths if camera in pp.name])

            task = progress.add_task(camera, total=len(camera_files))

            for ifile in range(len(camera_files) - 1):
                file1 = pathlib.Path(camera_files[ifile])
                file2 = pathlib.Path(camera_files[ifile + 1])

                for file_ in [file1, file2]:
                    if not file_.exists():
                        raise FileExistsError(f"File {file_!s} does not exist.")

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
                    log.warning(
                        f"{file1.name} and {file2.name}: invalid Hartmann positions. "
                        "Positions must be 'left' and 'right'. Ignoring these files."
                    )
                    continue

                if hartmann_position_1 == hartmann_position_2:
                    log.warning(
                        f"{file1.name} and {file2.name}: same Hartmann positions "
                        "found. Positions must be 'left' and 'right'. "
                        "Ignoring these files."
                    )
                    continue

                mjd = header_1.get("MJD", -999)

                coll_1 = header_1[collimator_key]
                coll_2 = header_2[collimator_key]

                if coll_1 != coll_2:
                    log.warning(
                        f"{file1.name} and {file2.name}: "
                        "collimator positions do not match."
                    )
                    continue

                hc = HartmannCamera(observatory, camera, m=1, b=0)

                camera_regions: list[SLICE_T] | None = None
                if regions is not None:
                    if isinstance(regions, dict) and camera in regions:
                        camera_regions = regions[camera]
                    elif isinstance(regions, list):
                        camera_regions = regions

                for ii, region in enumerate(camera_regions or [None]):
                    try:
                        result = hc(file1, file2, analysis_region=region)
                    except Exception as err:
                        log.warning(
                            f"Exception processing files {file1.name} "
                            f"and {file2.name}, region {ii + 1}: {err}",
                            HartmannUserWarning,
                        )
                        continue

                    # We calculate the piston move, but this only makes sense using
                    # and existing calibration.
                    m_current: float = config["coefficients"]["m"][camera]
                    b_current: float = config["coefficients"]["b"][camera]
                    piston = -(m_current * result.offset + b_current)

                    raw_data.append(
                        (
                            int(expno_1),
                            int(expno_2),
                            int(ii + 1),
                            camera,
                            float(coll_1),
                            result.success,
                            float(result.offset) if result.success else None,
                            int(piston) if result.success is not None else None,
                        )
                    )

                processed.append(file1.name)
                processed.append(file2.name)

                progress.update(task, advance=2)

    data = polars.DataFrame(
        data=raw_data,
        schema={
            "expno_1": polars.Int32,
            "expno_2": polars.Int32,
            "region": polars.Int16,
            "camera": polars.String,
            "collimator": polars.Float32,
            "success": polars.Boolean,
            "offset": polars.Float32,
            "collimator_move": polars.Int32,
        },
        orient="row",
    )

    # Plot data and output the updated coefficients. Since we are using the
    # piston factor (although I think we could get away with it) to convert from
    # pixel offset to collimator offset around zero, we first convert the collimator
    # units to pixels.
    if plot:
        for camera in cameras:
            data_cam = data.filter(polars.col.camera == camera)

            region_nos = (
                data_cam.select(polars.col.region).unique().to_series(0).to_list()
            )

            with plt.ioff():
                seaborn.set_theme(
                    style="darkgrid",
                    palette="deep",
                    font_scale=1.1,
                    color_codes=True,
                )

                fig, ax = plt.subplots()

                m = b = None

                for nr, ir in enumerate(region_nos):
                    # Calculate the fit coefficients using a polynomial fit.
                    dr = data_cam.filter(polars.col.region == ir)

                    if dr.height < 2:
                        log.warning(
                            f"Not enough data points to fit region {ir} for camera "
                            f"{camera}.",
                        )
                        m = b = None
                    else:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", category=RankWarning)
                            m, b = numpy.polyfit(dr["offset"], dr["collimator"], 1)

                    colour = COLOURS[nr]
                    marker = MARKERS[nr]

                    ax.scatter(
                        dr["offset"],
                        dr["collimator"],
                        marker=marker,
                        c=colour,
                        label=f"Region {ir}" if m is None else None,
                    )

                    if m is not None and b is not None:
                        xplot = numpy.linspace(
                            float(dr["offset"].min()),  # type: ignore
                            float(dr["offset"].max()),  # type: ignore
                            2,
                        )

                        yplot = m * xplot + b

                        ax.plot(
                            xplot,
                            yplot,
                            f"{colour}-",
                            label=rf"${nr + 1}: y={m:.3f}x+{b:.3f}$",
                        )

                        log.info(f"{camera} ({nr + 1}): m={m:.3f} b={b:.3f} [pixels]")

                ax.legend()

                ax.set_xlabel("Offset [pixels]")
                ax.set_ylabel(r"Collimator [$\mu\, {\rm m}$]")

                if len(region_nos) == 1 and m and b:
                    ax.set_title(f"{camera}: m={m:.3f} b={b:.3f}")
                else:
                    ax.set_title(camera)

                if mjd is not None:
                    fig_file = str(output / rf"hartmann_calibration_{mjd}_{camera}.pdf")
                else:
                    fig_file = str(output / rf"hartmann_calibration_{camera}.pdf")

                fig.savefig(fig_file)
                plt.close("all")

    if mjd is not None:
        parquet_file = output / f"hartmann_calibration_{mjd}.parquet"
    else:
        parquet_file = output / "hartmann_calibration.parquet"

    data.write_parquet(parquet_file)

    return data
