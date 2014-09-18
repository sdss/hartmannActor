#!/usr/bin/env python
"""Compute the collimator moves for an already-taken Hartmann pair."""

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

    args = parser.parse_args()

    exp1 = args.FILE1
    indir,expnum1 = os.path.split(exp1)
    expnum1 = get_expnum(expnum1)

    cmd = TestHelper.Cmd(verbose=True)
    config = ConfigParser.ConfigParser()
    config.read('../etc/hartmann.cfg')
    m,b = hartmannActor_main.get_collimation_constants(config)

    hart = boss_collimate.Hartmann(None, m, b)

    hart.collimate(expnum1, indir=indir, cmd=cmd, moveMotors=False)#, plot=True)


if __name__ == '__main__':
    sys.exit(main())
