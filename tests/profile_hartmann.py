"""
profile boss_collimate to find bottlenecks.
"""

import configparser
import cProfile
import pstats
import time

from actorcore import TestHelper

from hartmannActor import boss_collimate, hartmannActor_main


config = configparser.ConfigParser()
config.read("../etc/hartmann.cfg")
m, b, constants, coeff = hartmannActor_main.get_collimation_constants(config)

cmd = TestHelper.Cmd(verbose=True)
hart = boss_collimate.Hartmann(None, m, b, constants, coeff)
hart.spec = "sp1"
hart.cmd = cmd

# NOTE: this isn't going to tell us anything, because all the work happens
# inside the 4 processes, and Profile doesn't tell us anything about that.
# Need to profile a single OneCam call if we really want to learn what's up.
# print 'Profiling full hartmann __call__()'
# print '----------------------------------'
# prof = cProfile.Profile()
# prof.runcall(hart.collimate,165006,indir='data/',cmd=cmd,moveMotors=False)
# prof.dump_stats('hartmann.prof')
# p = pstats.Stats('hartmann.prof')
# p.strip_dirs()
# p.sort_stats('time').print_stats(10)

print("Profiling single oneCam __call__()")
print("----------------------------------")
# Now profile a single OneCam call, to see what happens in the guts of it.
prof = cProfile.Profile()
oneCam = boss_collimate.OneCam(
    m,
    b,
    constants["bsteps"],
    constants["focustol"],
    coeff,
    183069,
    183069,
    "/data/spectro/56896",
)
prof.runcall(oneCam, "r2")
prof.dump_stats("oneCam.prof")
p = pstats.Stats("oneCam.prof")
p.strip_dirs()
p.sort_stats("time").print_stats(10)

t1 = time.time()
hart.collimate(183069, mjd=56896, cmd=cmd)
t2 = time.time()
print("time:", t2 - t1)
