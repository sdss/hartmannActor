#!/usr/bin/env python
"""
Define available commands for hartmannActor.
"""


import time

import opscore.protocols.keys as keys
import opscore.protocols.types as types
from opscore.utility.qstr import qstr

import RO.Astro.Tm.MJDFromPyTuple as astroMJD

import hartmannActor.myGlobals as myGlobals

class hartmannCmd(object):
    '''Wrap commands to the hartmann actor'''

    def __init__(self, actor):
        self.actor = actor
        #
        # Declare commands
        #
        self.keys = keys.KeysDictionary("hartmann_hartmann", (1,1),
                                        keys.Key("id", types.Int(), help="first exposure number of Hartmann pair to process."),
                                        keys.Key("id2", types.Int(), help="second exposure number of Hartmann to process (default: id+1)."),
                                        keys.Key("mjd", types.Int(), help="MJD of the Hartmann pair to process (default: current MJD)."),
                                        keys.Key("noCorrect", help="if set, do not apply any recommended corrections."),
                                        keys.Key("noSubframe", help="if set, take fullframe images."),
                                        )

        self.vocab = [
            ('ping', '', self.ping),
            ('status', '', self.status),
            ('collimate', '[noCorrect] [noSubframe]', self.collimate),
            ('recompute', '<id> [<id2>] [<mjd>] [noCorrect]', self.recompute),
        ]

    def ping(self, cmd):
        '''Query the actor for liveness/happiness.'''
        cmd.inform("status=%s"%myGlobals.hartmannStatus)
        cmd.finish("text='Pong'")

    def status(self, cmd, finish=True):
        '''Report status and version; obtain and send current data'''

        self.actor.sendVersionKey(cmd)
        cmd.inform("status=%s"%myGlobals.hartmannStatus)
        if finish:
            cmd.finish()

    def recompute(self, cmd):
        """ Reduce a given pair of already taken exposures. """
        hartmann = myGlobals.hartmann
        keywords = cmd.cmd.keywords
        expnum1 = int(keywords['id'].values[0])
        expnum2 = int(keywords['id2'].values[0]) if 'id2' in keywords else None
        if 'mjd' in keywords:
            mjd = int(keywords['mjd'].values[0])
        else:
            # SDSS MJD is truncaded (MJD_TAI + 0.3)
            mjd = int(astroMJD.mjdFromPyTuple(time.gmtime())+0.3)

        moveMotors = "noCorrect" not in keywords

        hartmann.reinit()
        hartmann.collimate(expnum1, expnum2=expnum2, mjd=mjd, cmd=cmd)
        if hartmann.success and moveMotors:
            hartmann.move_motors()
        
        if hartmann.success:
            cmd.finish()
        else:
            cmd.fail('text="Collimation process failed"')
    
    def collimate(self, cmd):
        """
        Take and reduce a pair of hartmann exposures, assuming the arc lamps are already on.
        Apply the recommended collimator moves unless noCorrect is specified.
        """
        hartmann = myGlobals.hartmann
        moveMotors = "noCorrect" not in cmd.cmd.keywords
        subFrame = "noSubframe" not in cmd.cmd.keywords
        
        hartmann.reinit()
        hartmann(cmd, moveMotors=moveMotors, subFrame=subFrame)
        if hartmann.success:
            cmd.finish()
        else:
            cmd.fail('text="collimation process failed"')
