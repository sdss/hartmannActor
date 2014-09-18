"""
profile boss_collimate to find bottlenecks.
"""
import cProfile
import pstats
import time
import ConfigParser

from actorcore import TestHelper

from hartmannActor import boss_collimate, hartmannActor_main

config = ConfigParser.ConfigParser()
config.read('../etc/hartmann.cfg')
m,b = hartmannActor_main.get_collimation_constants(config)

cmd = TestHelper.Cmd(verbose=True)
hart = boss_collimate.Hartmann(None, m, b)
hart.spec = 'sp1'
hart.cmd = cmd


# NOTE: this isn't going to tell us anything, because all the work happens
# inside the 4 processes, and Profile doesn't tell us anything about that.
# Need to profile a single OneCam call if we really want to learn what's up.
prof = cProfile.Profile()
prof.runcall(hart.collimate,165006,indir='data/',cmd=cmd,moveMotors=False)
prof.dump_stats('hartmann.prof')
p = pstats.Stats('hartmann.prof')
p.strip_dirs()
p.sort_stats('time').print_stats(10)

t1 = time.time()
hart.collimate(165006, indir='data/', cmd=cmd, moveMotors=False)
t2 = time.time()
print 'time:',t2-t1
