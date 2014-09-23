"""
Computes spectrograph collimation focus from Hartmann mask exposures.

Replacement for idlspec2d combsmallcollimate+sosActor.
SOP shouldn't have a dependency on SoS, so the code for the short Hartmanns
is here now.

Example:
    # cmd is the current Command instance, for message passing.
    # take Hartmann exposures and output collimation values:
    hartmann = Hartmann()
    hartmann.doHartmann(cmd)
    # solve for the focus of exposure numbers 12345,12346 on the current MJD
    hartmann.collimate(cmd,12345)

The focus of the collimator is measured by comparing two Hartmann
exposures of arc lamps, and looking for shifts in the arc line
positions. A linear correlation coefficient is computed independently
in a subregion on each CCD as a function of pixel shifts of the 2nd
image in both X and Y.  The best-focus value is found in each region
by maximizing the linear correlation in the Y (wavelength) direction.

The position of the Hartmann shutters is read from the OBSCOMM (for
SDSS-I: '{focus, hartmann l}' or '{focus, hartmann l}') or HARTMANN
(for BOSS: 'Left' or 'Right') header keywords for SDSS-I.  It is
expected to be '{focus, hartmann l}' for one exposure and '{focus,
hartmann r}' for the other (in either order). It is assumed that the
collimator position is identical for both exposures.

The sense of the pixel shifts reported is what one would have to shift
the Hartmann-r exposure by in Y to agree with the Hartmann-l exposure.
"""
# IDL version by Kyle Dawson, David Schlegel, Matt Olmstead
# IDL->Python verson by John Parejko

import os.path
from multiprocessing import Pool

try:
    fitsio = True
    import fitsio
except ImportError:
    print "WARNING: fitsio not available. Using pyfits instead."
    print "If you install the python fitsio package, the code will run in about half the time."
    import pyfits
    fitsio = False
import numpy as np
from scipy.ndimage import interpolation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import hartmannActor.myGlobals as myGlobals

class HartError(Exception):
    """For known errors processing the Hartmanns"""
    pass
#...

def update_status(cmd, status):
    """update the global status value, and output the status keyword."""
    myGlobals.hartmannStatus = status
    cmd.inform('status=%s'%status)

class OneCamResult(object):
    """
    Store the results of a oneCam call().
    Makes multiprocessing much easier.
    """
    def __init__(self, cam, success, xshift, coeff, ibest, xoffset, piston):
        self.cam = cam
        self.success = success
        self.xshift = xshift
        self.coeff = coeff
        self.ibest = ibest
        self.xoffset = xoffset
        self.piston = piston

    def __str__(self):
        return '%s:%s : %s, %s'%(self.cam, self.success, self.xoffset, self.piston)

