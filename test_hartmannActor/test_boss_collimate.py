"""
Test the Hartmann collimation routine converted from idlspec2d combsmallcollimate.
"""

import unittest
import pyfits
import ConfigParser

import numpy as np

import hartmannTester

from hartmannActor import hartmannActor_main
from hartmannActor import boss_collimate

def get_mjd(filename):
    return int(filename.split('/')[2])

def get_expnum(filename):
    """Return the exposure number from this filename."""
    return int(filename.split('-')[-1].split('.')[0])

# Note: to take sample test exposures, you can't use flavor "science",
# because that closes the screen, unless you alsof specify "hartmann=left/right"
# It's best to take these as "boss exposure arc"
data_dir = 'data/'

NeOff1 = 'sdR-r2-00169558.fit.gz'
NeOff2 = 'sdR-r2-00169559.fit.gz'
HgCdOff1 = 'sdR-r2-00169560.fit.gz'
HgCdOff2 = 'sdR-r2-00169561.fit.gz'
bothOff1 = 'sdR-r2-00169562.fit.gz'
bothOff2 = 'sdR-r2-00169563.fit.gz'

maskOut1 = 'sdR-r2-00169556.fit.gz'
maskOut2 = 'sdR-r2-00169557.fit.gz'
bothLeft1 = 'sdR-r2-00169552.fit.gz'
bothLeft2 = 'sdR-r2-00169553.fit.gz'
bothRight1 = 'sdR-r2-00169554.fit.gz'
bothRight2 = 'sdR-r2-00169555.fit.gz'

noFFS = None

notHartmann = None

focused1 = 'sdR-r2-00165006.fit.gz'
focused2 = 'sdR-r2-00165007.fit.gz'

notFocused1 = 'sdR-r2-00169546.fit.gz'
notFocused2 = 'sdR-r2-00169547.fit.gz'


