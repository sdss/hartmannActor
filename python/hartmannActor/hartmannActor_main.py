#!/usr/bin/env python
"""An actor to generate and process hartmann frames."""

from twisted.internet import reactor

import actorcore.Actor
import opscore.actor.model
from hartmannActor import __version__, boss_collimate, myGlobals


def get_collimation_constants(config):
    """Get the collimation constants from the config file."""
    m = {}
    b = {}
    constants = {}
    coeff = {}
    for x in config.options('m'):
        m[x] = config.getfloat('m', x)

    for x in config.options('b'):
        b[x] = config.getfloat('b', x)

    for x in config.options('constants'):
        constants[x] = config.getfloat('constants', x)

    for x in config.options('coeff'):
        coeff[x] = config.getfloat('coeff', x)

    return m, b, constants, coeff


class Hartmann(actorcore.Actor.Actor):

    def __init__(self, name, productName=None, configFile=None, debugLevel=10):

        self.headURL = '$HeadURL$'
        self.version = __version__

        actorcore.Actor.Actor.__init__(self, name, productName=productName, configFile=configFile)

        self.logger.setLevel(debugLevel)
        # self.logger.propagate = True

        self.models = {}
        for actor in 'boss', :
            self.models[actor] = opscore.actor.model.Model(actor)

        m, b, constants, coeff = get_collimation_constants(self.config)
        myGlobals.hartmann = boss_collimate.Hartmann(self, m, b, constants, coeff)

        # Finally start the reactor
        self.run()

    def periodicStatus(self):
        """ """

        self.callCommand('status')
        reactor.callLater(3600, self.periodicStatus)

    def connectionMade(self):
        '''Runs this after connection is made to the hub'''

        # Schedule an update.
        self.periodicStatus()


if __name__ == '__main__':
    hartmann = Hartmann('hartmann', 'hartmannActor', debugLevel=5)
