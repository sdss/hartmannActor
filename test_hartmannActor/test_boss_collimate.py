"""
Test the Hartmann collimation routine converted from idlspec2d combsmallcollimate.
"""
import unittest

from opscore.actor.model import Model
from opscore.actor import cmdkeydispatcher

from hartmannActor import boss_collimate

from multiprocessing import Lock, Manager

class Cmd(object):
    def __init__(self):
        """Save the level of any messages that pass through."""
        self._messages = Manager().Value(str,'')
        self.lock = Lock()
    @property
    def messages(self):
        return self._messages.value
    def _msg(self,txt,level):
        print level,txt
        with self.lock:
            self._messages.value += level
    def inform(self,txt):
        self._msg(txt,'i')
    def diag(self,txt):
        self._msg(txt,'d')
    def warn(self,txt):
        self._msg(txt,'w')
    def fail(self,txt):
        self._msg(txt,'f')
    def error(self,txt):
        self._msg(txt,'e')

class Actor(object):
    def __init__(self,name):
        self.name = name
        self.models = {}
        if not Model.dispatcher:
            dispatcher = cmdkeydispatcher.CmdKeyVarDispatcher('test_hartmann')
            Model.setDispatcher(dispatcher)
            self.models['boss'] = Model('boss')

def get_expnum(filename):
    return int(filename.split('.fit')[0].split('-')[-1])

def get_mjd(filename):
    return int(filename.split('/')[2])

