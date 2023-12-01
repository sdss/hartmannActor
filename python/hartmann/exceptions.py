#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-23
# @Filename: exceptions.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations


class HartmannError(Exception):
    """A custom core hartmann exception"""

    def __init__(self, message=None):
        message = "There has been an error" if not message else message

        super(HartmannError, self).__init__(message)


class HartmannWarning(Warning):
    """Base warning for hartmann."""


class HartmannUserWarning(UserWarning, HartmannWarning):
    """The primary warning class."""

    pass


class HartmannSkippedTestWarning(HartmannUserWarning):
    """A warning for when a test is skipped."""

    pass


class HartmannDeprecationWarning(HartmannUserWarning):
    """A warning for deprecated features."""

    pass
