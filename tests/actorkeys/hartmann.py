#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-28
# @Filename: hartmann.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

# type: ignore


KeysDictionary(
    'hartmann', (1, 0),
    Key('text', String(help='text for humans')),
    Key('version', String(help='product version')),
    Key('status', String(help='status of collimation process: Idle/exposing/processing/')),
    Key('specs', String(help='what spectrographs are being processed.') * (0, 2)),
    Key('cameras', String(help='what cameras are being processed.') * (0, 4)),

    Key('b1RingMove', Float(units='deg', help='measured error in b1 ring rotation')),
    Key('b2RingMove', Float(units='deg', help='measured error in b2 ring rotation')),

    Key('r1MeanOffset',
        Float(name='pixels', units='pixels',
              help='measured distance between hartmann spots'),
        String('explanatory comment', name='comment')),
    Key('r2MeanOffset',
        Float(name='pixels', units='pixels',
              help='measured distance between hartmann spots'),
        String('explanatory comment', name='comment')),
    Key('b1MeanOffset',
        Float(name='pixels', units='pixels',
              help='measured distance between hartmann spots'),
        String('explanatory comment', name='comment')),
    Key('b2MeanOffset',
        Float(name='pixels', units='pixels',
              help='measured distance between hartmann spots'),
        String('explanatory comment', name='comment')),

    Key('r1PistonMove',
        Int(name='steps', units='steps',
            help='piston move required to correct r1 error')),
    Key('r2PistonMove',
        Int(name='steps', units='steps',
            help='piston move required to correct r2 error')),

    Key('sp1AverageMove',
        Int(name='steps', units='steps',
            help='collimator move required to best correct r1&b1 errors')),
    Key('sp2AverageMove',
        Int(name='steps', units='steps',
            help='collimator move required to best correct r2&b2 errors')),

    Key('sp1Residuals',
        Int(name='steps', units='steps', help='r1 residual error after sp1AverageMove'),
        Float(name='deg', units='deg', help='b1 residual error after sp1AverageMove'),
        String(name='comment', help='OK, or some useful error message')),
    Key('sp2Residuals',
        Int(name='steps', units='steps', help='r2 residual error after sp2AverageMove'),
        Float(name='deg', units='deg', help='b2 residual error after sp2AverageMove'),
        String(name='comment', help='OK, or some useful error message')),

)
