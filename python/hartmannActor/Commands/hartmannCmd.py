#!/usr/bin/env python

import logging
import os
import re
import subprocess

import opscore.protocols.keys as keys
import opscore.protocols.types as types
from opscore.utility.qstr import qstr

from hartmannActor import boss_collimate

class hartmannCmd(object):
    '''Wrap commands to the hartmann actor'''

    def __init__(self, actor):
        self.actor = actor
        #
        # Declare commands
        #
        self.keys = keys.KeysDictionary("hartmann_hartmann", (1,1),
                                        keys.Key("id", types.Int(), help="exposure number of first hartmann pair to process"),
                                        keys.Key("noCorrect", help="if set, do not apply any recommended corrections."),
                                        keys.Key("noSubframe", help="if set, take fullframe images."),
                                        )

        self.vocab = [
            ('ping', '', self.ping),
            ('status', '', self.status),
            ('doHartmann', '[noCorrect] [noSubframe]', self.doHartmann),
            ('runHartmann', '<id>', self.runHartmann),
        ]

    def ping(self, cmd):
        '''Query the actor for liveness/happiness.'''

        cmd.finish("text='Present and (probably) correct'")

    def _getIdlspec2dVersion(self):
        """ Try to return the current idlspec2d version. """

        # I don't quite trust running 'eups list' commands here.
        specDir = os.getenv('IDLSPEC2D_DIR')
        if not specDir:
            return "unknown"

        # On the other hand, this is cheezy
        m = re.search('^.*idlspec2d/([^/]+).*', specDir)
        if not m:
            return 'unparseable'

        return m.group(1)
        
    def status(self, cmd, finish=True):
        '''Report status and version; obtain and send current data'''

        self.actor.sendVersionKey(cmd)
        cmd.inform('idlspec2dVersion=%s' % (qstr(self._getIdlspec2dVersion())))
        if finish:
            cmd.finish()

    def runHartmann(self, cmd):
        """ Reduce a given pair of already taken exposures. """
        expnum1 = int(cmd.cmd.keywords['id'].values[0])
        
        cmd.diag('text="running collimate on %s/%s"' % (dir,firstId))
        hartmann = boss_collimate.Hartmann(actorState)
        hartmann.collimate(expnum1,cmd=msg.cmd)
        if hartmann.success:
            cmd.finish()
        else:
            cmd.fail('text="Collimation process failed"')
    
    def doHartmann(self, cmd):
        """
        Take and reduce a pair of hartmann exposures.
        Apply the recommended collimator moves unless noCorrect is specified.
        """
        moveMotors = "noCorrect" not in cmd.cmd.keywords
        subFrame = "noSubframe" not in cmd.cmd.keywords
        
        hartmann = boss_collimate.Hartmann()
        hartmann.doHartmann(msg.cmd,moveMotors=moveMotors,subFrame=subFrame)
        if hartmann.success:
            cmd.finish()
        else:
            cmd.fail('text="collimation process failed"')

    def old_runHartmann(self, cmd, doFinish=True):
        """ Reduce a given pair of already taken exposures. """
        exposureIds = []
             
        firstId = int(cmd.cmd.keywords['id'].values[0])
        #dir = str(cmd.cmd.keywords['dir'].values[0])
 
        cmd.diag('text="running collimate on %s/%s"' % (dir,firstId))

        ok = self._doRunHartmann(cmd, firstId)
        if ok:
            cmd.finish()
        else:
            cmd.fail('text="collimation process failed"')

    def _doRunHartmann(self, cmd, firstId, moveMotors=True):

        cmd.inform('text="running collimate on %s"' % (firstId))
        stdout, stderr = subprocess.Popen(["docollimate", str(firstId)], 
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

        for l in stderr.split('\n'):
            l = l.strip()
            if len(l) == 0:
                continue
 
            if re.search('^Installation number: ', l): continue
            if re.search('^Licensed for use by: ', l): continue
            if re.search('^IDL Version', l): continue
            if re.search('^% Compiled module: ', l): continue

            cmd.warn('text=%s' % (qstr(l)))
           
        moves = {}
        allOK = True
        for l in stdout.split('\n'):
            l = l.strip()
            if len(l) == 0:
                continue
            if re.search('^MRDFITS: ', l): 
                continue

            if l.find('WARNING') >= 0:
                cmd.warn('text=%s' % (qstr(l)))
                continue

            offsetM = re.search(r'^([rb][12])\s+(MeanOffset)\s+([^,]+),(.*)', l)
            if offsetM:
                quality = offsetM.group(4)
                key = "%s%s=%s,%s" % offsetM.groups()
                if quality != '"In focus"':
                    cmd.warn(key)
                else:
                    cmd.inform(key)
                continue
        
            redMoveM = re.search(r'^(r[12])\s+(PistonMove)\s+(.*)', l)
            if redMoveM:
                key = "%s%s=%s" % redMoveM.groups()
                cmd.inform(key)
                continue

            residM = re.search(r'^(sp[12])\s+(Residuals)\s+([^,]+),\s*([^,]+),\s*(.*)', l)
            if residM:
                OK = (residM.group(5) == '"OK"')
                allOK = allOK and OK
                key = "%s%s=%s,%s,%s" % residM.groups()
                if OK:
                    cmd.inform(key)
                else:
                    cmd.warn(key)
                continue

            blueMoveM = re.search(r'^(b[12])\s+(RingMove)\s+(.*)', l)
            if blueMoveM:
                key = "%s%s=%s" % blueMoveM.groups()
                cmd.respond(key)
                continue

            avgMoveM = re.search(r'^(sp[12])\s+(AverageMove)\s+(.*)', l)
            if avgMoveM:
                specName = avgMoveM.group(1)
                pistonStr = avgMoveM.group(3)
                key = "%s%s=%s" % avgMoveM.groups()
                cmd.inform(key)
                try:
                    piston = int(pistonStr)
                    moves[specName] = piston
                except:
                    cmd.warn('text=%s' % (qstr("failed to parse piston value in %s" % (pistonStr))))
                    piston = 0

                if moveMotors:
                    if not piston:
                        cmd.respond('text="no recommended piston change for %s"' % (specName))
                        continue
                        
                    ret = self.actor.cmdr.call(actor='boss', forUserCmd=cmd,
                                               cmdStr="moveColl spec=%s piston=%s" % (specName, piston),
                                               timeLim=30.0)
                    if ret.didFail:
                        return False
                else:
                    cmd.warn('text="NOT applying: boss moveColl spec=%s piston=%s"' % (specName, piston))
                continue

            cmd.warn('text=%s' % (qstr("not yet handling :%s:" % (l))))

        return 'sp1' in moves and 'sp2' in moves and allOK
    

    def old_doHartmann(self, cmd):
        '''Take and reduce a pair of hartmann exposures. Usually apply the recommended collimator moves. '''

        exposureIds = []
        moveMotors = "noCorrect" not in cmd.cmd.keywords
        subFrame = "noSubframe" not in cmd.cmd.keywords
        
        for side in 'left','right':
            window = "window=850,1400" if subFrame else ""
            ret = self.actor.cmdr.call(actor='boss', forUserCmd=cmd,
                                       cmdStr='exposure arc hartmann=%s itime=4 %s %s' % \
                                           (side,
                                            window,
                                            ("noflush" if side == "right" else "")),
                                       timeLim=90.0)
            exposureId = self.actor.models["boss"].keyVarDict["exposureId"][0]
            exposureId += 1
            exposureIds.append(exposureId)
            cmd.diag('text="got hartmann %s exposure %d"' % (side, exposureId))
                     
            if ret.didFail:
                cmd.fail('text="failed to take %s hartmann exposure"' % (side))
                return

        ok = self._doRunHartmann(cmd, exposureIds[0], moveMotors=moveMotors)
        if ok:
            cmd.finish()
        else:
            cmd.fail('text="collimation process failed"')

