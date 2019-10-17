#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Filename: boss_collimate.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

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


from __future__ import absolute_import, division, print_function

import os.path
import time
from multiprocessing import Pool

import numpy as np
from scipy.ndimage import interpolation

import hartmannActor.myGlobals as myGlobals
from opscore.utility.qstr import qstr
from sdss.utilities import astrodatetime


import matplotlib  # isort:skip
matplotlib.use('Agg')  # isort:skip
import matplotlib.pyplot as plt  # noqa isort:skip

try:
    fitsio = True
    import fitsio
except ImportError:
    print('WARNING: fitsio not available. Using pyfits instead.')
    print('If you install the python fitsio package, the code will run in about half the time.')
    import pyfits
    fitsio = False


class HartError(Exception):
    """For known errors processing the Hartmanns"""
    pass


def update_status(cmd, status):
    """update the global status value, and output the status keyword."""
    myGlobals.hartmannStatus = status
    cmd.inform('status=%s' % qstr(status))


def get_filename(indir, cam, expnum):
    """Return a full path to the the desired exposure."""
    basename = 'sdR-%s-%08d.fit.gz'
    return os.path.join(indir, basename % (cam, expnum))


class OneCamResult(object):
    """
    Store the results of a oneCam call().
    Makes multiprocessing much easier.
    """

    def __init__(self, cam, success, xshift, coeff, ibest, xoffset, piston, focused, messages):
        self.cam = cam
        self.success = success
        self.xshift = xshift
        self.coeff = coeff
        self.ibest = ibest
        self.xoffset = xoffset
        self.piston = piston
        self.messages = messages
        self.focused = focused

    def __str__(self):
        return '%s:%s : %s, %s' % (self.cam, self.success, self.xoffset, self.piston)