class TestOneCam(hartmannTester.HartmannTester, unittest.TestCase):
    def setUp(self):
        super(TestOneCam,self).setUp()
        self.oneCam = boss_collimate.OneCam(self.cmd, None, None, 292., 0, 0, '')
        self.spec = 'sp2'
        self.cam = 'r2'
        self.oneCam.spec = self.spec
        self.oneCam.cam = self.cam

    def _check_Hartmann_header(self, filename, expect):
        header = pyfits.getheader(data_dir + filename)
        result = self.oneCam.check_Hartmann_header(header)
        self.assertEqual(result, expect)
    def test_check_Hartmann_header_left(self):
        self._check_Hartmann_header(focused1, 'left')
    def test_check_Hartmann_header_right(self):
        self._check_Hartmann_header(focused2, 'right')
    def test_check_Hartmann_header_None(self):
        self._check_Hartmann_header(maskOut1, None)

    def _bad_header(self, header, isBad, nWarn):
        result = self.oneCam.bad_header(header)
        self.assertEqual(result, isBad)
        self._check_cmd(0,0,nWarn,0,False)
    def test_bad_header_ok(self):
        header = pyfits.getheader(data_dir + focused1)
        self._bad_header(header, False, 0)
    def test_bad_header_noNe(self):
        header = pyfits.getheader(data_dir + NeOff1)
        self._bad_header(header, True, 1)
    def test_bad_header_noHgcd(self):
        header = pyfits.getheader(data_dir + HgCdOff1)
        self._bad_header(header, True, 1)
    def test_bad_header_noLamps(self):
        header = pyfits.getheader(data_dir + bothOff1)
        self._bad_header(header, True, 2)
    @unittest.skip('need file for this test!')
    def test_bad_header_noFFS(self):
        header = pyfits.getheader(data_dir + noFFS)
        self._bad_header(header, True, 1)
    @unittest.skip('need file for this test!')
    def test_bad_header_not_Hartmann(self):
        header = pyfits.getheader(data_dir + notHartmann)
        self._bad_header(header, True, 1)

    def _load_data(self, expnum1, expnum2):
        self.oneCam.cam = 'r2'
        self.oneCam._load_data(data_dir, expnum1, expnum2)
        self.assertIsInstance(self.oneCam.bigimg1, np.ndarray)
        self.assertIsInstance(self.oneCam.bigimg2, np.ndarray)
        msg = "Files should have different content."
        self.assertFalse((self.oneCam.bigimg1 == self.oneCam.bigimg2).all(), msg)
        self.assertIsInstance(self.oneCam.header1, pyfits.header.Header)
        self.assertIsInstance(self.oneCam.header2, pyfits.header.Header)
        self.assertFalse(self.oneCam.header1 == self.oneCam.header2, msg)
    def test_load_data_ok_focused(self):
        expnum1 = get_expnum(focused1)
        expnum2 = get_expnum(focused2)
        self._load_data(expnum1, expnum2)
    def test_load_data_ok_notFocused(self):
        expnum1 = get_expnum(notFocused1)
        expnum2 = get_expnum(notFocused2)
        self._load_data(expnum1, expnum2)

    def _load_data_not_ok(self, expnum1, expnum2, nWarn, errMsg):
        self.oneCam.cam = 'r2'
        with self.assertRaises(boss_collimate.HartError) as cm:
            self.oneCam._load_data(data_dir, expnum1, expnum2)
        self.assertIn(errMsg, cm.exception.message)
        self._check_cmd(0,0,nWarn,0,False)
    def test_load_data_NeOff(self):
        expnum1 = get_expnum(NeOff1)
        expnum2 = get_expnum(NeOff2)
        self._load_data_not_ok(expnum1, expnum2, 1, 'Incorrect header values in fits file.')
    def test_load_data_HgCdOff(self):
        expnum1 = get_expnum(HgCdOff1)
        expnum2 = get_expnum(HgCdOff2)
        self._load_data_not_ok(expnum1, expnum2, 1, 'Incorrect header values in fits file.')
    def test_load_data_BothOff(self):
        expnum1 = get_expnum(bothOff1)
        expnum2 = get_expnum(bothOff2)
        self._load_data_not_ok(expnum1, expnum2, 2, 'Incorrect header values in fits file.')
    def test_load_data_both_left(self):
        expnum1 = get_expnum(bothLeft1)
        expnum2 = get_expnum(bothLeft2)
        self._load_data_not_ok(expnum1, expnum2, 0, 'FITS headers indicate both exposures had same Hartmann position: left')
    def test_load_data_both_right(self):
        expnum1 = get_expnum(bothRight1)
        expnum2 = get_expnum(bothRight2)
        self._load_data_not_ok(expnum1, expnum2, 0, 'FITS headers indicate both exposures had same Hartmann position: right')
    def test_load_data_both_both_not(self):
        expnum1 = get_expnum(maskOut1)
        expnum2 = get_expnum(maskOut2)
        self._load_data_not_ok(expnum1, expnum2, 0, 'FITS headers do not indicate these are Hartmann exposures.')

