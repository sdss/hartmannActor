# encoding: utf-8

from __future__ import annotations

import os
import warnings

from typing import Any

from sdsstools import get_config, get_logger, get_package_version


def set_observatory(observatory: str | None):
    """Returns and sets the config for the desired observatory."""

    if "config" in globals() and config is not None:
        globals()["config"].clear()
    else:
        globals()["config"] = {}

    if observatory is None:
        observatory = "APO"
        warnings.warn("Unknown observatory. Defaulting to APO!", UserWarning)
    else:
        observatory = observatory.upper()

    os.environ["OBSERVATORY"] = observatory
    globals()["OBSERVATORY"] = observatory

    new_config = get_config("hartmann")
    globals()["config"].update(new_config)

    return new_config


# pip package name
NAME = "sdss-hartmannActor"

# Loads config. config name is the package name.
OBSERVATORY = "APO"  # Gets overridden by set_observatory()
config: dict[str, Any] = set_observatory(os.environ.get("OBSERVATORY", None))

log = get_logger(NAME)

# package name should be pip package name
__version__ = get_package_version(path=__file__, package_name=NAME)

from .hartmann import *
