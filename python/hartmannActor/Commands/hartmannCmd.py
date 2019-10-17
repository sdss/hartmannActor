#!/usr/bin/env python
"""
Define available commands for hartmannActor.
"""

import time

import hartmannActor.myGlobals as myGlobals
import opscore.protocols.keys as keys
import opscore.protocols.types as types
import RO.Astro.Tm.MJDFromPyTuple as astroMJD
from hartmannActor import boss_collimate


class hartmannCmd(object):
    """Wrap commands to the hartmann actor"""

    def __init__(self, actor):

        self.actor = actor

        # Declare commands
        self.keys = keys.KeysDictionary(
            'hartmann_hartmann', (1, 1),
            keys.Key('id', types.Int(),
                     help='first exposure number of Hartmann pair to process.'),
            keys.Key('id2', types.Int(),
                     help='second exposure number of Hartmann to process (default: id+1).'),
            keys.Key('mjd', types.Int(),
                     help='MJD of the Hartmann pair to process (default: current MJD).'),
            keys.Key('noCorrect',
                     help='if set, do not apply any recommended corrections.'),
            keys.Key('noSubframe',
                     help='if set, take fullframe images.'),
            keys.Key('ignoreResiduals',
                     help='if set, apply red moves regardless of resulting blue residuals.'),
            keys.Key('noCheckImage',
                     help='if set, do not check the flux level in the image '
                          '(useful for sparse plugged plates).'),
            keys.Key('minBlueCorrection',
                     help='if set, the calculated correction for the blue ring will be '
                          'the minimum to get in the tolerance range.'),
            keys.Key('bypass', types.String(),
                     help='a list of checks and systems to bypass'),
            keys.Key('cameras', types.String(), help='a list of cameras to process'),
        )

        self.vocab = [
            ('ping', '', self.ping),
            ('status', '', self.status),
            ('collimate', '[noCorrect] [noSubframe] [ignoreResiduals] [noCheckImage] '
                          '[minBlueCorrection] [<bypass>] [<cameras>]', self.collimate),
            ('recompute', '<id> [<id2>] [<mjd>] [noCorrect] '
                          '[noCheckImage] [<bypass>] [<cameras>]', self.recompute),
        ]

    def ping(self, cmd):
        """Query the actor for liveness/happiness."""
        cmd.inform('status=%s' % myGlobals.hartmannStatus)
        cmd.finish("text='Pong'")

    def status(self, cmd, finish=True):
        """Report status and version; obtain and send current data"""

        self.actor.sendVersionKey(cmd)
        cmd.inform('status=%s' % myGlobals.hartmannStatus)
        cmd.inform('specs=%s' % ','.join(myGlobals.specs))
        cmd.inform('cameras=%s' % ','.join(myGlobals.cameras))

        if finish:
            cmd.finish()

    def recompute(self, cmd):
        """Reduce a given pair of already taken exposures."""

        hartmann = myGlobals.hartmann
        keywords = cmd.cmd.keywords

        expnum1 = int(keywords['id'].values[0])
        expnum2 = int(keywords['id2'].values[0]) if 'id2' in keywords else None

        if 'mjd' in keywords:
            mjd = int(keywords['mjd'].values[0])
        else:
            # SDSS MJD is truncated (MJD_TAI + 0.3)
            mjd = int(astroMJD.mjdFromPyTuple(time.gmtime()) + 0.3)

        moveMotors = 'noCorrect' not in keywords
        noCheckImage = 'noCheckImage' in keywords
        cameras = keywords['cameras'].values[0].split(',') if 'cameras' in keywords else None

        if 'bypass' in cmd.cmd.keywords:
            bypass = cmd.cmd.keywords['bypass'].values[0].split(',')
        else:
            bypass = []

        hartmann.reinit()
        hartmann.collimate(expnum1, expnum2=expnum2, mjd=mjd, cmd=cmd,
                           noCheckImage=noCheckImage, bypass=bypass,
                           cameras=cameras)
        if hartmann.success and moveMotors:
            hartmann.move_motors()

        boss_collimate.update_status(cmd, 'idle')
        if hartmann.success:
            cmd.finish()
        else:
            cmd.fail('text="Collimation process failed"')

    def collimate(self, cmd):
        """Take and reduce a pair of hartmann exposures.

        Assumes the arc lamps are already on. Apply the recommended collimator
        moves unless noCorrect is specified.

        """

        keywords = cmd.cmd.keywords

        hartmann = myGlobals.hartmann
        moveMotors = 'noCorrect' not in keywords
        subFrame = 'noSubframe' not in keywords
        ignoreResiduals = 'ignoreResiduals' in keywords
        noCheckImage = 'noCheckImage' in keywords
        minBlueCorrection = 'minBlueCorrection' in keywords
        cameras = keywords['cameras'].values[0].split(',') if 'cameras' in keywords else None

        if 'bypass' in keywords:
            bypass = keywords['bypass'].values[0].split(',')
        else:
            bypass = []

        if ignoreResiduals and not moveMotors:
            cmd.fail('text=ignoreResiduals and noCorrect are mutually exclusive!')
            return

        hartmann.reinit()

        hartmann(cmd,
                 moveMotors=moveMotors,
                 subFrame=subFrame,
                 ignoreResiduals=ignoreResiduals,
                 noCheckImage=noCheckImage,
                 minBlueCorrection=minBlueCorrection,
                 bypass=bypass,
                 cameras=cameras)

        if hartmann.success:
            cmd.finish()
        else:
            cmd.fail('text="collimation process failed"')