class TestHartmann(hartmannTester.HartmannCallsTester, unittest.TestCase):
    def setUp(self):
        super(TestHartmann,self).setUp()
        self.actor.models = self.actorState.models
        config = ConfigParser.ConfigParser()
        config.read('../etc/hartmann.cfg')
        m,b = hartmannActor_main.get_collimation_constants(config)

        self.hart = boss_collimate.Hartmann(self.actor, m, b)
        self.hart.cmd = self.cmd
        
    def test_move_motors(self):
        self.hart.move_motors('sp2', 10)
        self._check_cmd(1,0,0,0,False)
    def test_move_motors_fails(self):
        self.cmd.failOn = 'boss moveColl spec=sp2 piston=20'
        with self.assertRaises(boss_collimate.HartError) as cm:
            self.hart.move_motors('sp2', 20)
        self.assertIn('Failed to move collimator pistons', cm.exception.message)
        self._check_cmd(1,0,0,0,False)

    def _take_hartmanns(self,nCalls,nInfo,nWarn,nErr, expect):
        result = self.hart.take_hartmanns(True)
        self.assertEqual(result,expect)
        self._check_cmd(nCalls,nInfo,nWarn,nErr, False)
    def test_take_hartmanns(self):
        self._take_hartmanns(2,3,0,0, [1234501,1234502])

    def _take_hartmanns_fails(self,nCalls,nInfo,nWarn,nErr, expect):
        with self.assertRaises(boss_collimate.HartError) as cm:
            self.hart.take_hartmanns(True)
        self.assertIn('Failed to take %s hartmann exposure'%expect, cm.exception.message)
        self._check_cmd(nCalls,nInfo,nWarn,nErr, False)
    def test_take_hartmanns_fails_left(self):
        self.cmd.failOn = "boss exposure arc hartmann=left itime=4 window=850,1400"
        self._take_hartmanns_fails(1,1,0,0, 'left')
    def test_take_hartmanns_fails_right(self):
        self.cmd.failOn = "boss exposure arc hartmann=right itime=4 window=850,1400 noflush"
        self._take_hartmanns_fails(2,2,0,0, 'right')

    def _lamps_tester(self, nInfo, nWarn, nErr, filename):
        """To help with lamp-off tests."""
        exp1 = get_expnum(filename)
        self.hart.collimate(exp1,indir=data_dir,cmd=self.cmd)
        self.assertFalse(self.hart.success)
        # NOTE: No good way to test the message levels due to multiprocessing
        # self._check_cmd(0,nInfo,nWarn,nErr,False)
    def test_no_Ne(self):
        """Test with a file that had all Ne lamps off."""
        self._lamps_tester(0,4,5,NeOff1)
    def test_no_HgCd(self):
        """Test with a file that had all HgCd lamps off."""
        self._lamps_tester(0,4,5,HgCdOff1)
    def test_no_Arcs(self):
        """Test with a file that had both arc lamps off."""
        self._lamps_tester(0,8,5,bothOff1)

    def _mask_tester(self,filename):
        """To help with hartmann position testing."""
        exp1 = get_expnum(filename)
        self.hart.collimate(exp1,indir=data_dir,cmd=self.cmd)
        self.assertFalse(self.hart.success)
        # NOTE: No good way to test the message levels due to multiprocessing
        # self._check_cmd(0,0,0,4,False)
    def test_both_left(self):
        """Test with a file where both members of the pair had Left Hartmanns."""
        self._mask_tester(bothLeft1)
    def test_both_right(self):
        """Test with a file where both members of the pair had Right Hartmanns."""
        self._mask_tester(bothRight1)
    def test_both_out(self):
        """Test with a file where both members of the pair had Hartmanns out."""
        self._mask_tester(maskOut1)
        
    @unittest.skip('need file for this test!')
    def test_no_light(self):
        """Test with a file that has no signal."""
        exp1 = get_expnum(notHartmann)
        self.hart.collimate(exp1,cmd=self.cmd)
        self.assertFalse(self.hart.success)

    def test_collimate_one_file(self):
        """Test collimating given left expnum, the subsequent expnum is right."""
        exp1 = get_expnum(notFocused1)
        self.hart.collimate(exp1,indir=data_dir,cmd=self.cmd)
        self.assertTrue(self.hart.success)
        # TBD: get correct result from combsmallcollimate.pro
    
    def test_collimate_two_files(self):
        """Test collimating with files in correct order (left->right)."""
        exp1 = get_expnum(focused1)
        exp2 = get_expnum(focused2)
        self.hart.collimate(exp1,exp2,indir=data_dir,cmd=self.cmd)
        self.assertTrue(self.hart.success)
        # TBD: get correct result from combsmallcollimate.pro
    
    def test_collimate_reverse_order(self):
        """Test collimating with files in reversed order (right->left)."""
        exp1 = get_expnum(focused1)
        exp2 = get_expnum(focused2)
        self.hart.collimate(exp2,exp1,indir=data_dir,cmd=self.cmd) # note reversed order!
        self.assertTrue(self.hart.success)
        # TBD: get correct result from combsmallcollimate.pro
    

    def test_call_exposure_fails(self):
        """Test collimating where the first file fails"""
        self.cmd.failOn = "boss exposure arc hartmann=left itime=4 window=850,1400"
        self.hart(self.cmd)
        self.assertFalse(self.hart.success)
        self._check_cmd(1,0,0,1,False)


if __name__ == '__main__':
    verbosity = 2

    unittest.main(verbosity=verbosity)