class OneCam(object):
    """Collimate one camera."""
    def __init__(self, cmd, m, b, bsteps, coeff,
                 expnum1, expnum2, indir, test=False):
        self.cmd = cmd
        self.test = test
        
        self.indir = indir
        self.expnum1 = expnum1
        self.expnum2 = expnum2

        # A pattern for the filenames that we can format for the full name.
        self.basename = 'sdR-%s-%08d.fit.gz'

        # allowable focus tolerance (pixels): if offset is less than this, we're in focus.
        self.focustol = 0.20
        
        # maximum pixel shift to search in X
        self.maxshift = 2
        
        # collimator motion constants for the different regions.
        self.m = m #{'b1':1.,'b2':1.,'r1':1.,'r2':1.}
        self.b = b #{'b1':0.129,'b2':0.00,'r1':-0.229,'r2':0.068}

        # steps per degree for the blue ring.
        self.bsteps = bsteps
        # "funny fudge factors" from Kyle Dawson
        # These values were intially determined by comparing to the original SDSS spectrographs
        # They need to be adjusted when, e.g., the spectrograph motors are changed.
        # pixscale = -15. vs. pixscale/24. is because of the change from SDSS to BOSS
        pixscale = -15. # in microns
        self.fudge = {'b1':coeff['b1']*self.bsteps*pixscale,
                      'b2':coeff['b2']*self.bsteps*pixscale,
                      'r1':coeff['r1']*pixscale,
                      'r2':coeff['r2']*pixscale}

        # region to use in the analysis. [xlow,xhigh,ylow,yhigh]
        # NOTE: this region is chosen to have no blending and strong lines.
        # Even though there are only two lines in the blue, there should be enough signal
        # in one line to get a good cross-correlation.
        # Also, the other blue lines have a higher temperature dependence, so
        # we don't want to use them, as the arc lamp might not be warm yet.
        self.region = np.s_[850:1301,1500:2501]
        
        self.bias_slice = [np.s_[950:1338,10:100],np.s_[950:1338,4250:4340]]
        self.cam_gains = {'b1':[1.048, 1.048, 1.018, 1.006], 'b2':[1.040, 0.994, 1.002, 1.010],
                          'r1':[1.966, 1.566, 1.542, 1.546], 'r2':[1.598, 1.656, 1.582, 1.594]}
        self.gain_slice = {'b':[[np.s_[0:2055,0:2047],np.s_[56:2111,128:2175]],
                                [np.s_[0:2055,2048:4095],np.s_[56:2111,2176:4223]]],
                           'r':[[np.s_[0:2063,0:2056],np.s_[48:2111,119:2175]],
                                [np.s_[0:2063,2057:4113],np.s_[48:2111,2176:4232]]],}
        
        # Did everything work?
        self.success = True
        # to store the results of the calculations.
        self.xshift = None
        self.ibest = None
        self.xoffset = None
        self.piston = None
    #...
    
    def __call__(self, cam):
        """
        Compute the collimation values for one camera.
        
        See parameters for self.collimate().
        """
        if cam not in ['r1','r2','b1','b2']:
            raise HartError("I do not recognize camera %s"%self.cam)
        self.cam = cam
        self.spec = 'sp'+cam[1]

        try:
            self._load_data(self.indir,self.expnum1,self.expnum2)
            self._do_gain_bias()
            self._check_images()
            self._find_shift()
            self._find_collimator_motion()
        # Have to handle exceptions here, because we're called via multiprocess.
        except HartError as e:
            self.cmd.error('text="%s"'%e)
            self.success = False
        except Exception as e:
            self.cmd.error('text="!!!! Unknown error when processing Hartmanns! !!!!"')
            self.cmd.error('text="%s"'%e)
            self.success = False
        return OneCamResult(cam, self.success, self.xshift, self.coeff, self.ibest, self.xoffset, self.piston)
    
    def check_Hartmann_header(self,header):
        """
        Return whether this is a left, right or unknown Hartmann.
        """
        # OBSCOMM only exists in dithered flats taken with "specFlats", so
        # we have to "get" it (returns None if missing), not just take it as a keyword.
        obscomm = header.get('OBSCOMM')
        hartmann = header.get('HARTMANN')
        # Need strip() incase extra whitespace is stuck on the end.
        if obscomm == '{focus, hartmann l}' or hartmann.strip() == 'Left':
            return 'left'
        elif obscomm == '{focus, hartmann r}' or hartmann.strip() == 'Right':
            return 'right'
        else:
            return None
    #...
    
    def bad_header(self,header):
        """
        Return True if the header indicates there are no lamps on or no flat-field
        petals closed.
        If the wrong number of petals are closed, then emit a warning and return False.
        """
        sum_string = lambda field: sum([int(x) for x in field.split()])
        
        isBad = False
        ffs = header.get('FFS',None)
        # 8 flat field screens: 0 for open, 1 for closed
        if ffs:
            ffs_sum = sum_string(ffs)
            if ffs_sum < 8:
                self.cmd.warn("text='Only %d of 8 flat-field petals closed: %s'"%(ffs_sum,ffs))
            if ffs_sum == 0:
                isBad = True
        else:
            self.cmd.warn("text='FFS not in FITS header!'")
            isBad = True
        
        Ne = header.get('NE',None)
        HgCd = header.get('HGCD',None)
        # 4 of each lamp: 0 for off, 1 for on
        if Ne is not None and HgCd is not None:
            Ne_sum = sum_string(Ne)
            HgCd_sum = sum_string(HgCd)
            if Ne_sum < 4:
                self.cmd.warn("text='Only %d of 4 Ne lamps turned on: %s'"%(Ne_sum,Ne))
            if HgCd_sum < 4:
                self.cmd.warn("text='Only %d of 4 HgCd lamps turned on: %s'"%(HgCd_sum,HgCd))
            if Ne_sum == 0 or HgCd_sum == 0:
                isBad = True
        else:
            self.cmd.warn("text='NE and/or HgCd not in FITS header.'")
            isBad = True
        
        return isBad
    
    def _load_data(self,indir,expnum1,expnum2):
        """
        Read in the two images, and check that headers are reasonable.
        Sets self.bigimg[1,2] and returns True if everything is ok, else return False."""
        filename1 = os.path.join(indir,self.basename%(self.cam,expnum1))
        filename2 = os.path.join(indir,self.basename%(self.cam,expnum2))
        if not os.path.exists(filename1) and not os.path.exists(filename2):
            raise HartError("All files not found: %s, %s!"%(filename1,filename2))
        
        # NOTE: we don't process with sdssproc, because the subarrays cause it to fail.
        # Also, because it would restore the dependency on SoS that this class removed!
        try:
            if fitsio:
                header1 = fitsio.read_header(filename1,0)
            else:
                header1 = pyfits.getheader(filename1,0)
        except IOError:
            raise HartError("Failure reading file %s"%filename1)
        try:
            if fitsio:
                header2 = fitsio.read_header(filename2,0)
            else:
                header2 = pyfits.getheader(filename2,0)
        except IOError:
            raise HartError("Failure reading file %s"%filename2)

        if self.bad_header(header1) or self.bad_header(header2):
            raise HartError("Incorrect header values in fits file.")
       
        self.hartpos1 = self.check_Hartmann_header(header1)
        self.hartpos2 = self.check_Hartmann_header(header2)
        if self.hartpos1 is None or self.hartpos2 is None:
            raise HartError("FITS headers do not indicate these are Hartmann exposures.")
        if self.hartpos1 == self.hartpos2:
            raise HartError("FITS headers indicate both exposures had same Hartmann position: %s"%self.hartpos1)

        # upcast the arrays, to make later math work better.
        if fitsio:
            self.bigimg1 = np.array(fitsio.read(filename1,0),dtype='float64')
            self.bigimg2 = np.array(fitsio.read(filename2,0),dtype='float64')
        else:
            self.bigimg1 = np.array(pyfits.getdata(filename1,0),dtype='float64')
            self.bigimg2 = np.array(pyfits.getdata(filename2,0),dtype='float64')
        self.header1 = header1
        self.header2 = header2
    #...

    def _do_gain_bias(self):
        """Apply the bias and gain to the images."""
        bigimg1 = self.bigimg1
        bigimg2 = self.bigimg2
        # determine bias levels
        bias1 = [ np.median(bigimg1[self.bias_slice[0]]), np.median(bigimg1[self.bias_slice[1]]) ]
        bias2 = [ np.median(bigimg2[self.bias_slice[0]]), np.median(bigimg2[self.bias_slice[1]]) ]
        # apply bias and gain to the images
        # gain_slice is a dict with keys 'r' and 'b
        gain = self.cam_gains[self.cam]
        gslice = self.gain_slice[self.cam[0]]

        # Only apply gain to quadrants 0 and 1, since we aren't using quadrants 2 and 3.
        # NOTE: we are overwriting the original array, including the original bias region.
        # This is ok, because all the processing is done on a subregion of this,
        # indexed from the new edge.
        bigimg1[gslice[0][0]] = gain[0]*(bigimg1[gslice[0][1]]-bias1[0])
        bigimg1[gslice[1][0]] = gain[1]*(bigimg1[gslice[1][1]]-bias1[1])
        bigimg2[gslice[0][0]] = gain[0]*(bigimg2[gslice[0][1]]-bias2[0])
        bigimg2[gslice[1][0]] = gain[1]*(bigimg2[gslice[1][1]]-bias2[1])
    #...

    def _check_images(self):
        """Check that there is actually light in the images."""
        img1 = self.bigimg1[self.region]
        # find the variance near bright lines
        # ddof=1 for consistency with IDL's variance() which has denominator (N-1)

        # NOTE: TBD: need to compare this with any new choices for subFrame.
        if 'b' in self.cam:
            var = np.var(img1[300:450,:],ddof=1)
        else:
            var = np.var(img1[0:150,:],ddof=1)
       # check that the camera is capturing light by requiring variance greater than 100
        if var < 100:
            raise HartError("THERE DOES NOT APPEAR TO BE ANY LIGHT FROM THE ARCS IN %s!!!"%self.cam)
    #...

    def _find_shift(self,order=3):
        """
        Find the best shift between image1 and image2.
        Expects _load_data() to have been run first to initialize things.
        order is the order of the spline used for shifting in the correlation step.
        """
        # Mask pixels around the edges of the image.
        # We don't have inverse-variances because sdssproc isn't run, so we can't do
        # smarter masking, like bad pixel smoothing, cosmic rays, etc.
        # It is important to mask out the ends of the array, because of
        # spline-induced oddities there.
        subimg1 = self.bigimg1[self.region].copy()
        subimg2 = self.bigimg2[self.region].copy()
        mask = np.ones(subimg1.shape,dtype='f8')
        mask[:10,:] = 0
        mask[-10:,:] = 0
        mask[:,:10] = 0
        mask[:,-10:] = 0

        # Compute linear correlation coefficients
        # Calculate the maximum product of the two images when shifting by steps of dx.
        dx = 0.05
        nshift = int(np.ceil(2*self.maxshift/dx))
        xshift = -self.maxshift + dx * np.arange(nshift,dtype='f8')
        self.xshift = xshift # save for plotting
        
        def calc_shift(xs,img1,img2,mask):
            shifted = interpolation.shift(img2,[xs,0],order=order,prefilter=False)
            return (img1*shifted*mask).sum()
        
        self.coeff = np.zeros(nshift,dtype='f8')
        filtered1 = interpolation.spline_filter(subimg1)
        filtered2 = interpolation.spline_filter(subimg2)
        for i in range(nshift):
            #self.coeff[i] = (subimg1*interpolation.shift(subimg2,[xshift[i],0],order=order)*mask).sum()
            #self.coeff[i] = (filtered1*interpolation.shift(filtered2,[xshift[i],0],order=order,prefilter=False)*mask).sum()
            self.coeff[i] = calc_shift(xshift[i],filtered1,filtered2,mask)
        ibest = self.coeff.argmax()
        self.ibest = ibest # save for plotting
        self.xoffset = xshift[ibest]
        # If the sequence is actually R-L, instead of L-R,
        # then the offset acctually goes the other way.
        if self.hartpos1 == 'right':
            self.xoffset = -self.xoffset
    #...

    def _find_collimator_motion(self):
        """
        Compute the required collimator movement from self.xoffset.
        Assumes _find_shift has been run successfully.

        Current procedure for determining the offsets:
            When the observers start complaining about focus warnings...
            * We have them step through focus between -10000 and 10000,
              taking a full and quick hartmann +flat and arc at each step.
            * Then we have enough information to recalibrate the relationship
              between the full and quick hartmanns.
        This has to happen once every three months or so.
        """
        m = self.m[self.cam]
        b = self.b[self.cam]
        if self.test:
            b = 0.
        offset = self.xoffset*m + b

        if offset < self.focustol:
            focus = 'In Focus'
            msglvl = self.cmd.inform
        else:
            focus = 'Out of focus'
            msglvl = self.cmd.warn
        msglvl('%sMeanOffset=%.2f,"%s"'%(self.cam,offset,focus))

        piston = int(offset*self.fudge[self.cam])
        if 'r' in self.cam:
            self.cmd.inform('%sPistonMove=%d'%(self.cam,piston))
        else:
            self.cmd.inform('%sRingMove=%.1f'%(self.cam,-piston/self.bsteps))
        self.piston = piston
    #...

