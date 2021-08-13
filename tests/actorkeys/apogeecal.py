#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-28
# @Filename: apogeecal.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

# This is the initial test keys dictionary for APOGEE Calibration Box

# type: ignore


KeysDictionary(
    'apogeecal', (1, 0),

    # Misc
    Key('text',
        String(),
        help='text for humans'),
    Key('version',
        String(),
        help='version string derived from svn info.'),

    # Lamps
    Key('calSourceNames',
        String() * (3, 6),
        help='List of calibration lamp names'),
    Key('calSourceStatus',
        Bool('false', 'true', invalid='?') * (3, 6),
        help='Calibration lamp on (true) or off (false)'),
    Key('calShutter',
        Bool('closed', 'open', invalid='?'),
        help='State of the CalBox shutter'),
    Key('calBoxController',
        Bool('off', 'on', invalid='?'),
        help='State of the CalBox controller')

)
