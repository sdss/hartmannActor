#!/usr/bin/env python
"""An actor to generate and process hartmann frames."""

import opscore.utility.sdss3logging as sdss3logging
import logging

from twisted.internet import reactor

import opscore.actor.model
import actorcore.Actor

class SOS(actorcore.Actor.Actor):
    def __init__(self, name, productName=None, configFile=None, debugLevel=10):
        actorcore.Actor.Actor.__init__(self, name, productName=productName, configFile=configFile)

        self.headURL = '$HeadURL: svn+ssh://sdss3svn@sdss3.org/repo/ops/actors/sosActor/trunk/python/sosActor/sosActor_main.py $'

        self.logger.setLevel(debugLevel)
        self.logger.propagate = True

        self.models = {}
        for actor in 'boss',:
            self.models[actor] = opscore.actor.model.Model(actor)

        m,b = self.get_collimation_constants()

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

    def get_collimation_constants(self):
        """Get the collimation constants from the config file."""
        m = {}
        b = {}
        for x in self.config.options('m'):
            m[x] = self.config.getfloat('m',x)
        for x in self.config.options('b'):
            b[x] = self.config.getfloat('b',x)
        return m,b
#
# To work
#
if __name__ == '__main__':
    sos = SOS('sos', 'sosActor', debugLevel=5)
