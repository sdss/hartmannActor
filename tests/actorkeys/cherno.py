#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2021-06-11
# @Filename: cherno.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

# type: ignore


KeysDictionary(
    'cherno', (0, 1),
    Key('version', String(help='actor version')),
    Key('text', String(), help='text for humans'),
    Key('error', String(), help='text for humans'),
    Key("axis_error",
        Float(name="RA",
              help="<easured pointing correction in RA (distance across the sky)",
              units="arcsec"),
        Float(name="DEC",
              help="Measured pointing correction in Dec (distance across on the sky)",
              units="arcsec"),
        Float(name="Rot",
              help="Measured pointing correction in rotation",
              units="arcsec"),
        doCache=False,
        help="Measured pointing corrections")
)
