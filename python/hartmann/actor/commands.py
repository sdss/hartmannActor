#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-23
# @Filename: commands.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from clu.parsers.click import command_parser as hartmann_parser

from hartmann import OBSERVATORY, Hartmann, config

from ..exceptions import HartmannError


if TYPE_CHECKING:
    from hartmann import HartmannResult

    from .actor import HartmannCommandType


@hartmann_parser.command()
@click.option("--spec", "-s", type=str, help="The spectrograph to collimate.")
@click.option(
    "--exposure-time",
    "-t",
    type=float,
    help="Exposure time in seconds. Currently ignored at APO.",
)
@click.option(
    "--sub-frame/--no-sub-frame",
    default=OBSERVATORY == "APO",
    is_flag=True,
    help="Takes a sub-frame Hartmann pair.",
)
@click.option("--move/--no-move", default=True, help="Move the collimator.")
@click.option(
    "--min-blue-correction",
    "-m",
    is_flag=True,
    help="Reports the minimum blue ring move required to be in tolerance.",
)
@click.option(
    "--ignore-residuals",
    "-r",
    is_flag=True,
    help="Ignore blue residuals and apply collimator correction.",
)
@click.option(
    "--ignore-errors",
    is_flag=True,
    help="Always marks the command as successfully done even when the blue ring is "
    "not in tolerance. Useful for scripting and focus sweeps.",
)
@click.option(
    "--no-lamps",
    "-l",
    is_flag=True,
    help="Do not turn on/off lamps.",
)
@click.option(
    "--keep-lamps",
    "-k",
    is_flag=True,
    help="Do not turn off the lamps after the Hartmann.",
)
async def collimate(
    command: HartmannCommandType,
    spec: str | None = None,
    exposure_time: float | None = None,
    move: bool = True,
    sub_frame: bool = False,
    min_blue_correction: bool = False,
    ignore_residuals: bool = False,
    ignore_errors: bool = False,
    no_lamps: bool = False,
    keep_lamps: bool = False,
):
    """Exposes BOSS and adjusts the collimator."""

    if spec is None:
        for spec_ in config["specs"]:
            if config["specs"][spec_]["observatory"] == command.actor.observatory:
                spec = spec_
                break

    assert isinstance(spec, str)

    hartmann = Hartmann(command.actor.observatory, spec, command=command)

    result: HartmannResult | None = None
    try:
        filenames = await hartmann.take_hartmanns(
            sub_frame=sub_frame,
            lamps=not no_lamps,
            keep_lamps=keep_lamps,
            exposure_time=exposure_time,
        )
        result = await hartmann.collimate(
            filenames,
            ignore_residuals=ignore_residuals,
            min_blue_correction=min_blue_correction,
            move_motors=move,
        )
    except HartmannError as err:
        return command.fail(str(err))
    finally:
        command.info(status="idle")

    if ignore_errors is False and (result is None or result.success is False):
        return command.fail("Hartmann collimation failed.")

    return command.finish()


@hartmann_parser.command()
@click.argument("MJD", type=int)
@click.argument("FRAME0", type=int)
@click.argument("FRAME1", type=int, required=False)
@click.option("--spec", "-s", type=str, help="The spectrograph to collimate.")
@click.option(
    "--min-blue-correction",
    "-m",
    is_flag=True,
    help="Reports the minimum blue ring move required to be in tolerance.",
)
@click.option(
    "--ignore-residuals",
    "-r",
    is_flag=True,
    help="Ignore blue residuals and apply collimator correction.",
)
async def reprocess(
    command: HartmannCommandType,
    mjd: int,
    frame0: int,
    frame1: int | None = None,
    spec: str | None = None,
    min_blue_correction: bool = False,
    ignore_residuals: bool = False,
):
    """Reprocesses exposures."""

    if spec is None:
        for spec_ in config["specs"]:
            if config["specs"][spec_]["observatory"] == command.actor.observatory:
                spec = spec_
                break

    assert isinstance(spec, str)

    if frame1 is None:
        frame1 = frame0 + 1

    path = f"/data/spectro/{mjd}/"
    file = "sdR-{camera}-{frame:08}.fit.gz"

    filenames = []
    for camera in config["specs"][spec]["cameras"]:
        filenames.append(path + file.format(camera=camera, frame=frame0))
        filenames.append(path + file.format(camera=camera, frame=frame1))

    hartmann = Hartmann(command.actor.observatory, spec, command=command)

    try:
        await hartmann.collimate(
            filenames,
            ignore_residuals=ignore_residuals,
            min_blue_correction=min_blue_correction,
            move_motors=False,
        )
    except HartmannError as err:
        return command.fail(str(err))

    return command.finish()


@hartmann_parser.command()
async def status(command: HartmannCommandType):
    """Reports the status of the actor."""

    if command.actor.model is None or "status" not in command.actor.model:
        status = "unknown"
    else:
        status = command.actor.model["status"].value
        if status is None or (isinstance(status, list) and status[0] is None):
            status = "unknown"

    command.info(status=status)

    return command.finish()