class OneCam(object):
    """Collimate one camera."""

    def __init__(self, m, b, bsteps, focustol, coeff, expnum1, expnum2, indir,
                 test=False, noCheckImage=False, bypass=[]):
        """
            Kwargs:
            noCheckImage (bool): skip the variance calculation check for whether
                                 there is light in the camera (useful for sparse pluggings).
            bypass (list): bypasses to apply.
        """

        self.test = test

        self.indir = indir
        self.expnum1 = expnum1
        self.expnum2 = expnum2
        self.noCheckImage = noCheckImage
        self.bypass = bypass

        # allowable focus tolerance (pixels): if offset is less than this, we're in focus.
        self.focustol = focustol

        # maximum pixel shift to search in X
        self.maxshift = 2

        # collimator motion constants for the different regions.
        self.m = m  # {'b1':1.,'b2':1.,'r1':1.,'r2':1.}
        self.b = b  # {'b1':0.129,'b2':0.00,'r1':-0.229,'r2':0.068}

        # steps per degree for the blue ring.
        self.bsteps = bsteps
        # "funny fudge factors" from Kyle Dawson
        # These values were intially determined by comparing to the original SDSS spectrographs
        # They need to be adjusted when, e.g., the spectrograph motors are changed.
        # pixscale = 15. vs. pixscale/24. is because of the change from SDSS to BOSS
        pixscale = 15.  # in microns
        self.fudge = {
            'b1': coeff['b1'] * pixscale,
            'b2': coeff['b2'] * pixscale,
            'r1': coeff['r1'] * pixscale,
            'r2': coeff['r2'] * pixscale
        }

        # region to use in the analysis. [xlow,xhigh,ylow,yhigh]
        # NOTE: this region is chosen to have no blending and strong lines.
        # Even though there are only two lines in the blue, there should be enough signal
        # in one line to get a good cross-correlation.
        # Also, the other blue lines have a higher temperature dependence, so
        # we don't want to use them, as the arc lamp might not be warm yet.
        self.region = np.s_[850:1301, 1500:2501]

        self.bias_slice = [np.s_[950:1339, 10:101], np.s_[950:1339, 4250:4341]]
        self.cam_gains = {
            'b1': [1.048, 1.048, 1.018, 1.006],
            'b2': [1.040, 0.994, 1.002, 1.010],
            'r1': [1.966, 1.566, 1.542, 1.546],
            'r2': [1.598, 1.656, 1.582, 1.594]
        }
        self.gain_slice = {
            'b': [[np.s_[0:2056, 0:2048], np.s_[56:2112, 128:2176]],
                  [np.s_[0:2056, 2048:4096], np.s_[56:2112, 2176:4224]]],
            'r': [[np.s_[0:2064, 0:2057], np.s_[48:2112, 119:2176]],
                  [np.s_[0:2064, 2057:4114], np.s_[48:2112, 2176:4233]]],
        }

        # Did everything work?
        self.success = True
        # to store the results of the calculations.
        self.coeff = None
        self.xshift = None
        self.ibest = None
        self.xoffset = None
        self.piston = None
        self.focused = False

        # will contain tuples of msglevel (i,w,e) and the associated message.
        self.messages = []

    def __call__(self, cam):
        """Compute the collimation values for one camera.

        Parameters
        ----------
        cam : str
            The camera to perform the calculation on (r1, r2, b1, b2)

        """

        if cam not in ['r1', 'r2', 'b1', 'b2']:
            self.add_msg('e', 'text="I do not recognize camera %s"' % cam)
            self.success = False
            return None

        self.cam = cam

        self.spec = 'sp' + cam[1]

        try:

            self._load_data(self.indir, self.expnum1, self.expnum2)
            self._do_gain_bias()

            if not self.noCheckImage:
                self._check_images()

            self._find_shift()
            self._find_collimator_motion()

        # Have to handle exceptions here, because we're called via multiprocess.
        except HartError as e:

            self.add_msg('e', 'text="%s had error: %s"' % (self.cam, e))
            self.success = False

        except Exception as e:

            self.add_msg('e', 'text="!!!! Unknown error when processing Hartmanns! !!!!"')
            self.add_msg('e', 'text="%s reported %s: %s"' % (self.cam, type(e).__name__, e))
            self.success = False

        return OneCamResult(cam, self.success, self.xshift, self.coeff,
                            self.ibest, self.xoffset, self.piston, self.focused,
                            self.messages)

    def add_msg(self, level, message):
        """Add a message to the message list to be returned."""
        self.messages.append((level, message))

    def check_Hartmann_header(self, header):
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

    def bad_header(self, header):
        """
        Return True if the header indicates there are no lamps on or no flat-field
        petals closed.
        If the wrong number of petals are closed, then emit a warning and return False.
        """

        sum_string = lambda field: sum([int(x) for x in field.split()])  # noqa

        isBad = False
        ffs = header.get('FFS', None)
        # 8 flat field screens: 0 for open, 1 for closed
        if ffs:
            try:
                ffs_sum = sum_string(ffs)
                if ffs_sum < 8:
                    self.add_msg(
                        'w', 'text="%s: Only %d of 8 flat-field petals closed: %s"' % (self.cam,
                                                                                    ffs_sum, ffs))
                if ffs_sum == 0:
                    isBad = True
            except:
                self.add_msg('w', 'text="{}: failed reading FFS info"'.format(self.cam))
                isBad = True
        else:
            self.add_msg('w', "text='%s: FFS not in FITS header!'" % self.cam)
            isBad = True

        if 'ffs' in self.bypass and isBad:
            self.add_msg('w', 'text="FFS check failed but FFS are bypassed."')
            isBad = False

        Ne = header.get('NE', None)
        HgCd = header.get('HGCD', None)
        # 4 of each lamp: 0 for off, 1 for on
        if Ne is not None and HgCd is not None:
            Ne_sum = sum_string(Ne)
            HgCd_sum = sum_string(HgCd)
            if Ne_sum < 4:
                self.add_msg(
                    'w', "text='%s: Only %d of 4 Ne lamps turned on: %s'" % (self.cam, Ne_sum, Ne))
            if HgCd_sum < 4:
                self.add_msg(
                    'w', "text='%s: Only %d of 4 HgCd lamps turned on: %s'" % (self.cam, HgCd_sum,
                                                                               HgCd))
            if Ne_sum == 0 or HgCd_sum == 0:
                isBad = True
        else:
            self.add_msg('w', "text='%s: NE and/or HgCd not in FITS header.'" % self.cam)
            isBad = True

        return isBad

    def _load_data(self, indir, expnum1, expnum2):
        """
        Read in the two images, and check that headers are reasonable.
        Sets self.bigimg[1,2] and returns True if everything is ok, else return False."""
        filename1 = get_filename(indir, self.cam, expnum1)
        filename2 = get_filename(indir, self.cam, expnum2)
        if not os.path.exists(filename1) and not os.path.exists(filename2):
            raise HartError('All files not found: %s, %s!' % (filename1, filename2))

        # NOTE: we don't process with sdssproc, because the subarrays cause it to fail.
        # Also, because it would restore the dependency on SoS that this class removed!
        try:
            if fitsio:
                header1 = fitsio.read_header(filename1, 0)
            else:
                header1 = pyfits.getheader(filename1, 0)
        except IOError:
            raise HartError('Failure reading file %s' % filename1)
        try:
            if fitsio:
                header2 = fitsio.read_header(filename2, 0)
            else:
                header2 = pyfits.getheader(filename2, 0)
        except IOError:
            raise HartError('Failure reading file %s' % filename2)

        if self.bad_header(header1) or self.bad_header(header2):
            raise HartError('Incorrect header values in fits file.')

        self.hartpos1 = self.check_Hartmann_header(header1)
        self.hartpos2 = self.check_Hartmann_header(header2)
        if self.hartpos1 is None or self.hartpos2 is None:
            raise HartError('FITS headers do not indicate these are Hartmann exposures.')
        if self.hartpos1 == self.hartpos2:
            raise HartError('FITS headers indicate both exposures had same Hartmann position: %s' %
                            self.hartpos1)

        # upcast the arrays, to make later math work better.
        if fitsio:
            self.bigimg1 = np.array(fitsio.read(filename1, 0), dtype='float64')
            self.bigimg2 = np.array(fitsio.read(filename2, 0), dtype='float64')
        else:
            self.bigimg1 = np.array(pyfits.getdata(filename1, 0), dtype='float64')
            self.bigimg2 = np.array(pyfits.getdata(filename2, 0), dtype='float64')
        self.header1 = header1
        self.header2 = header2

    def _do_gain_bias(self):
        """Apply the bias and gain to the images."""
        bigimg1 = self.bigimg1
        bigimg2 = self.bigimg2
        # determine bias levels
        bias1 = [np.median(bigimg1[self.bias_slice[0]]), np.median(bigimg1[self.bias_slice[1]])]
        bias2 = [np.median(bigimg2[self.bias_slice[0]]), np.median(bigimg2[self.bias_slice[1]])]
        # apply bias and gain to the images
        # gain_slice is a dict with keys 'r' and 'b
        gain = self.cam_gains[self.cam]
        gslice = self.gain_slice[self.cam[0]]

        # Only apply gain to quadrants 0 and 1, since we aren't using quadrants 2 and 3.
        # NOTE: we are overwriting the original array, including the original bias region.
        # This is ok, because all the processing is done on a subregion of this,
        # indexed from the new edge.
        bigimg1[gslice[0][0]] = gain[0] * (bigimg1[gslice[0][1]] - bias1[0])
        bigimg1[gslice[1][0]] = gain[1] * (bigimg1[gslice[1][1]] - bias1[1])
        bigimg2[gslice[0][0]] = gain[0] * (bigimg2[gslice[0][1]] - bias2[0])
        bigimg2[gslice[1][0]] = gain[1] * (bigimg2[gslice[1][1]] - bias2[1])

    def _check_images(self):
        """Check that there is actually light in the images."""
        # The core of the idea here is to find the variance of a region with
        # several bright lines. Low variance means no light.
        # However, we also have to ensure we aren't thrown off by a few strong
        # cosmic rays or several bright pixels.
        # So, we clip all values > 1000 to 1000 before we compute the variance,
        # to reduce the impact of a handful of bright pixels.
        img1 = self.bigimg1[self.region].copy()
        img2 = self.bigimg2[self.region].copy()
        img1[img1 > 1000] = 1000
        img2[img2 > 1000] = 1000

        # ddof=1 for consistency with IDL's variance() which has denominator (N-1)
        # NOTE: need to keep r&b slices in sync with subFrame changes.
        if 'b' in self.cam:
            var1 = np.var(img1[300:450, :], ddof=1)
            var2 = np.var(img2[300:450, :], ddof=1)
        else:
            var1 = np.var(img1[0:150, :], ddof=1)
            var2 = np.var(img2[0:150, :], ddof=1)

        if var1 < 100 or var2 < 100:
            raise HartError(
                'THERE DOES NOT APPEAR TO BE ANY LIGHT FROM THE ARCS IN %s!!!' % self.cam)

    def _find_shift(self, order=3):
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
        mask = np.ones(subimg1.shape, dtype='f8')
        mask[:10, :] = 0
        mask[-10:, :] = 0
        mask[:, :10] = 0
        mask[:, -10:] = 0

        # Compute linear correlation coefficients
        # Calculate the maximum product of the two images when shifting by steps of dx.
        dx = 0.05
        nshift = int(np.ceil(2 * self.maxshift / dx))
        xshift = -self.maxshift + dx * np.arange(nshift, dtype='f8')
        self.xshift = xshift  # save for plotting

        def calc_shift(xs, img1, img2, mask):
            shifted = interpolation.shift(img2, [xs, 0], order=order, prefilter=False)
            return (img1 * shifted * mask).sum()

        self.coeff = np.zeros(nshift, dtype='f8')
        filtered1 = interpolation.spline_filter(subimg1)
        filtered2 = interpolation.spline_filter(subimg2)
        for i in range(nshift):
            # self.coeff[i] = (subimg1 * interpolation.shift(subimg2,
            #                                                [xshift[i], 0],
            #                                                order=order) * mask).sum()
            # self.coeff[i] = (filtered1 * interpolation.shift(filtered2,
            #                                                  [xshift[i], 0],
            #                                                  order=order,
            #                                                  prefilter=False) * mask).sum()
            self.coeff[i] = calc_shift(xshift[i], filtered1, filtered2, mask)

        ibest = self.coeff.argmax()
        self.ibest = ibest  # save for plotting
        self.xoffset = xshift[ibest]
        # If the sequence is actually R-L, instead of L-R,
        # then the offset acctually goes the other way.
        if self.hartpos1 == 'right':
            self.xoffset = -self.xoffset

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
        offset = self.xoffset * m + b

        if abs(offset) < self.focustol:
            focus = 'In Focus'
            self.focused = True
            msglvl = 'i'
        else:
            focus = 'Out of focus'
            self.focused = False
            msglvl = 'w'
        self.add_msg(msglvl, '%sMeanOffset=%.2f,"%s"' % (self.cam, offset, focus))

        piston = int(offset * self.fudge[self.cam])
        if 'r' in self.cam:
            self.add_msg('i', '%sPistonMove=%d' % (self.cam, piston))
        else:
            self.add_msg('i', '%sRingMove=%.1f' % (self.cam, -piston / self.bsteps))
        self.piston = piston


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
        # how much pixel-to-pixel separation we allow to be "in focus"
        self.focustol = constants['focustol']

        self.coeff = coeff

        # the sub-frame region on the chip to read out when doing quick-hartmanns.
        self.subFrame = [850, 1400]

        self.data_root_dir = '/data/spectro'
        self.plotfilebase = 'Collimate-%05d_%08d-%08d.png'

        self.reinit()

    def reinit(self):
        self.success = True
        # final results go here
        self.result = {'sp1': {'b': np.nan, 'r': np.nan}, 'sp2': {'b': np.nan, 'r': np.nan}}
        self.full_result = {'sp1': {'b': None, 'r': None}, 'sp2': {'b': None, 'r': None}}
        self.moves = {'sp1': 0, 'sp2': 0}
        self.residuals = {'sp1': [0, 0., ''], 'sp2': [0, 0., '']}
        self.bres_min = {'sp1': 0., 'sp2': 0.}

        # Can't use update_status here, as we don't necessarily have a cmd available.
        myGlobals.hartmannStatus = 'initialized'

    def __call__(self, cmd, moveMotors=False, subFrame=True,
                 ignoreResiduals=False, noCheckImage=False, plot=False,
                 minBlueCorrection=False, bypass=None, cameras=None):
        """Take and reduce a pair of hartmann exposures.

        Usually apply the recommended collimator moves.

        Parameters
        ----------
        cmd : Cmdr
            The currently active Commander instance, for passing info/warn
            messages.
        moveMotors : bool
            Apply the computed corrections.
        subFrame : bool
            Only readout a part of the chip.
        ignoreResiduals : bool
            Apply red moves regardless of resulting blue residuals.
        noCheckImage : bool
            Skip the variance calculation check for whether there is light in
            the camera (useful for sparse pluggings).
        plot : bool
            Make a plot representing the calculation.
        minBlueCorrection : bool
            Calculates only the minimum blue ring correction needed to
            get the focus within the tolerance level.
        bypass : list or None
            A list of strings with the bypasses to apply.
        cameras : list
            Cameras to process.

        """

        self.cmd = cmd

        # Check bypass type
        bypass = bypass or []
        if not isinstance(bypass, list):
            bypass = [bypass]

        try:

            # take the hartmann frames.
            exposureId = self.take_hartmanns(subFrame)

            # Perform the collimation calculations
            self.collimate(
                exposureId[0],
                exposureId[1],
                ignoreResiduals=ignoreResiduals,
                plot=plot,
                noCheckImage=noCheckImage,
                minBlueCorrection=minBlueCorrection,
                bypass=bypass,
                cameras=cameras)

            if self.success and moveMotors:
                self._move_motors()

        except HartError as e:

            self.cmd.error('text="%s"' % e)
            self.success = False

        except Exception as e:

            self.cmd.error('text="Unhandled Exception when processing Hartmanns!"')
            self.cmd.error('text="%s"' % e)
            self.success = False

        update_status(self.cmd, 'idle')

    def _bundle_result(self, cams, results):
        """Return dict of spec:{cam:piston}."""

        for cam, result in zip(cams, results):
            self.full_result['sp' + cam[1]][cam[0]] = result
            self.result['sp' + cam[1]][cam[0]] = result.piston

    def output_messsages(self, results):
        """Send the messages that each OneCam process produced."""
        mdict = {'i': self.cmd.inform, 'w': self.cmd.warn, 'e': self.cmd.error}
        for cam_result in results:
            for msg in cam_result.messages:
                mdict[msg[0]](msg[1])

    def file_waiter(self, files):
        """
        Wait until all files exist, or 8 seconds have passed.
        Return None if all files exist, or the files that weren't found.
        """
        counter = 0
        wait = 0.5  # seconds
        # Fail after 12 seconds, so scale by wait time.
        while counter <= 12 / wait:
            time.sleep(wait)
            test = [os.path.exists(f) for f in files]
            if all(test):
                return None
            counter += 1
        return [files[i] for i, x in enumerate(test) if not x]

    def _collimate(self, expnum1, expnum2, indir, docams, noCheckImage):
        """The guts of the collimation, to be wrapped in a try:except block."""

        # pool = ThreadPool(len(docams)) # NOTE: for testing with threads instead of processes
        pool = Pool(len(docams))

        oneCam = OneCam(self.m, self.b, self.bsteps, self.focustol, self.coeff,
                        expnum1, expnum2, indir, noCheckImage=noCheckImage, bypass=self.bypass)

        results = pool.map(oneCam, docams)

        pool.close()
        pool.join()

        self.output_messsages(results)
        success = dict([(x.cam, x.success) for x in results])
        if not all(success.values()):
            failures = [x for x in success if not success[x]]
            raise HartError('Collimation calculation failed for %s.' % ','.join(failures))

        self._bundle_result(docams, results)

    def collimate(self, expnum1, expnum2=None, indir=None, mjd=None,
                  cameras=None, test=False, ignoreResiduals=False,
                  plot=False, cmd=None, noCheckImage=False,
                  minBlueCorrection=False, bypass=None):
        """Compute the spectrograph collimation focus from Hartmann exposures.

        Parameters
        ----------
        expnum1 : int
            First exposure number of raw sdR file.
        expnum2 : int or None
            Second exposure number (if `None`: expnum1 + 1)
        indir : str
            Directory where the exposures are located.
        mjd : int
            MJD of exposures in /data directory.
        cameras : list
            Cameras to process.
        test : bool
            If True, we are trying to determine the collimation parameters,
            so ignore 'b' parameter.
        ignoreResiduals : bool
            Apply red moves even if blue residuals are too high.
        plot : bool
            If True, save a plot of the best fit collimation.
        minBlueCorrection : bool
            If True, calculates the minimum blue correction needed to
            get in focus.
        cmd : Cmdr
            Command handler
        bypass : list or None
            Bypasses to apply.

        """

        specs = myGlobals.specs
        spec_ids = [int(spec[-1]) for spec in specs]

        cameras = cameras or myGlobals.cameras
        cameras = [camera for camera in cameras if int(camera[-1]) in spec_ids]

        self.bypass = bypass or []

        self.test = test
        if cmd is not None:
            self.cmd = cmd
        if expnum2 is None:
            expnum2 = expnum1 + 1

        if mjd is not None:
            self.mjd = mjd
        if indir is None:
            indir = os.path.join(self.data_root_dir, str(self.mjd))

        update_status(self.cmd, 'waiting on files')

        files1 = [get_filename(indir, '%s' % cam, expnum1) for cam in cameras]
        files2 = [get_filename(indir, '%s' % cam, expnum2) for cam in cameras]

        files_missing = self.file_waiter(files1 + files2)
        if files_missing is not None:
            raise HartError('Cannot complete collimation, these files '
                            'not found: %s' % ','.join(files_missing))

        update_status(self.cmd, 'processing')

        try:
            self._collimate(expnum1, expnum2, indir, cameras, noCheckImage)
        except Exception as e:
            self.success = False
            self.cmd.error('text="Collimation calculation failed! %s"' % e)
            return
        else:
            for spec in specs:
                self._mean_moves(spec, ignoreResiduals=ignoreResiduals,
                                 minBlueCorrection=minBlueCorrection)
            if plot:
                self.make_plot(expnum1, expnum2)

    def take_hartmanns(self, subFrame):
        """
        Take a pair of hartmann exposures, in self.subFrame if requested.
        Returns the exposure IDs of the two exposures.
        """

        update_status(self.cmd, 'exposing')

        exposureIds = []
        timeLim = 120.0
        for side in 'left', 'right':
            window = 'window={0},{1}'.format(*self.subFrame) if subFrame else ''
            cmdStr = 'exposure arc hartmann=%s itime=4 %s %s' % (side, window,
                                                                 ('noflush'
                                                                  if side == 'right' else ''))
            ret = self.actor.cmdr.call(
                actor='boss', forUserCmd=self.cmd, cmdStr=cmdStr, timeLim=timeLim)
            if ret.didFail:
                raise HartError('Failed to take %s hartmann exposure"' % (side))
            # opscore fake-Ints don't cleanly pickle for multiprocessing.
            exposureId = int(self.models['boss'].keyVarDict['exposureId'][0])
            # NOTE: exposureId is a lagging indicator.
            exposureId += 1
            exposureIds.append(exposureId)
            self.mjd = int(astrodatetime.datetime.utcnow().sdssjd)
            self.cmd.inform('text="got hartmann %s exposure %d"' % (side, exposureId))
        return exposureIds

    def _mean_moves(self, spec, ignoreResiduals=False, minBlueCorrection=False):
        """Compute the mean movement and residuals for this spectrograph,
        after r&b moves have been determined."""

        if np.all(np.isnan(self.result[spec].values())):
            self.cmd.warn('text="No camera information available for {}."'.format(spec))
            self.success = False
            return

        avg = np.nanmean(self.result[spec].values())
        bres = -(self.result[spec]['b'] - avg) / self.bsteps
        rres = self.result[spec]['r'] - avg

        if np.isnan(bres):
            self.cmd.warn('text="bres is nan, skipping blue ring correction,"')
            bres = 0.

        # Calculates the minimum blue ring correction needed to get in the
        # focus tolerance plus a buffer (see ticket #2701).
        buff = 0  # We don't use any buffer for now, just report the blue ring
        # move to get exactly into tolerance.
        if abs(bres) >= self.badres:
            bres_min = 2 * (bres - np.sign(bres) * self.badres) + np.sign(bres) * buff
        else:
            bres_min = 0.

        if abs(bres) < self.badres:
            resid = '"OK"'
            msglvl = self.cmd.inform
        elif ignoreResiduals:
            if not minBlueCorrection:
                resid = '"Move blue ring %.1f degrees."' % (bres * 2)
            else:
                resid = ('"Move blue ring {0:.1f} degrees. '
                         'This is the minimum move needed to '
                         'get in focus tolerance."'.format(bres_min))
            msglvl = self.cmd.warn
        else:
            if not minBlueCorrection:
                resid = ('"Bad angle: move blue ring %.1f degrees then rerun '
                         'gotoField with Hartmanns checked."' % (bres * 2))
            else:
                resid = ('"Bad angle: move blue ring %.1f degrees then '
                         'rerun gotoField with Hartmanns checked. This is the '
                         'minimum move needed to get in focus tolerance."' % bres_min)

            msglvl = self.cmd.warn
            self.success = False

        msglvl('%sResiduals=%.0f,%.1f,%s' % (spec, rres, bres, resid))
        self.cmd.inform('%sAverageMove=%d' % (spec, int(avg)))
        self.moves[spec] = avg
        self.residuals[spec] = [rres, bres, resid]
        self.bres_min[spec] = bres_min

    def move_motors(self):
        """Apply computed collimator piston moves, in an exception-safe manner."""
        try:
            self._move_motors()
        except HartError as e:
            self.cmd.error('text="%s"' % e)
            self.success = False
        except Exception as e:
            self.cmd.error('text="Unhandled Exception when processing Hartmanns!"')
            self.cmd.error('text="%s"' % e)
            self.success = False

    def _move_motors(self):
        """Apply computed collimator piston moves."""
        update_status(self.cmd, 'moving')
        for spec in myGlobals.specs:
            piston = self.moves[spec]
            self._move_motor(spec, piston)

    def _move_motor(self, spec, piston):
        """Apply a collimator piston move to spectrograph spec."""
        if int(piston) == 0:
            self.cmd.respond('text="no recommended piston change for %s"' % (spec))
            return
        timeLim = 30.0
        cmdVar = self.actor.cmdr.call(
            actor='boss',
            forUserCmd=self.cmd,
            cmdStr='moveColl spec=%s piston=%d' % (spec, piston),
            timeLim=timeLim)
        if cmdVar.didFail:
            errMsg = 'Failed to move collimator pistons for %s.' % spec
            if 'Timeout' in cmdVar.lastReply.keywords:
                errMsg = ' '.join((errMsg, 'Command timed out'))
            raise HartError(errMsg)

    def _get_inset_range(result, ibest, xshift):
        """Get the xrange of the inset plot."""
        inset_xlim = 14
        inset = [ibest - inset_xlim, ibest + inset_xlim]
        # prevent array overflow when getting the inset plot range.
        if ibest < inset_xlim:
            inset[0] = 0
        if len(xshift) - ibest < inset_xlim:
            inset[1] = len(xshift) - 1
        return inset

    def _plot_one(self, ax1, ax2, spec, shade='', marker='*'):
        """
        Plot collimation curves for one spectrograph.
        Set shade='dark' to get the dark colors (e.g. to distinguish sp1 and sp2).
        """
        ylim1 = [0.4, 1.05]
        ylim2 = [0.92, 1.01]

        def color(cam):
            rb = {'r': 'red', 'b': 'cyan'}
            return shade + rb[cam]

        result = self.full_result[spec]
        for cam in result:
            inset = self._get_inset_range(result[cam].ibest, result[cam].xshift)
            ax1.plot(
                result[cam].xshift,
                result[cam].coeff / max(result[cam].coeff),
                '*-',
                color=color(cam),
                lw=1.5,
                mec='none',
                ms=6,
                marker=marker,
                label=cam + spec[2])
            ax2.plot(
                result[cam].xshift[inset[0]:inset[1]],
                result[cam].coeff[inset[0]:inset[1]] / max(result[cam].coeff),
                '*-',
                color=color(cam),
                lw=1.5,
                mec='none',
                ms=6,
                marker=marker)
            ax1.axvline(result[cam].xoffset, ls='--', lw=1.2, color=color(cam))
            ax2.axvline(result[cam].xoffset, ls='--', lw=1.2, color=color(cam))
            plt.yticks(np.arange(0.90, 1.01, .05))
        ax1.set_ylim(ylim1[0], ylim1[1])
        ax2.axis([result[cam].xshift[inset[0]], result[cam].xshift[inset[1]], ylim2[0], ylim2[1]])
        ax1.set_xlabel('pixels')
        ax1.set_ylabel('cross-correlation')

    def make_plot(self, expnum1, expnum2):
        """Save a plot of the pixel vs. correlation for this collimation."""
        plotfile = self.plotfilebase % (self.mjd, expnum1, expnum2)
        fig = plt.figure()
        title = 'Collimate: MJD=%5i Exp=%08i-%08i' % (self.mjd, expnum1, expnum2)
        ax1 = fig.add_axes([0.1, 0.1, 0.8, 0.8])
        ax2 = fig.add_axes([0.35, 0.2, 0.3, 0.3])

        for spec in ['sp1', 'sp2']:
            shade = 'dark' if spec == 'sp2' else ''
            marker = '^' if spec == 'sp2' else 's'
            self._plot_one(ax1, ax2, spec, shade=shade, marker=marker)
            ax1.set_title(title)

        ax1.legend(loc='best', labelspacing=0.2, borderpad=.2)

        plt.savefig(plotfile, bbox_inches='tight')
