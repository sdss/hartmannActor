"""
Tests for the various hartmannCmds, using the full command structure.
"""

import ConfigParser
import unittest
import time

from hartmannActor import hartmannActor_main, boss_collimate
import hartmannActor.myGlobals as myGlobals
import hartmannTester

import RO.Astro.Tm.MJDFromPyTuple as astroMJD

class FakeHartmann():
    """Fake calls to the Hartmann class, with either success or failure."""
    def __init__(self, success):
        self.success = success
    def reinit(self):
        pass
    def __call__(self, cmd, **kwargs):
        self.cmd = cmd
        self.kwargs = kwargs
        return self.success
    def collimate(self, expnum1, **kwargs):
        self.expnum1 = expnum1
        self.kwargs = kwargs
        return self.success

class HartmannCmdTester(hartmannTester.HartmannTester):
    def setUp(self):
        self.verbose = True
        super(HartmannCmdTester,self).setUp()
        self.timeout = 1

        self.actor.models = self.actorState.models
        config = ConfigParser.ConfigParser()
        config.read('../etc/hartmann.cfg')
        m,b,constants,coeff = hartmannActor_main.get_collimation_constants(config)
        self.hart = boss_collimate.Hartmann(self.actor, m, b, constants, coeff)
        self.hart.cmd = self.cmd


class TestHartmannCmd(HartmannCmdTester,unittest.TestCase):
    def test_ping(self):
        self._run_cmd('ping', None)
        self._check_cmd(0,1,0,0,True)

    def test_status(self):
        self._run_cmd('status', None)
        self._check_cmd(0,2,0,0,True)

    def _recompute(self, args, expect, success=True):
        hart = FakeHartmann(success)
        myGlobals.hartmann = hart
        self._run_cmd('recompute %s'%args, None)
        self._check_cmd(0,0,0,0, True, not success)
        self.assertEqual(hart.expnum1,expect['expnum1'])
        self.assertEqual(hart.kwargs['expnum2'],expect.get('expnum2'))
        self.assertEqual(hart.kwargs['mjd'],expect.get('mjd'))
        self.assertEqual(hart.kwargs['moveMotors'],expect.get('moveMotors',True))
    def test_recompute_ok(self):
        expect = {'expnum1':1, 'mjd':12345}
        self._recompute('id={expnum1} mjd={mjd}'.format(**expect), expect, success=True)
    def test_recompute_no_move(self):
        currentMJD = int(astroMJD.mjdFromPyTuple(time.gmtime())+0.3)
        expect = {'expnum1':3, 'mjd':currentMJD, 'moveMotors':False}
        self._recompute('id={expnum1} noCorrect'.format(**expect), expect, success=True)
    def test_recompute_fails(self):
        expect = {'expnum1':1, 'expnum2':5, 'mjd':12345}
        self._recompute('id={expnum1} id2={expnum2} mjd={mjd}'.format(**expect), expect, success=False)

    def _collimate(self, args, expect, success=True):
        hart = FakeHartmann(success)
        myGlobals.hartmann = hart
        self._run_cmd('collimate %s'%args, None)
        self._check_cmd(0,0,0,0, True, not success)
        self.assertEqual(hart.kwargs['moveMotors'],expect.get('moveMotors',True))
        self.assertEqual(hart.kwargs['subFrame'],expect.get('subFrame',True))
    def test_collimate_ok(self):
        expect = {}
        self._collimate('', expect, success=True)
    def test_collimate_no_move_no_subFrame(self):
        expect = {'moveMotors':False, 'subFrame':False}
        self._collimate('noCorrect noSubframe', expect, success=True)
    def test_collimate_fails(self):
        expect = {}
        self._collimate('', expect, success=False)



if __name__ == '__main__':
    verbosity = 2

    unittest.main(verbosity=verbosity)
