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

# pre-cooked results for plotting, etc.
xshift = -2 + 0.5 * np.arange(80,dtype='f8')
b1coeff = np.array([13578575671.429024, 13957607760.156925, 14337598371.420261, 14717447732.466045, 15096056070.541536, 15472323612.894087, 15845150586.770298, 16213437219.41724, 16576083738.081778, 16931990370.01193, 17280057342.45355, 17619184882.654633, 17948273217.86175, 18266222575.321724, 18571933182.28212, 18864305265.98989, 19142239053.69136, 19404634772.63464, 19650392650.066315, 19878412913.23327, 20087595789.383163, 20277015761.6572, 20446444336.777508, 20595827277.360176, 20725110346.021767, 20834239305.37888, 20923159918.048275, 20991817946.645813, 21040159153.78829, 21068129302.09245, 21075674154.174366, 21062739472.650772, 21029271020.137966, 20975214559.252735, 20900515852.61114, 20805120662.829853, 20688974752.525707, 20552023884.31456, 20394213820.813583, 20215490324.638084, 20015799158.406033, 19795303191.89246, 19555033723.510025, 19296239158.831383, 19020167903.42841, 18728068362.872047, 18421188942.736286, 18100778048.592266, 17768084086.012638, 17424355460.56907, 17070840577.83293, 16708787843.37779, 16339445662.774652, 15964062441.596525, 15583886585.414814, 15200166499.801704, 14814150590.329466, 14427087262.57019, 14040224922.096468, 13654811974.479586, 13272096825.291769, 12893179861.398504, 12518569394.838352, 12148625718.942526, 11783709127.04213, 11424179912.46857, 11070398368.553396, 10722724788.62834, 10381519466.02454, 10047142694.0732, 9719954766.105919, 9400315975.454065, 9088586615.448889, 8785126979.42247, 8490297360.705311, 8204458052.629222, 7927969348.525747, 7661191541.72605, 7404484925.562016, 7158209793.364207])
r1coeff = np.array([448037727076.66925, 465178743372.0309, 482413041330.2614, 499697808009.79425, 516990230469.11383, 534247495766.63385, 551426790960.9138, 568485303110.3641, 585380219273.479, 602068726508.7711, 618508011874.6398, 634655262429.549, 650467665232.0454, 665902407340.5149, 680916675813.4915, 695467657709.4867, 709512540086.801, 723008510004.1033, 735912754519.6827, 748182460692.1958, 759774815579.9761, 770652012218.0188, 780796267547.0935, 790194804484.4994, 798834845947.5892, 806703614853.5004, 813788334119.5641, 820076226663.0332, 825554515401.2633, 830210423251.5308, 834031173130.913, 837003987956.9403, 839116090646.712, 840354704117.6395, 840707051286.8663, 840160355071.7391, 838701838389.5554, 836318724157.5428, 832998235292.9568, 828727594713.137, 823494025335.3344, 817293910443.0667, 810160274785.203, 802135303476.6964, 793261181632.6339, 783580094368.0962, 773134226798.0857, 761965764037.7272, 750116891202.0314, 737629793406.0483, 724546655764.8596, 710909663393.4697, 696761001406.9686, 682142854920.458, 667097409048.8734, 651666848907.4242, 635893359611.0226, 619819126274.7905, 603486334013.7858, 586937167943.0563, 570213813177.6438, 553356372831.9546, 536396622017.93915, 519364253846.831, 502288961429.9011, 485200437878.424, 468128376303.66656, 451102469816.9171, 434152411529.40753, 417307894552.42773, 400598611997.2289, 384054256975.121, 367704522597.3041, 351579101975.1195, 335707688219.7725, 320119974442.5837, 304845653754.7822, 289914419267.6543, 275355964092.457, 261199981340.48422])
b2coeff = np.array([6215102006.237334, 6439596160.1668825, 6674777758.993854, 6920215182.879749, 7175476811.987941, 7440131026.479864, 7713746206.518509, 7995890732.265784, 8286132983.883559, 8584041341.535022, 8889184185.382317, 9201129895.587463, 9519446852.312466, 9843703435.720144, 10173468025.973242, 10508309003.23286, 10847794747.662262, 11191493639.423399, 11538974058.67813, 11889804385.58937, 12243553000.319695, 12599658238.400503, 12957038256.840761, 13314481168.016745, 13670775084.309988, 14024708118.096334, 14375068381.755255, 14720643987.664656, 15060223048.20192, 15392593675.746435, 15716543982.675913, 16030862081.368279, 16334336084.202152, 16625754103.554977, 16903904251.806484, 17167574641.333492, 17415553384.514755, 17646628593.729195, 17859588381.353195, 18053220859.767124, 18226314141.34683, 18377897444.1188, 18507964408.686043, 18616749781.297783, 18704488308.20568, 18771414735.659363, 18817763809.910023, 18843770277.2056, 18849668883.798244, 18835694375.936085, 18802081499.87169, 18749065001.853535, 18676879628.131233, 18585760124.956383, 18475941238.580124, 18347657715.249393, 18201144301.21681, 18036635742.73088, 17854366786.04271, 17654572177.403187, 17437486663.059704, 17203492828.822605, 16953564618.723816, 16688823816.355843, 16410392205.308159, 16119391569.172375, 15816943691.54107, 15504170356.003452, 15182193346.1518, 14852134445.576103, 14515115437.86787, 14172258106.618378, 13824684235.418943, 13473515607.860247, 13119874007.532831, 12764881218.028908, 12409659022.938604, 12055329205.853508, 11703013550.364073, 11353833840.06179])
r2coeff = np.array([171572249095.39206, 183870682220.3686, 196727396548.4785, 210119542800.25476, 224024271696.27283, 238418733957.05466, 253280080303.20804, 268585461455.26157, 284312028133.76776, 300436931059.3103, 316937320952.45905, 333790348533.71576, 350973164523.6707, 368462919642.92114, 386236764611.96027, 404271850151.3711, 422545326981.7156, 441034345823.5666, 459716057397.4656, 478567612423.995, 497566161623.6713, 516683413194.56946, 535869305244.7258, 555068333359.6703, 574224993124.9105, 593283780126.0009, 612189189948.3983, 630885718177.7086, 649317860399.4312, 667430112199.0707, 685166969162.1477, 702472926874.2354, 719292480920.7854, 735570126887.4437, 751250360359.6256, 766277676922.871, 780596572162.761, 794151541664.7549, 806887081014.4095, 818747685797.2281, 829677851598.8079, 839631030987.489, 848596504463.2169, 856572509508.8743, 863557283607.2577, 869549064241.2172, 874546088893.5471, 878546595047.1558, 881548820184.8052, 883551001789.4222, 884551377343.7395, 884548184330.6407, 883539660232.9941, 881524042533.5338, 878499568715.1818, 874464476260.7167, 869417002653.0327, 863355385374.862, 856277861909.1862, 848182669738.7205, 839068046346.3771, 828941819502.0612, 817850178124.0856, 805848901417.9838, 792993768589.18, 779340558843.1932, 764945051385.492, 749863025421.4889, 734150260156.707, 717862534796.5885, 701055628546.5847, 683785320612.1844, 666107390198.9094, 648077616512.1265, 629751778757.4061, 611185656140.107, 592435027865.7836, 573555673139.8604, 554603371167.8221, 535633901155.15186])
b1 = boss_collimate.OneCamResult('b1', True, xshift, b1coeff, 30, -0.5, -2157)
r1 = boss_collimate.OneCamResult('r1', True, xshift, r1coeff, 34, -0.3, -1921)
b2 = boss_collimate.OneCamResult('b2', True, xshift, b2coeff, 48, 0.4, 903)
r2 = boss_collimate.OneCamResult('r2', True, xshift, r2coeff, 50, 0.5, 3638)
full_result = {'sp1':{'b':b1,'r':r1},'sp2':{'b':b2,'r':r2}}

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
        m,b,constants = hartmannActor_main.get_collimation_constants(config)

        self.hart = boss_collimate.Hartmann(self.actor, m, b, constants)
        self.hart.cmd = self.cmd
        self.hart.mjd = 12345
        
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

    def test_make_plot(self):
        exp1 = get_expnum(notFocused1)
        exp2 = get_expnum(notFocused2)
        self.hart.mjd = 12345
        self.hart.full_result = full_result
        self.hart.make_plot(exp1, exp2)
        
    @unittest.skip('need file for this test!')
    def test_no_light(self):
        """Test with a file that has no signal."""
        exp1 = get_expnum(notHartmann)
        self.hart.collimate(exp1,cmd=self.cmd)
        self.assertFalse(self.hart.success)

    def test_collimate_one_file(self):
        """Test collimating given left expnum, the subsequent expnum is right."""
        expect = {'sp1':{'b':-1,'r':-1},'sp2':{'b':-1,'r':-1}}
        exp1 = get_expnum(notFocused1)
        self.hart.collimate(exp1,indir=data_dir,cmd=self.cmd,plot=True)
        self.assertTrue(self.hart.success)
        # TBD: get correct result from combsmallcollimate.pro
        self.assertEqual(expect, self.hart.result)
    
    def test_collimate_two_files(self):
        """Test collimating with files in correct order (left->right)."""
        expect = {'sp1':{'b':-1,'r':-1},'sp2':{'b':-1,'r':-1}}
        exp1 = get_expnum(focused1)
        exp2 = get_expnum(focused2)
        self.hart.collimate(exp1,exp2,indir=data_dir,cmd=self.cmd,plot=True)
        self.assertTrue(self.hart.success)
        # TBD: get correct result from combsmallcollimate.pro
        self.assertEqual(expect, self.hart.result)

    def test_collimate_reverse_order(self):
        """Test collimating with files in reversed order (right->left)."""
        expect = {'sp1':{'b':-1,'r':-1},'sp2':{'b':-1,'r':-1}}
        exp1 = get_expnum(focused1)
        exp2 = get_expnum(focused2)
        self.hart.collimate(exp2,exp1,indir=data_dir,cmd=self.cmd,plot=True) # note reversed order!
        self.assertTrue(self.hart.success)
        # TBD: get correct result from combsmallcollimate.pro
        self.assertEqual(expect, self.hart.result)

    def test_call_exposure_fails(self):
        """Test collimating where the first file fails"""
        self.cmd.failOn = 'boss exposure arc hartmann=left itime=4 window=850,1400'
        self.hart(self.cmd,plot=True)
        self.assertFalse(self.hart.success)
        self._check_cmd(1,2,0,1,False)


if __name__ == '__main__':
    verbosity = 2

    suite = None
    # suite = unittest.TestLoader().loadTestsFromName('test_boss_collimate.TestHartmann.test_make_plot_notFocused')
    if suite:
        unittest.TextTestRunner(verbosity=verbosity).run(suite)
    else:
        unittest.main(verbosity=verbosity)
