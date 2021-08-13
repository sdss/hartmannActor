#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-05-22
# @Filename: jaeger.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
#
# @Last modified by: José Sánchez-Gallego
# @Last modified time: 2019-11-22 15:14:15

# type: ignore


KeysDictionary(
    'jaeger', (0, 1),
    Key('version', String(help='actor version')),
    Key('text', String(), help='text for humans'),
    Key('locked', Bool(), help='is the FPS locked?'),
    Key('engineering_mode', Bool(), help='is the FPS in engineering mode?'),
    Key('move_time', Float(), help='time the FPS will be moving'),
    Key('status',
        Int(name='positioner_id', help='the ID of the positioner'),
        Float(name='alpha', help='the angle of the alpha arm', units='degrees'),
        Float(name='beta', help='the angle of the beta arm', units='degrees'),
        Int(name='status_bits', help='the status maskbit'),
        Bool(name='initialised', help='is the positioner initialised?'),
        Bool(name='bootloader', help='is the position in bootloader mode?'),
        String(name='firmware', help='the version of the firmware loaded'),
        Int(name='interface', help='the interface index'),
        Int(name='bus', help='the interface index')),
    Key('current',
        Int(name='alpha', help='alpha current'),
        Int(name='beta', help='alpha current'))
)
