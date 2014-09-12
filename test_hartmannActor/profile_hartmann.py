"""
profile boss_collimate to find bottlenecks.
"""
import cProfile
import pstats
import time

from sopActor.utils import boss_collimate

class Cmd(object):
    def __init__(self):
        """Save the level of any messages that pass through."""
        self.messages = ''
    def _msg(self,txt,level):
        print level,txt
        self.messages += level
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

cmd = Cmd()
hart = boss_collimate.Hartmann()
hart.spec = 'sp1'
hart.cmd = cmd

prof = cProfile.Profile()
#prof.runcall(hart.collimate,cmd,165006)#,plot=True)
prof.runcall(hart.do_one_cam,'b1','/data/spectro/*/','sdR-%s-%08d.fit*',165006,165007,False)#,plot=True)
prof.dump_stats('hartmann.prof')
p = pstats.Stats('hartmann.prof')
p.strip_dirs()
p.sort_stats('time').print_stats(10)

t1 = time.time()
hart.collimate(cmd,165190)
t2 = time.time()
print 'time:',t2-t1
