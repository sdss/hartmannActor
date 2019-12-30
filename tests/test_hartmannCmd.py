"""
Tests for the various hartmannCmds, using the full command structure.
"""


import unittest

import astropy.time

import hartmannActor.myGlobals as myGlobals
from hartmannActor import boss_collimate, hartmann

from . import hartmannTester
from .test_boss_collimate import config


class FakeHartmann():
    """Fake calls to the Hartmann class, with either success or failure."""

    def __init__(self, success):
        self.success = success
        self.moved = False

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

    def move_motors(self):
        self.moved = True
        return True


class HartmannCmdTester(hartmannTester.HartmannTester):

    def setUp(self):
        self.verbose = True
        super(HartmannCmdTester, self).setUp()
        self.timeout = 1

        self.actor.models = self.actorState.models

        m, b, constants, coeff = hartmann.get_collimation_constants(config)
        self.hart = boss_collimate.Hartmann(self.actor, m, b, constants, coeff)
        self.hart.cmd = self.cmd

        myGlobals.specs = config['spec']['specs'].split(' ')
        myGlobals.cameras = config['spec']['cameras'].split(' ')


class TestHartmannCmd(HartmannCmdTester, unittest.TestCase):

    def test_ping(self):
        self._run_cmd('ping', None)
        self._check_cmd(0, 1, 0, 0, True)

    def test_status(self):
        self._run_cmd('status', None)
        self._check_cmd(0, 4, 0, 0, True)

    def _recompute(self, args, expect, success=True):
        hart = FakeHartmann(success)
        myGlobals.hartmann = hart
        self._run_cmd('recompute %s' % args, None)
        self._check_cmd(0, 1, 0, 0, True, not success)
        self.assertEqual(hart.expnum1, expect['expnum1'])
        self.assertEqual(hart.kwargs['expnum2'], expect.get('expnum2'))
        self.assertEqual(hart.kwargs['mjd'], expect.get('mjd'))
        self.assertEqual(hart.moved, expect.get('moveMotors', True))
        self.assertEqual(hart.kwargs['noCheckImage'], expect.get('noCheckImage', False))

    def test_recompute_ok(self):
        expect = {'expnum1': 1, 'mjd': 12345}
        self._recompute('id={expnum1} mjd={mjd}'.format(**expect), expect, success=True)

    def test_recompute_no_move(self):
        currentMJD = int(astropy.time.Time.now().mjd + 0.3)
        expect = {'expnum1': 3, 'mjd': currentMJD, 'moveMotors': False}
        self._recompute('id={expnum1} noCorrect'.format(**expect), expect, success=True)

    def test_recompute_fails(self):
        expect = {'expnum1': 1, 'expnum2': 5, 'mjd': 12345, 'moveMotors': False}
        self._recompute(
            'id={expnum1} id2={expnum2} mjd={mjd}'.format(**expect), expect, success=False)

    def test_recompute_noCheckImage(self):
        expect = {'expnum1': 1, 'mjd': 12345, 'noCheckImage': True}
        self._recompute(
            'id={expnum1} mjd={mjd} noCheckImage'.format(**expect), expect, success=True)

    def test_recompute_bypass(self):
        expect = {'expnum1': 1, 'mjd': 12345, 'bypass': ['ffs']}
        self._recompute('id={expnum1} mjd={mjd} bypass="ffs"'.format(**expect),
                        expect, success=True)

    def _collimate(self, args, expect, success=True):
        hart = FakeHartmann(success)
        myGlobals.hartmann = hart
        self._run_cmd('collimate %s' % args, None)
        self._check_cmd(0, 0, 0, 0, True, not success)
        self.assertEqual(hart.kwargs['moveMotors'], expect.get('moveMotors', True))
        self.assertEqual(hart.kwargs['subFrame'], expect.get('subFrame', True))
        self.assertEqual(hart.kwargs['ignoreResiduals'], expect.get('ignoreResiduals', False))
        self.assertEqual(hart.kwargs['noCheckImage'], expect.get('noCheckImage', False))
        self.assertEqual(hart.kwargs['bypass'], expect.get('bypass', []))

    def test_collimate_ok(self):
        expect = {}
        self._collimate('', expect, success=True)

    def test_collimate_no_move_no_subFrame(self):
        expect = {'moveMotors': False, 'subFrame': False}
        self._collimate('noCorrect noSubframe', expect, success=True)

    def test_collimate_fails(self):
        expect = {}
        self._collimate('', expect, success=False)

    def test_ignoreResiduals(self):
        expect = {'ignoreResiduals': True, 'moveMotors': True}
        self._collimate('ignoreResiduals', expect, success=True)

    def test_ignoreResiduals_moveMotors_collide(self):
        args = 'ignoreResiduals noCorrect'
        self._run_cmd('collimate %s' % args, None)
        self._check_cmd(0, 0, 0, 0, True, True)

    def test_noCheckImage(self):
        expect = {'noCheckImage': True}
        self._collimate('noCheckImage', expect, success=True)

    def test_collimate_bypass_ffs(self):
        expect = {'bypass': ['ffs']}
        self._collimate('bypass="ffs"', expect, success=True)

    def test_collimate_bypass_multiple(self):
        expect = {'bypass': ['ffs', 'hola']}
        self._collimate('bypass="ffs,hola"', expect, success=True)
