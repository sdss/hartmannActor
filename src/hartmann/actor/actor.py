#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-23
# @Filename: actor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import logging
import os

import clu

from hartmann import __version__, log
from hartmann.exceptions import HartmannError, HartmannUserWarning


__all__ = ["HartmannActor", "HartmannCommandType"]


class HartmannActor(clu.LegacyActor):
    """The hartmann SDSS-style actor."""

    def __init__(self, *args, observatory: str | None = None, **kwargs):
        if "schema" not in kwargs:
            base = os.path.join(os.path.dirname(__file__), "..")
            base_schema = os.path.realpath(os.path.join(base, "etc/schema.json"))
            kwargs["schema"] = base_schema

        # Set the observatory where the actor is running.
        if observatory is None:
            try:
                self.observatory = os.environ["OBSERVATORY"]
            except KeyError:
                raise HartmannError(
                    "Observatory not passed and $OBSERVATORY is not set."
                )
        else:
            self.observatory = observatory

        super().__init__(*args, **kwargs)

        self.version = __version__

        # Add ActorHandler to log and to the warnings logger.
        self.actor_handler = clu.ActorHandler(
            self,
            level=logging.WARNING,
            filter_warnings=[HartmannUserWarning],
        )
        log.addHandler(self.actor_handler)
        if log.warnings_logger:
            log.warnings_logger.addHandler(self.actor_handler)


HartmannCommandType = clu.Command[HartmannActor]
