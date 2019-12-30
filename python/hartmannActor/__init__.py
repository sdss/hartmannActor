#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-29
# @Filename: __init__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import pathlib

import pkg_resources


def get_version():

    try:
        return pkg_resources.get_distribution('sdss-hartmannActor').version
    except pkg_resources.DistributionNotFound:
        try:
            import toml
            poetry_config = toml.load(
                open(pathlib.Path(__file__).parent / '../../pyproject.toml'))
            return poetry_config['tool']['poetry']['version']
        except Exception:
            return '0.0.0'


__version__ = get_version()

NAME = 'sdss-hartmannActor'
