#!/usr/bin/env python
"""An actor to generate and process hartmann frames."""

import sys

import actorcore.Actor
import opscore.actor.model
from twisted.internet import reactor

from hartmannActor import __version__, boss_collimate, myGlobals


def get_collimation_constants(config):
    """Get the collimation constants from the config file."""

    m = {}
    b = {}
    constants = {}
    coeff = {}

    for x in config['m'].keys():
        m[x] = config['m'][x]

    for x in config['b'].keys():
        b[x] = config['b'][x]

    for x in config['constants'].keys():
        constants[x] = config['constants'][x]

    for x in config['coeff'].keys():
        coeff[x] = config['coeff'][x]

    return m, b, constants, coeff


class HartmannActor(actorcore.Actor.SDSSActor):
    """The Platedb actor main class."""

    @staticmethod
    def newActor(location=None, **kwargs):
        """Return the version of the actor based on our location."""

        # Determines the location (this method is defined in SDSSActor)
        location = HartmannActor.determine_location(location)

        # Creates the appropriate object depending on the location
        if location == 'APO':
            return HartmannActorAPO('hartmann', productName='hartmannActor', **kwargs)
        elif location == 'LCO':
            return HartmannActorLCO('hartmann', productName='hartmannActor', **kwargs)
        elif location == 'LOCAL':
            return HartmannActorLocal('hartmann', productName='hartmannActor', **kwargs)
        else:
            raise KeyError('Don\'t know my location: cannot return a working Actor!')

    def __init__(self,
                 name,
                 productName=None,
                 configFile=None,
                 debugLevel=30,
                 makeCmdrConnection=True):

        self.version = __version__

        actorcore.Actor.SDSSActor.__init__(self, name, productName=productName,
                                           configFile=configFile)

        self.logger.setLevel(debugLevel)
        # self.logger.propagate = True

        self.models = {}
        for actor in 'boss', :
            self.models[actor] = opscore.actor.model.Model(actor)

        myGlobals.config = self.config
        myGlobals.models = self.models
        myGlobals.actor = self

        m, b, constants, coeff = get_collimation_constants(self.config)
        myGlobals.hartmann = boss_collimate.Hartmann(self, m, b, constants, coeff)
        myGlobals.hartmann_thread = None

        # Spectrographs to process.
        myGlobals.specs = self.config['spec']['specs'].split(' ')
        myGlobals.cameras = self.config['spec']['cameras'].split(' ')

    def periodicStatus(self):
        """ """

        self.callCommand('status')
        reactor.callLater(3600, self.periodicStatus)

    def connectionMade(self):
        '''Runs this after connection is made to the hub'''

        # Schedule an update.
        self.periodicStatus()


class HartmannActorAPO(HartmannActor):
    """APO version of this actor."""
    location = 'APO'


class HartmannActorLCO(HartmannActor):
    """LCO version of this actor."""
    location = 'LCO'


class HartmannActorLocal(HartmannActor):
    """Local Version of this actor."""
    location = 'LOCAL'


def run_actor():

    if len(sys.argv) > 1:
        location = sys.argv[1]
    else:
        location = None

    hartmann = HartmannActor.newActor(location=location)
    hartmann.run()


if __name__ == '__main__':

    run_actor()
