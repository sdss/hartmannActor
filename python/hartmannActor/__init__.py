#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-29
# @Filename: __init__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import pkg_resources


def get_version(NAME):

    try:
        return pkg_resources.get_distribution(NAME).version
    except pkg_resources.DistributionNotFound:
        try:
            from sdsstools import get_package_version
            return get_package_version(__file__, NAME) or '0.0.0'
        except (ImportError, ModuleNotFoundError):
            return '0.0.0'


NAME = 'sdss-hartmannActor'

__version__ = get_version(NAME)
