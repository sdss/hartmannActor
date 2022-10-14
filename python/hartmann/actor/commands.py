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

from hartmann import Hartmann, config

from ..exceptions import HartmannError


if TYPE_CHECKING:
    from hartmann import HartmannResult

    from .actor import HartmannCommandType


@hartmann_parser.command()
@click.option("--spec", "-s", type=str, help="The spectrograph to collimate.")
@click.option(
    "--sub-frame",
    "-s",
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
    move: bool = True,
    sub_frame: bool = False,
    min_blue_correction: bool = False,
    ignore_residuals: bool = False,
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
        )
        result = await hartmann.collimate(
            filenames,
            ignore_residuals=ignore_residuals,
            min_blue_correction=min_blue_correction,
            move_motors=move,
        )
    except HartmannError as err:
        return command.fail(str(err))

    if result is None or result.success is False:
        return command.fail("Hartmann collimation failed.")

    return command.finish()