#...

class Hartmann(object):
    """
    Call Hartmann.doHartmann to take and reduce a pair of hartmann exposures.
    """
    def __init__(self, actor, m, b, constants, coeff):
        """
        Actor can be None, if you don't need to send an actual commands.
        Need m and b, the slope and intercept of the collimator motor relation.
        constants is a dictionary with various parameters for OneCam.
        coeff is a cam dictionary of the "fudge factors" for OneCam.
        """

        self.actor = actor
        # so we can use it at the commandline, outside STUI/tron.
        self.models = actor.models if actor is not None else None
            
        self.cmd = None
        self.mjd = 00000

        self.m = m
        self.b = b
        # steps per degree for the blue ring.
        self.bsteps = constants['bsteps']
        # tolerance for bad residual on blue ring
        self.badres = constants['badres']

        self.coeff = coeff
        
        # the sub-frame region on the chip to read out when doing quick-hartmanns.
        self.subFrame = [850,1400]

        self.data_root_dir = '/data/spectro'
        self.plotfilebase = 'Collimate-%05d_%08d-%08d.png'

        self.reinit()
    #...
    
    def reinit(self):
        # final results go here
        self.result = {'sp1':{'b':0.,'r':0.},'sp2':{'b':0.,'r':0.}}
        self.full_result = {'sp1':{'b':None,'r':None},'sp2':{'b':None,'r':None}}
        self.success = True
        # Can't use update_status here, as we don't necessarily have a cmd available.
        myGlobals.hartmannStatus = 'initialized'

    def __call__(self, cmd, moveMotors=False, subFrame=True, plot=False):
        """
        Take and reduce a pair of hartmann exposures.
        Usually apply the recommended collimator moves.
        
        cmd is the currently active Commander instance, for passing info/warn messages.
        if moveMotors is set, apply the computed corrections.
        if subFrame is set, only readout a part of the chip.
        if plot is set, make a plot representing the calculation.
        """
        self.cmd = cmd

        try:
            # take the hartmann frames.
            exposureId = self.take_hartmanns(subFrame)
            # Perform the collimation calculations
            self.collimate(exposureId[0],exposureId[1],moveMotors=moveMotors,plot=plot)
            if self.success and moveMotors:
                update_status(self.cmd, 'moving')
                for spec,piston in self.result.items():
                    self.move_motors(spec,piston)
        except HartError as e:
            self.cmd.error('text="%s"'%e)
            self.success = False
        except Exception as e:
            self.cmd.error('text="Unhandled Exception when processing Hartmanns!"')
            self.cmd.error('text="%s"'%e)
            self.success = False

        update_status(self.cmd, 'idle')
    #...

    def _bundle_result(self, cams, results):
        """Return dict of spec:{cam:piston}."""
        for cam, result in zip(cams, results):
            self.full_result['sp'+cam[1]][cam[0]] = result
            self.result['sp'+cam[1]][cam[0]] = result.piston

    def _collimate(self, expnum1, expnum2, indir, moveMotors, docams):
        """The guts of the collimation, to be wrapped in a try:except block."""
        # pool = ThreadPool(len(docams))
        pool = Pool(len(docams))
        oneCam = OneCam(self.cmd, self.m, self.b, self.bsteps, self.coeff,
                        expnum1, expnum2, indir, moveMotors)
        results = pool.map(oneCam, docams)
        pool.close()
        pool.join()

        success = dict([(x.cam,x.success) for x in results])
        if not all(success.values()):
            failures = [x for x in success if not success[x]]
            raise HartError('Collimation calculation failed for %s.'%','.join(failures))

        self._bundle_result(docams, results)

    def collimate(self, expnum1, expnum2=None, indir=None, mjd=None,
                  specs=['sp1','sp2'],docams1=['b1','r1'],docams2=['b2','r2'],
                  test=False, plot=False, cmd=None, moveMotors=False):
        """
        Compute the spectrograph collimation focus from Hartmann mask exposures.
        
        expnum1: first exposure number of raw sdR file (integer).
        expnum2: second exposure number (default: expnum1+1)
        indir:   directory where the exposures are located.
        mjd:     MJD of exposures in /data directory.
        spec:    spectrograph(s) to collimate ('sp1','sp2',['sp1','sp2'])
        docams1: camera(s) in sp1 to collimate ('b1','r1',['b1','r1'])
        docams2: camera(s) in sp2 to collimate ('b2','r2',['b2','r2'])
        test:    If True, we are trying to determine the collimation parameters, so ignore 'b' parameter.
        plot:    If True, save a plot of the best fit collimation.
        cmd:     command handler
        moveMotors: If True, actually apply the calculated specMech moves.
        """

        self.test = test
        if cmd is not None:
            self.cmd = cmd
        if expnum2 is None:
            expnum2 = expnum1+1

        if mjd is not None:
            self.mjd = mjd
        if indir is None:
            indir = os.path.join(self.data_root_dir,str(self.mjd))

        update_status(self.cmd, 'processing')

        # # to handle the various string/list/tuple possibilities for each argument
        # docams = []
        # if spec == 'sp1':
        #     docams.extend([docams1,] if isinstance(docams1,str) else docams1)
        # elif spec == 'sp2':
        #     docams.extend([docams2,] if isinstance(docams2,str) else docams2)
        # else:
        #     self.success = False
        #     self.cmd.error('text="I do not understand spectrograph: %s"'%spec)
        #     return

        docams = ['r1','r2','b1','b2']
        try:
            self._collimate(expnum1, expnum2, indir, moveMotors, docams)
        except Exception as e:
            self.success = False
            self.cmd.error('text="Collimation calculation failed! %s"'%e)
            return
        else:
            for spec in specs:
                self._mean_moves(spec)
            if plot:
               self.make_plot(expnum1,expnum2)
    #...
    
    def take_hartmanns(self,subFrame):
        """
        Take a pair of hartmann exposures, in self.subFrame if requested.
        Returns the exposure IDs of the two exposures.
        """

        update_status(self.cmd, 'exposing')

        exposureIds = []
        timeLim = 90.0
        for side in 'left','right':
            window = "window={0},{1}".format(*self.subFrame) if subFrame else ""
            cmdStr = 'exposure arc hartmann=%s itime=4 %s %s'%(side,window,("noflush" if side == "right" else ""))
            ret = self.actor.cmdr.call(actor='boss',forUserCmd=self.cmd,
                                       cmdStr=cmdStr,timeLim=timeLim)
            if ret.didFail:
                raise HartError('Failed to take %s hartmann exposure"' % (side))
            exposureId = self.models["boss"].keyVarDict["exposureId"][0]
            # ????
            # TBD: why was there an exposureId+1 here???
            # ????
            # exposureId += 1
            exposureIds.append(exposureId)
            self.mjd = int(self.models["boss"].keyVarDict["BeginExposure"][1])
            self.cmd.inform('text="got hartmann %s exposure %d"' % (side, exposureId))
        return exposureIds

    def _mean_moves(self, spec):
        """Compute the mean movement and residuals for this spectrograph,
        after r&b moves have been determined."""

        avg = sum(self.result[spec].values())/2.
        bres = -(self.result[spec]['b'] - avg)/self.bsteps
        rres = self.result[spec]['r'] - avg

        if abs(bres) < self.badres:
            resid = '"OK"'
            msglvl = self.cmd.inform
        else:
            resid = '"Bad angle: move blue ring %.1f degrees then rerun gotoField with Hartmanns checked."'%(bres*2)
            msglvl = self.cmd.warn
            self.success = False
        msglvl('%sResiduals=%d,%.1f,%s'%(spec,rres,bres,resid))
        self.cmd.inform('%sAverageMove=%d'%(spec,avg))

    def move_motors(self, spec, piston):
        """Apply a collimator piston move to spectrograph spec."""
        if piston == 0:
            self.cmd.respond('text="no recommended piston change for %s"' % (spec))
        timeLim = 30.0
        cmdVar = self.actor.cmdr.call(actor='boss', forUserCmd=self.cmd,
                                      cmdStr="moveColl spec=%s piston=%s" % (spec, piston),
                                      timeLim=timeLim)
        if cmdVar.didFail:
            raise HartError('Failed to move collimator pistons.')

    def _get_inset_range(result, ibest, xshift):
        """Get the xrange of the inset plot."""
        inset_xlim = 14
        inset = [ibest-inset_xlim,ibest+inset_xlim]
        # prevent array overflow when getting the inset plot range.
        if ibest < inset_xlim:
            inset[0] = 0
        if len(xshift)-ibest < inset_xlim:
            inset[1] = len(xshift)-1
        return inset

    def _plot_one(self, ax1, ax2, spec):
        """Plot collimation curves for one spectrograph"""
        ylim1 = [0.4,1.05]
        ylim2 = [0.92,1.01]

        result = self.full_result[spec]
        for cam in result:
            inset = self._get_inset_range(result[cam].ibest, result[cam].xshift)
            ax1.plot(result[cam].xshift,result[cam].coeff/max(result[cam].coeff),'*-',color=cam,lw=1.5)
            ax2.plot(result[cam].xshift[inset[0]:inset[1]],result[cam].coeff[inset[0]:inset[1]]/max(result[cam].coeff),'*-',color=cam,lw=1.5)
            ax1.plot([result[cam].xoffset,result[cam].xoffset],ylim1,'--',color=cam)
            ax2.plot([result[cam].xoffset,result[cam].xoffset],ylim2,'--',color=cam)
            plt.yticks(np.arange(0.90,1.01,.05))
        ax1.set_ylim(ylim1[0],ylim1[1])
        ax2.axis([result[cam].xshift[inset[0]],result[cam].xshift[inset[1]],ylim2[0],ylim2[1]])
        ax1.set_xlabel('pixels')
        ax1.set_ylabel('cross-correlation')


    def make_plot(self, expnum1, expnum2):
        """Save a plot of the pixel vs. correlation for this collimation."""
        plotfile = self.plotfilebase%(self.mjd, expnum1, expnum2)
        fig = plt.figure()
        title = 'Collimate: MJD=%5i Exp=%08i-%08i'%(self.mjd, expnum1, expnum2)
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
        ax2 = fig.add_axes([0.35,0.2,0.3,0.3])

        for spec in ['sp1','sp2']:
            self._plot_one(ax1,ax2,spec)
            ax1.set_title(title)

        plt.savefig(plotfile,bbox_inches='tight')
#...
