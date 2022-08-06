#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-23
# @Filename: commands.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

from typing import TYPE_CHECKING

from clu.parsers.click import command_parser as hartmann_parser


if TYPE_CHECKING:
    from .actor import HartmannCommandType


@hartmann_parser.command()
async def collimate(command: HartmannCommandType):
    """Exposes BOSS and adjusts the collimator."""

    return command.finish()