class Test_boss_collimate(unittest.TestCase):
    def setUp(self):
        #import pdb
        #pdb.set_trace()
        actor = Actor('hartmann')#,productName='hartmannActor')
        #actor.models['boss'] = Model('boss')
                        
        self.cmd = Cmd()
        self.hart = boss_collimate.Hartmann(actor)
        
        # Note: to take sample test exposures, you can't use flavor "science",
        # because that closes the screen, unless you also specify "hartmann=left/right"
        # It's best to take these as "boss exposure arc"
        self.ffsOpen = ''
        self.ffsSomeClosed = ''
        
        self.NeOff1 = '/data/spectro/56612/sdR-r2-00169558.fit.gz'
        self.NeOff2 = '/data/spectro/56612/sdR-r2-00169559.fit.gz'
        self.HgCdOff1 = '/data/spectro/56612/sdR-r2-00169560.fit.gz'
        self.HgCdOff2 = '/data/spectro/56612/sdR-r2-00169561.fit.gz'
        self.bothOff1 = '/data/spectro/56612/sdR-r2-00169562.fit.gz'
        self.bothOff2 = '/data/spectro/56612/sdR-r2-00169563.fit.gz'
        
        self.maskOut1 = '/data/spectro/56612/sdR-r2-00169556.fit.gz'
        self.maskOut2 = '/data/spectro/56612/sdR-r2-00169557.fit.gz'
        self.bothLeft1 = '/data/spectro/56612/sdR-r2-00169552.fit.gz'
        self.bothLeft2 = '/data/spectro/56612/sdR-r2-00169553.fit.gz'
        self.bothRight1 = '/data/spectro/56612/sdR-r2-00169554.fit.gz'
        self.bothRight2 = '/data/spectro/56612/sdR-r2-00169555.fit.gz'
        
        self.notHartmann = '/data/spectro/56526/sdR-r2-00165131.fit.gz'
        
        self.focused1 = '/data/spectro/56492/sdR-r2-00165006.fit.gz'
        self.focused2 = '/data/spectro/56492/sdR-r2-00165007.fit.gz'
        
        self.notFocused1 = '/data/spectro/56612/sdR-r2-00169546.fit.gz'
        self.notFocused2 = '/data/spectro/56612/sdR-r2-00169547.fit.gz'
        
        self.noLampsMsg = 'ee'*2
        self.badMasksMsg = 'ee'*2
        self.inFocusMsg = 'i'*2*4+'ii'*2
        self.outFocusMsg = 'wi'+'i'*2*3+'ii'*2
        self.badHeaderMsg = 'e'*2+'ee'
        self.noFFSMsg = 'ee'*2
        
    def tearDown(self):
        # delete plot files, if they were created.
        pass
    
    def testNotHartmann(self):
        """Test with a file that isn't a Hartmann image."""
        exp1 = get_expnum(self.notHartmann)
        self.hart.collimate(exp1,cmd=self.cmd)
        self.assertEqual(self.cmd.messages,self.badHeaderMsg)
        self.assertFalse(self.hart.success)
    
    def _lamps_tester(self,filename):
        """To help with lamp-off tests."""
        exp1 = get_expnum(filename)
        self.hart.collimate(exp1,cmd=self.cmd)
        self.assertEqual(self.cmd.messages,self.noLampsMsg)
        self.assertFalse(self.hart.success)
    def testNoNe(self):
        """Test with a file that had all Ne lamps off."""
        self._lamps_tester(self.NeOff1_file)
    def testNoNe(self):
        """Test with a file that had all HgCd lamps off."""
        self._lamps_tester(self.HgCdOff1_file)
    def testNoNe(self):
        """Test with a file that had both arc lamps off."""
        self._lamps_tester(self.bothOff1_file)
    
    def _mask_tester(self,filename):
        """To help with hartmann position testing."""
        exp1 = get_expnum(filename)
        self.hart.collimate(exp1,cmd=self.cmd)
        self.assertEqual(self.cmd.messages,self.badMasksMsg)
        self.assertFalse(self.hart.success)
    def testBothLeft(self):
        """Test with a file where both members of the pair had Left Hartmanns."""
        self._mask_tester(self.bothLeft1)
    def testBothRight(self):
        """Test with a file where both members of the pair had Right Hartmanns."""
        self._mask_tester(self.bothRight1)
    def testBothOut(self):
        """Test with a file where both members of the pair had Hartmanns out."""
        self._mask_tester(self.maskOut1)
    
    @unittest.skip('need test files!')
    def testNoFFS(self):
        """Test with a file that had all FFS open."""
        exp1 = get_expnum(self.ffsOpen_file)
        self.hart.collimate(exp1,cmd=self.cmd)
        self.assertEqual(self.cmd.messages,self.noFFSMsg)
        pass
    
    @unittest.skip('need test files!')
    def testNoLight(self):
        """Test with a file that has no signal."""
        exp1 = get_expnum(self.noLight_file)
        self.hart.collimate(exp1,cmd=self.cmd)
        self.assertEqual(self.cmd.messages,self.noLightMsg)
        pass
    
    def testHartmannOneFile(self):
        """Test collimating left expnum, the subsequent expnum is right."""
        exp1 = get_expnum(self.notFocused1)
        self.hart.collimate(exp1,cmd=self.cmd)
        self.assertEqual(self.cmd.messages,self.OutFocusMsg)
        self.assertTrue(self.hart.success)
        # TBD: get correct result from combsmallcollimate.pro
    
    def testHartmannTwoFiles(self):
        """Test collimating with files in correct order (left->right)."""
        exp1 = get_expnum(self.focused1)
        exp2 = get_expnum(self.focused2)
        self.hart.collimate(exp1,exp2,plot=True,cmd=self.cmd)
        self.assertEqual(self.cmd.messages,self.inFocusMsg)
        self.assertTrue(self.hart.success)
        # TBD: get correct result from combsmallcollimate.pro
        
    @unittest.skip('working on it!')
    def testReverseOrder(self):
        """Test collimating with files in reversed order (right->left)."""
        exp1 = get_expnum(self.focused1)
        exp2 = get_expnum(self.focused2)
        self.hart.collimate(exp2,exp1,plot=True,cmd=self.cmd) # note reversed order!
        self.assertEqual(self.cmd.messages,self.inFocusMsg)
        self.assertTrue(self.hart.success)
        # TBD: get correct result from combsmallcollimate.pro
        
if __name__ == '__main__':
    unittest.main()
