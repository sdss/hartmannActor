#!/usr/bin/env python
"""
Compute the collimator moves for an already-taken Hartmann pair.

Defaults to using etc/hartmann.cfg for the slope and intercept, unless -m or -b are specified.
"""

import sys, os
import argparse
import ConfigParser

from actorcore import TestHelper

from hartmannActor import hartmannActor_main
from hartmannActor import boss_collimate

def get_expnum(filename):
    """Return the exposure number from this filename."""
    return int(filename.split('-')[-1].split('.')[0])

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, prog=os.path.basename(sys.argv[0]))
    parser.add_argument('FILE1', metavar='FILE1', type=str,
                        help='The first hartmann file (generally left).')
    parser.add_argument('FILE2', metavar='FILE2', default=None, nargs='?',
                        help='Optional second hartmann file (generally right).')
    parser.add_argument('-m',default=None, dest='m',
                        help='Slope of the offset->motor function: b1,r1,b2,r2.')
    parser.add_argument('-b',default=None, dest='b',
                        help='Intercept of the offset->motor function: b1,r1,b2,r2.')
    parser.add_argument('--bsteps',default=None, dest='bsteps',
                        help='steps per degree for the blue ring')
    parser.add_argument('--badres',default=None, dest='badres',
                        help='tolerance for bad residual on blue ring')
    args = parser.parse_args()

    exp1 = args.FILE1
    indir,expnum1 = os.path.split(exp1)
    expnum1 = get_expnum(expnum1)
    if args.FILE2:
        indir,expnum2 = os.path.split(args.FILE2)
        expnum2 = get_expnum(expnum2)

    if '/data/spectro' in indir:
        mjd = os.path.split(indir)[-1]
    else:
        mjd = None

    cmd = TestHelper.Cmd(verbose=True)
    config = ConfigParser.ConfigParser()
    config.read(os.environ['HARTMANNACTOR_DIR']+'/etc/hartmann.cfg')
    m,b,constants = hartmannActor_main.get_collimation_constants(config)

    cams = ['b1','r1','b2','r2']
    if args.m is not None:
        m = dict(zip(cams, [float(x) for x in args.m.split(',')]))
    if args.b is not None:
        b = dict(zip(cams, [float(x) for x in args.b.split(',')]))
    if args.bsteps is not None:
        constants['bsteps'] = args.bsteps
    if args.badres is not None:
        constants['badres'] = args.badres

    hart = boss_collimate.Hartmann(None, m, b, constants)

    hart.collimate(expnum1, indir=indir, mjd=mjd, cmd=cmd, moveMotors=False, plot=True)


if __name__ == '__main__':
    sys.exit(main())
