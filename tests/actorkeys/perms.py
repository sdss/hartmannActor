#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-28
# @Filename: perms.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
# Based on what the TCC knows about the perms widget

# type: ignore


KeysDictionary(
    'perms', (1, 2),
    Key('actors', String() * (0,),
        help='Actors controlled by perms'),
    Key('authList', String() * (1,),
        help='Program and 0 or more authorized actors'),
    Key('lockedActors', String() * (0,),
        help='Actors locked out by APO'),
    Key('programs', String() * (0,),
        help='Programs registered with perms'),
)
