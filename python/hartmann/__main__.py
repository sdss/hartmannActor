#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-23
# @Filename: __main__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import os

import click
from click_default_group import DefaultGroup

from clu.tools import cli_coro as cli_coro_lvm
from sdsstools.daemonizer import DaemonGroup

from hartmann.actor.actor import HartmannActor


@click.group(cls=DefaultGroup, default="actor", default_if_no_args=True)
@click.option(
    "-c",
    "--config",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the user configuration file.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Debug mode. Use additional v for more details.",
)
@click.pass_context
def hartmann(ctx, config_file, verbose):
    """Hartmann actor."""

    ctx.obj = {"verbose": verbose, "config_file": config_file}


@hartmann.group(cls=DaemonGroup, prog="hartmann_actor", workdir=os.getcwd())
@click.pass_context
@cli_coro_lvm
async def actor(ctx):
    """Runs the actor."""

    default_config_file = os.path.join(os.path.dirname(__file__), "etc/hartmann.yml")
    config_file = ctx.obj["config_file"] or default_config_file

    hartmann_actor = HartmannActor.from_config(config_file)

    if ctx.obj["verbose"]:
        if hartmann_actor.log.fh:
            hartmann_actor.log.fh.setLevel(0)
        hartmann_actor.log.sh.setLevel(0)

    await hartmann_actor.start()
    await hartmann_actor.run_forever()


if __name__ == "__main__":
    hartmann()
