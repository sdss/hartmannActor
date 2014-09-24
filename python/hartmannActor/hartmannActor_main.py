#!/usr/bin/env python
"""An actor to generate and process hartmann frames."""

import opscore.utility.sdss3logging as sdss3logging
import logging

from twisted.internet import reactor

import opscore.actor.model
import actorcore.Actor

from hartmannActor import boss_collimate, myGlobals

def get_collimation_constants(config):
    """Get the collimation constants from the config file."""
    m = {}
    b = {}
    constants = {}
    coeff = {}
    for x in config.options('m'):
        m[x] = config.getfloat('m',x)

    for x in config.options('b'):
        b[x] = config.getfloat('b',x)

    for x in config.options('constants'):
        constants[x] = config.getfloat('constants',x)

    for x in config.options('coeff'):
        coeff[x] = config.getfloat('coeff',x)

    return m,b,constants, coeff

class Hartmann(actorcore.Actor.Actor):
    def __init__(self, name, productName=None, configFile=None, debugLevel=10):
        actorcore.Actor.Actor.__init__(self, name, productName=productName, configFile=configFile)

        self.headURL = '$HeadURL: svn+ssh://sdss3svn@sdss3.org/repo/ops/actors/hartmannActor/trunk/python/hartmannActor/hartmannActor_main.py $'

        self.logger.setLevel(debugLevel)
        self.logger.propagate = True

        self.models = {}
        for actor in 'boss',:
            self.models[actor] = opscore.actor.model.Model(actor)

        m,b,constants,coeff = get_collimation_constants(self.config)
        myGlobals.hartmann = boss_collimate.Hartmann(self, m, b, constants, coeff)

        #
        # Finally start the reactor
        #
        self.run()

    def periodicStatus(self):
        """ """

        self.callCommand("status")
        reactor.callLater(3600, self.periodicStatus)

    def connectionMade(self):
        '''Runs this after connection is made to the hub'''

        # Schedule an update.
        #
        self.periodicStatus()

#
# To work
#
if __name__ == '__main__':
    hartmann = Hartmann('hartmann', 'hartmannActor', debugLevel=5)
