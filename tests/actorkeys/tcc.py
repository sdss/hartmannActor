#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-28
# @Filename: tcc.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

# type: ignore


KeysDictionary(
    'tcc', (5, 2),
    Key('airTemp',
        Float(name='airTemp', invalid='nan', units='C'),
        help='Temperature of the outside air. Used for refraction correction.'),
    Key('axePos',
        Float(name='az', invalid='nan', units='deg', help='azimuth'),
        Float(name='alt', invalid='nan', units='deg', help='altitude'),
        Float(name='rot', invalid='nan', units='deg', help='instrument rotator'),
        help='Actual mount position of azimuth, altitude and instrument rotator,'
             'as reported by the axes controllers. Not many digits past the decimal but'
             'very useful for status displays. Axes that are not available are listed'
             'as \'nan\'. The state of the axes is given by AxisCmdState, which is always'
             'displayed in the same message as this keyword. See also TCCPos'),
    Key('axisConnState',
        String(name='az', help='azimuth axis'),
        String(name='alt', help='altitude axis'),
        String(name='rot',
               help='instrument rotator, or NotAvailable '
                    'if the current instrument has no rotator'),
        help='State of connection to each axis controller'),
    Key('altDTime', Float(invalid='nan', units='sec'),
        help='Approximate altitude controller clock time - TCC clock time. '
             'Warning: this has systematic error on the order of 0.1 seconds due '
             'to communication lag. It is primarily intended to indicate serious '
             'time discrepancies. Furthermore, some or all axes may show large '
             'error if any one axis controller delays the write or times out. '
             'To fix a time discrepancy, first set the TCC clock via the WWV '
             'clock (SET TIME), then set the controller clocks (AXIS INIT). '
             'has systematic error due to communication delays.'),
    Key('altErr',
        Float(name='abs', invalid='nan', units='as', help='maximum absolute value'),
        Float(name='mean', invalid='nan', units='as', help='mean absolute value'),
        Float(name='std', invalid='nan', units='as',
              help='standard deviation absolute value'),
        doCache=False,
        help='Altitude servo error statistics: maximum absolute value,'
             ' mean and standard deviation.'),
    Key('altLim',
        Float(name='min', invalid='nan', units='deg', help='minimum position'),
        Float(name='max', invalid='nan', units='deg', help='maximum position'),
        Float(name='speed', invalid='nan', units='deg/sec', help='maximum speed'),
        Float(name='acceler', invalid='nan',
              units='deg/sec^2', help='maximum acceleration'),
        Float(name='jerk', invalid='nan', units='deg/sec^3', help='maximum jerk'),
        help='Altitude motion limits used by the TCC (which are more restrictive '
             'than the limits used by the axis controller).'),
    Key('altReply', String(),
        help='Unparsed reply from the altitude axis controller'),
    Key('altStat',
        Float(name='pos', invalid='nan', units='deg', help='position'),
        Float(name='vel', invalid='nan', units='deg/sec', help='velocity'),
        Float(name='time', invalid='nan', units='TAI (MJD, sec)', help='time'),
        UInt(name='status', invalid='nan', reprFmt='0x%x', help='status word'),
        help='Status reported by the axis controller.'),
    Key('altTrackAdvTime',
        Int(name='sampl', invalid='nan', help='number of samples'),
        Float(name='min', invalid='nan', units='sec', help='minimum'),
        Float(name='max', invalid='nan', units='sec', help='maximum'),
        Float(name='mean', invalid='nan', units='sec', help='mean'),
        Float(name='std', invalid='nan', units='sec', help='standard deviation'),
        doCache=False,
        help='Statistics for how far in advance tracking updates are '
             'sent to the altitude controller'),
    Key('axisBadStatusMask',
        UInt(invalid='nan', reprFmt='0x%x'),
        help='If any bit is high both in this mask and in the '
             'status word from an axis controller, '
             'then the status is flagged as \'bad\'. This flag is stored in '
             'the AxeLim block. See also AxisWarnStatusMask and Bad<AxisName>Status.'),
    Key('axisCmdState',
        Enum('Drifting', 'Halted', 'Halting', 'Slewing',
             'Tracking', 'NotAvailable', '?',
             labelHelp=[
                 'The axis is moving at constant velocity while the TCC computes a slew path.',
                 'The axis has been halted (by user request or because of a '
                 'problem such as a communications failure).',
                 'The axis is slewing to a stop, as per the track/stop command.',
                 'The axis is slewing.',
                 'The axis is tracking.',
                 '(only applicable to the rotator) there is no rotator at '
                 'this instrument port.',
                 'Unknown (indicates a TCC bug)']) * 3,
        help='The state of each axis as commanded by the TCC. '
             'Warning: this is only the state commanded by the TCC. '
             'To see what the axes are actually doing, see keywords such as '
             '!!! doesn\'t exist?: <AxisName>Stat!!!, AxePos and AxisErrCode. '
             'AxisCmdState supersedes TCCStatus, which is deprecated but still '
             'present for now.'),
    Key('axisErrCode',
        String(invalid='?') * 3,
        help='The error code for each axis, as a string. '
             'The error code explains why an axis is not moving. Common codes are: '
             'CannotCompute: Could not compute the position. '
             'ControllerError: The axis controller reported an error or there was a '
             'communications error (such as a timeout or bad command echo). '
             'HaltRequested: The axis was halted by the user. '
             'MinPos: The minimum position limit was exceeded. '
             'MaxPos: Maximum position limit exceeded, or '
             '(if alternate wraps allowed) position out of bounds. '
             'MaxVel: Maximum velocity exceeded. '
             'NoRestart: The axis was already halted and a slew or offset was performed '
             'that left halted axis halted. '
             'NotAvailable: (only applicable to the rotator) there is '
             'no rotator at this instrument port. '
             '?: Unknown (indicates a TCC bug).'),
    Key('axisMaxDTime', Float(invalid='nan', units='sec'),
        doCache=False,
        help='Indicates the maximum axis controller clock error (in sec), '
             'that is acceptable before a warning is printed. '
             'This value is stored in the AxeLim block. '
             'See also <AxisName>DTime and Bad<AxisName>DTime.'),
    Key('axisNoSlew',
        String(help='A string of three characters corresponding to azimuth, '
                    'altitude, and instrument rotator respectively. '
                    'Each character may be \'T\', for cannot slew, or \'F\' for can slew.'),
        doCache=False,
        help='Indicates that one or more axes will not be able to slew.'),
    Key('axisNoTrack',
        String(help='A string of three characters corresponding to azimuth, '
                    'altitude, and instrument rotator respectively. '
                    'Each character may be \'T\', for initialized, or \'F\' for not.'),
        doCache=False,
        help='Indicates that one or more axes have stopped tracking '
             '(probably due to running into a limit).'),
    Key('axisWarnStatusMask',
        UInt(invalid='nan', reprFmt='0x%x'),
        help='If any bit is high both in this mask and in the '
             'status word from an axis controller, '
             'then the status is flagged as a warning. '
             'This mask is stored in the AxeLim block. '
             'See also AxisBadStatusMask and Warn<AxisName>Status.'),
    Key('azDTime', Float(invalid='nan', units='sec'),
        help='Approximate azimuth controller clock time - TCC clock time. '
             'Warning: this has systematic error on the order of 0.1 seconds '
             'due to communication lag. It is primarily intended to indicate '
             'serious time discrepancies. Furthermore, some or all axes may '
             'show large error if any one axis controller delays the write '
             'or times out. To fix a time discrepancy, first set the TCC clock '
             'via the WWV clock (SET TIME), then set the controller clocks '
             '(AXIS INIT). has systematic error due to communication delays.'),
    Key('azErr',
        Float(name='abs', invalid='nan', units='as', help='maximum absolute value'),
        Float(name='mean', invalid='nan', units='as', help='mean absolute value'),
        Float(name='std', invalid='nan', units='as',
              help='standard deviation absolute value'),
        doCache=False,
        help='Azimuth servo error statistics: maximum absolute value, '
             'mean and standard deviation.'),
    Key('azLim',
        Float(name='min', invalid='nan', units='deg', help='minimum position'),
        Float(name='max', invalid='nan', units='deg', help='maximum position'),
        Float(name='speed', invalid='nan', units='deg/sec', help='maximum speed'),
        Float(name='acceler', invalid='nan',
              units='deg/sec^2', help='maximum acceleration'),
        Float(name='jerk', invalid='nan', units='deg/sec^3', help='maximum jerk'),
        help='Azimuth motion limits used by the TCC (which are more restrictive '
             'than the limits used by the axis controller).'),
    Key('azReply', String(),
        help='Unparsed reply from the azimuth axis controller'),
    Key('azStat',
        Float(name='pos', invalid='nan', units='deg', help='position'),
        Float(name='vel', invalid='nan', units='deg/sec', help='velocity'),
        Float(name='time', invalid='nan', units='TAI (MJD, sec)', help='time'),
        UInt(name='status', invalid='nan', reprFmt='0x%x', help='status word'),
        help='Status reported by the axis controller.'),
    Key('azTrackAdvTime',
        Int(name='sampl', invalid='nan', help='number of samples'),
        Float(name='min', invalid='nan', units='sec', help='minimum'),
        Float(name='max', invalid='nan', units='sec', help='maximum'),
        Float(name='mean', invalid='nan', units='sec', help='mean'),
        Float(name='std', invalid='nan', units='sec', help='standard deviation'),
        doCache=False,
        help='Statistics for how far in advance tracking updates '
             'are sent to the azimuth controller'),
    Key('azWrapPref',
        Enum('None', 'Nearest', 'Negative', 'Middle', 'Positive', 'NoUnwrap'),
        doCache=False,
        help='Preferred wrap for the azimuth axis.'),
    Key('badAltDTime',
        help='Indicates that the altitude axis controller\'s '
             'clock is too far off from the TCC\'s clock.'),
    Key('badAltStatus',
        help='Indicates that a seriously bad bit is set in the altitude axis '
             'controller\'s status word. See also AxisBadStatusMask and '
             'Warn<AxisName>Status.'),
    Key('badAzDTime',
        help='Indicates that the azimuth axis controller\'s clock is '
             'too far off from the TCC\'s clock.'),
    Key('badAzStatus',
        help='Indicates that a seriously bad bit is set in the azimuth axis '
             'controller\'s status word. See also AxisBadStatusMask and '
             'Warn<AxisName>Status.'),
    Key('badRotDTime',
        help='Indicates that the rotator axis controller\'s clock is '
             'too far off from the TCC\'s clock.'),
    Key('badRotStatus',
        help='Indicates that a seriously bad bit is set in the '
             'rotator axis controller\'s status word. See also '
             'AxisBadStatusMask and Warn<AxisName>Status.'),
    Key('boresight',
        PVT(name='az'),
        PVT(name='alt'),
        help='The user-specified position of the boresight '
             '(the position of the object on the instrument). '
             'In older versions of the TCC it was set via \'Offset InstPlane\', '
             'and this still may work, but the new recommended way to set '
             'it is \'Offset Boresight\'. Internally to the TCC this '
             'variable is known as Obj_Inst_xy.'),
    Key('broadcast', String(), doCache=False,
        help='Message sent by the broadcast command.'),
    Key('calibOff',
        PVT(name='az', help='azimuth'),
        PVT(name='alt', help='altitude'),
        PVT(name='rot', help='rotator'),
        help='The current calibration offset.'),
    Key('chebyBegEndTime',
        Float(name='begin', units='sec', help='beginning time'),
        Float(name='end', units='sec', help='end time'),
        doCache=False,
        help='Time range (TAI, MJD seconds) over which the '
             'Chebyshev polynomial is evaluated. Only meaningful if UseCheby=T.'),
    Key('chebyCoeffsUser1',
        Float() * (0, None),
        doCache=False,
        help='Coefficients of a Chebychev polynomial of the '
             'first kind specifying the value of user '
             'position axis 1 (deg). The range of the polynomial '
             'is given by ChebyBegEndTime. Only meaningful if UseCheby=T.'),
    Key('chebyCoeffsUser2',
        Float() * (0, None),
        doCache=False,
        help='Coefficients of a Chebychev polynomial of the '
             'first kind specifying the value of user '
             'position axis 2 (deg). The range of the polynomial is '
             'given by ChebyBegEndTime. Only meaningful if UseCheby=T.'),
    Key('chebyCoeffsDist',
        Float() * (0, None),
        doCache=False,
        help='Coefficients of a Chebychev polynomial of the first kind '
             'specifying the value of distance to the object (au). '
             'The range of the polynomial is given by ChebyBegEndTime. '
             'Only meaningful if UseCheby=T.'),
    Key('chebyFile',
        String(help='path to file'),
        doCache=False,
        help='Path of a file loaded using Track/Chebyshev=path. The file '
             'contains Chebyshev polynomial coefficients that describe the '
             'path of an object. Only meaningful if UseCheby=T.'),
    Key('cmd',
        String(),
        doCache=False,
        help='Partial text of a TCC command. Only 40 or so characters '
             'is shown; the remainder is truncated without warning.'),
    Key('cmdDTime',
        Float(invalid='nan', units='sec'),
        doCache=False,
        help='Predicted duration of command, in seconds.'),
    Key('convAng',
        PVT(),
        doCache=False,
        help='Change in orientation: the converted reference direction minus '
             'the user-supplied reference direction.A vector is constructed '
             'perpendicular to the position along the user-supplied reference '
             'direction. This vector is converted to the final coordinate '
             'system, and its angle measured with respect to the final coordinate '
             'system to give the converted reference direction.'),
    Key('convPM',
        Float(name='polMotion', invalid='nan',
              units='as/century', help='proper motion') * 2,
        Float(name='parallax', invalid='nan', units='as', help='parallax'),
        Float(name='radVel', invalid='nan', units='km/sec',
              help='radial velocity (positive receding)'),
        doCache=False,
        help='Converted proper motion, parallax, and radial velocity '
             '(output of CONVERT command).'),
    Key('convPos',
        PVT(name='az'),
        PVT(name='alt'),
        doCache=False, help='Converted position (output of CONVERT command).'),
    Key('currArcOff',
        PVT(name='az'),
        PVT(name='alt'),
        help='The current value of the arc offset. This will only differ '
             'from the ObjArcOff if the velocity is nonzero and is being '
             'corrected for drift scanning (TDICorr). (Internal to the TCC '
             'this is obj.userArcOff with the velocity multiplied by '
             'obj.arcVelCorr. There is no obj.currArcOff.)'),
    Key('currUsers',
        UInt(invalid='nan'),
        help='The number of users currently connected to the TCC software.'),
    Key('disabledProc',
        String() * (0), doCache=False,
        help='Shows which optional processes are disabled (if any). '
             'Note: the names are as known by VMS; '
             'hence they include a leading \'T_\' and are all uppercase.'),
    Key('duration',
        Float(invalid='nan', units='sec'), doCache=False,
        help='Shows the current duration (in seconds) of some operation. '
             'Other keywords on the same line should indicate what this '
             'is the duration of. See also See also MaxDuration.'),
    Key('expTime',
        Float(invalid='nan', units='sec'), doCache=False,
        help='Exposure time (sec). This time is used for guiding, '
             'pointing error corrections, and as a default for GCAMERA commands.'),
    Key('expected',
        String(), doCache=False,
        help='Bad echo from a controller; this is the text that was expected. See also Received.'),
    Key('failed',
        String(), doCache=False,
        help='The command failed. Warning: not reliably output and not intended '
             'for automated use; please use the command status code instead.'),
    Key('gCamID',
        Int(invalid='nan', help='device ID') * (1, 2),
        help='Identification of the guide camera in use.'),
    Key('gcView',
        String(),
        help='Name of guide camera view. The normal default view has no name ('')'),
    Key('gImCtr',
        Float(name='x', invalid='nan', help='x pixels'),
        Float(name='y', invalid='nan', help='y pixels'),
        help='Guide image center (unbinned pixels); '
             'ses also GImScale. pos. '
             '(unbinned pixels) = offset + scale * pos. (deg).'),
    Key('gImLim',
        Float(name='minX', invalid='nan', help='min x'),
        Float(name='minY', invalid='nan', help='min y'),
        Float(name='maxX', invalid='nan', help='max x'),
        Float(name='maxY', invalid='nan', help='max y'),
        help='Edges of guide image (unbinned pixels).'),
    Key('gImScale',
        Float(name='x', invalid='nan', help='x scale'),
        Float(name='y', invalid='nan', help='y scale'),
        help='Guide image scale (unbinned pixels/deg); '
             'see also GImCtr. '
             'pos. (unbinned pixels) = offset + scale * pos. (deg).'),
    Key('gmechID',
        UInt(invalid='nan') * (1, 2),
        help='guide camera mechanical controller iD (0 if none); '
             'new TCC outputs one value, old TCC outputs two'),
    Key('gPCtr', Float(invalid='nan') * 2,
        help='deprecated (use gProbeInfo)', doCache=False),
    Key('gPLim', Float(invalid='nan') * 4,
        help='deprecated (use gProbeInfo)', doCache=False),
    Key('gPRotGImAng', Float(invalid='nan'),
        help='deprecated(use gProbeInfo)', doCache=False),
    Key('gPRotXY',
        Float(name='rotX', invalid='nan'),
        Float(name='rotY', invalid='nan'),
        help='deprecated (use gProbeInfo)', doCache=False),
    Key('gProbe', Int(invalid='nan'), help='deprecated (use gProbeInfo)', doCache=False),
    Key('gProbeInfo',
        Int(name='number', invalid='nan', help='number (1, ...)'),
        Bool('F', 'T', help='enabled?', name='enabled'),
        Float(name='cenX', invalid='nan', help='center x', units='unbinned pixels'),
        Float(name='cenY', invalid='nan', help='center y', units='unbinned pixels'),
        Float(name='minX', invalid='nan', help='min x', units='unbinned pixels'),
        Float(name='minY', invalid='nan', help='min y', units='unbinned pixels'),
        Float(name='maxX', invalid='nan', help='max x', units='unbinned pixels'),
        Float(name='maxY', invalid='nan', help='max y', units='unbinned pixels'),
        Float(name='rotX',
              invalid='nan',
              help='x position of center of guide probe w.r.t. rotator',
              units='deg'),
        Float(name='rotY',
              invalid='nan',
              help='y position of center of guide probe w.r.t. rotator',
              units='deg'),
        Float(name='angle',
              invalid='nan',
              help='angle from probe image x to rotator x',
              units='deg'),
        help='information about a guide probe; information is provided for all '
             'probes in order from 1 to N, so if you see information for probe 1 '
             'you can erase data about the remaining probes',
        doCache=False),
    Key('gSWavelength',
        Float(invalid='nan', units='A'),
        help='The central wavelength for the object (in Angstroms). Used to '
             'correct for refraction. See also ObjWavelength'),
    Key('guideOff',
        PVT(name='az', help='azimuth'),
        PVT(name='alt', help='altitude'),
        PVT(name='rot', help='rotator'),
        help='The current guide offset.'),
    Key('humidity',
        Float(invalid='nan'),
        help='Relative humidity (fraction, NOT percent!); used for refraction correction.'),
    Key('iimCtr',
        Float(name='x', invalid='nan', units='pixels', help='x'),
        Float(name='y', invalid='nan', units='pixels', help='y'),
        help='Instrument image center (unbinned pixels). See also IImScale, IImLim. \
pos. (unbinned pixels) = offset + scale * pos. (deg)'),
    Key('iimLim',
        Float(name='minX', invalid='nan', units='pixels', help='min x'),
        Float(name='minY', invalid='nan', units='pixels', help='min y'),
        Float(name='maxX', invalid='nan', units='pixels', help='max x'),
        Float(name='maxY', invalid='nan', units='pixels', help='max y'),
        help='Edges of instrument image (unbinned pixels). See also IImScale, IImCtr.'),
    Key('iimScale',
        Float(name='x', invalid='nan', units='pixels/deg', help='x'),
        Float(name='y', invalid='nan', units='pixels/deg', help='y'),
        help='Instrument image scale (unbinned pixels/deg) See also IImCtr, IImLim. \
pos. (unbinned pixels) = offset + scale * pos. (deg)'),
    Key('inst',
        String(), help='Name of the current instrument.'),
    Key('instFocus',
        Float(invalid='nan', units='um'),
        help='Secondary mirror focus offset due to instrument.'),
    Key('instPos',
        Enum('NA1', 'NA2', 'BC1', 'TR1', 'TR2', 'SK1', 'SK2', 'SK3', 'SK4', 'CA1', 'non'),
        help='Name of instrument position (\'non\' if none specified yet).'),
    Key('ipConfig',
        String(help='A string of three characters corresponding to availablity '
                    'for instrument rotator, guide camera, and uider mechanical '
                    'respectively. Each character may be \'T\', for true, '
                    'or \'F\' for false.'),
        help='Instrument-position configuration, e.g. is an instrument rotator available'),
    Key('iter',
        UInt(invalid='nan'),
        doCache=False,
        help='Iteration number. Other keywords on the same line should '
             'indicate what is being iterated. See also MaxIter.'),
    Key('job',
        String(),
        doCache=False),
    Key('jobList',
        String() * (0),
        help='batch jobs that can be queued'),
    Key('jobStatus',
        String(name='name', help='name of job'),
        String(name='status', help='status of job'),
        help='status of current batch job'),
    Key('lst',
        Float(invalid='nan', units='deg'),
        help='Local apparent sidereal time (LST), as an angle.'),
    Key('maxDuration',
        Float(invalid='nan', units='sec'), doCache=False,
        help='Maximum duration of a task, in seconds. '
             'Other keywords on the same line should indicate '
             'what this is the maximum duration of. See also Duration.'),
    Key('maxIter',
        UInt(invalid='nan'), doCache=False,
        help='Maximum number of iterations allowed. '
             'Other keywords on the same line should indicate what '
             'is being iterated. See also Iter.'),
    Key('maxUsers', UInt(invalid='nan'),
        help='The maximum number of users that may use the TCC software at this'
             'time. See also CurrUsers. Warning: this value only applies to '
             'subsequent attempts to connect. If this value is reduced below '
             'the current number of users, it will have no affect on the current users.'),
    Key('mirrorConnState',
        String(name='prim',
               help='primary mirror, or NotAvailable '
                    'if no primary mirror controller'),
        String(name='sec',
               help='secondary mirror, or NotAvailable if no secondary mirror controller'),
        String(name='tert',
               help='tertiary mirror, or NotAvailable if no tertiary mirror controller'),
        help='State of connection to each mirror controller'),
    Key('moveItems',
        String(help='A 9 character string; each character is either '
                    'Y (item changed) or N (item did not change): '
                    '1=object name '
                    '2=any of: object position, coordinate system, epoch, distance, '
                    'proper motion (or parallax), or radial velocity'
                    '3=object magnitude'
                    '4=object offset'
                    '5=arc offset (eg for drift-scanning)'
                    '6=boresight position,'
                    '7=rotator angle or type of rotation'
                    '8=guide offset'
                    '9=calibration offset'),
        doCache=False,
        help='Indicates which user-set position attributes have been changed for a move. '
             'This keyword always appears with Moved or SlewBeg, and never appears any '
             'other time.'),
    Key('moved',
        help='Indicates that the telescope made an immediate move '
             '(the default style of offset). The telescope may still be '
             'moving (especially if it\'s a large offset), since the TCC has '
             'no reliable way of knowing when an immediate move is done.'),
    Key('numUsers', Int(), help='number of users'),
    Key('objArcOff',
        PVT(name='az'),
        PVT(name='alt'),
        help='User-specified arc offset. This is an offset along a great circle. '
             'The magnitude of the vector is the length of '
             'the arc. The angle of the vector specifies the tangent to the arc '
             '(at the beginning of the arc, e.g. at the position '
             'before applying the arc offset). '
             '(Note: if velocity is being corrected for drift scanning, '
             'e.g. TDICorr, then the position and time components are '
             'regularly updated. This is purely for internal bookkeeping purposes. '
             'The velocity component is left alone (ironically enough) '
             'but is not the true current velocity; for that see CurrArcOff.) '
             'See also CurrArcOff, TDICorr.'),
    Key('objDist',
        Float(invalid='nan', units='au'),
        help='Geocentric distance to the object, in au, or \'inf\' if very far away.'),
    Key('objInstAng',
        PVT(),
        help='Orientation of object on the instrument. '
             'Specifically, it is the angle from the instrument x,y axes to the axes '
             'of the object\'s user-specified coordinate system (typically RA,Dec). '
             'For example: if the direction of increasing coordinate system '
             'axis 1 (typically RA) lies along the instrument x axis, the angle '
             'is 0; if along y, the angle is 90.'),
    Key('objMag',
        Float(invalid='nan', units='mag'),
        help='Object brightness, in magnitudes.'),
    Key('objName',
        String(),
        help='Object name. The name is an arbitrary string set by the user or '
             'from a catalog or whatever. The TCC makes no use of the name.'),
    Key('objNetPos',
        PVT(name='az'),
        PVT(name='alt'),
        help='Position of object in the user-specified coordinate system, '
             'with proper motion, parallax & radial velocity '
             'removed to the current date, and including the current object '
             'offset and arc offset.'),
    Key('objOff',
        PVT(name='az'),
        PVT(name='alt'),
        help='deprecated: not supported by new TCC'),
    Key('objObs',
        PVT(name='az', help='azimuth'),
        PVT(name='alt', help='altitude'),
        help='observed (refracted apparent topocentric) position of target'),
    Key('objPM',
        Float(name='eqMotion',
              invalid='nan',
              help='equatorial proper motion (dEquatAng/dt)',
              units='as/century'),
        Float(name='polMotion', invalid='nan',
              help='polar proper motion', units='as/century'),
        Float(name='parallax', invalid='nan', help='parallax', units='arcsec'),
        Float(name='radialVel',
              invalid='nan',
              help='radial velocity (positive receding)',
              units='km/sec'),
        help='proper motion, etc. of target'),
    Key('objPos',
        PVT(name='az'),
        PVT(name='alt'),
        help='User-specified position of the object (excluding offsets).'),
    Key('objSys',
        Enum('ICRS', 'FK5', 'FK4', 'Gal', 'Geo', 'None', 'Topo',
             'Obs', 'Phys', 'Mount', 'Inst', 'GImage',
             name='sys'),
        Float(name='date',
              invalid='nan',
              help='date; 0 for systems with no date, and for observed systems '
                   'if the current date is being used'),
        help='User-specified coordinate system of object, '
             'as described in TCC Commands: coordSys'),
    Key('objWavelength',
        Float(invalid='nan', units='A'),
        help='The central wavelength for the object (in Angstroms). '
             'Used to correct for refraction. See also GSWavelength'),
    Key('objZPMPos',
        PVT(name='az'),
        PVT(name='alt'),
        help='Position of object in user-specified coordinate system, '
             'but with proper motion, parallax, and radial velocity '
             'removed to the current epoch.'),
    Key('predFWHM',
        Float(invalid='nan', units='as'),
        doCache=False,
        help='Predicted seeing FWHM (arcsec). Used for guiding and '
             'pointing error correction, and as a default for GCAMERA commands.'),
    Key('pressure',
        Float(invalid='nan', units='Pa'),
        help='Air pressure; used for refraction correction.'),
    Key('primActMount',
        Float(units='microsteps', invalid='nan') * (1, 6),
        help='Actuator lengths determined from primEncMount and the mirror model. '
             'This may not match primCmdMount, even if the actuators move as commanded, '
             'due to systematic errors in the mirror model.'
             'For an actuator without an encoder, the commanded actuator mount is used. '),
    Key('primCmdMount',
        Float(invalid='nan') * (1, 6),
        help='commanded position of primary mirror actuators', units='microsteps'),
    Key('primDesEncMount',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Desired encoder lengths, in actuator microsteps, '
             'based on primDesOrient and the mirror model. '
             'There is one entry per actuator, rather than per encoder: '
             'for an actuator without an encoder, the commanded actuator '
             'mount is used.'),
    Key('primEncMount',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Measured encoder lengths, in actuator microsteps, based on '
             'primDesOrient and the mirror model. There is one entry per '
             'actuator, rather than per encoder; for an actuator without '
             'an encoder, the commanded actuator mount is used.'),
    Key('primModelMount',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Actuator mount position determined from desOrient the the mirror model'),
    Key('primNetMountOffset',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Offset applied to a model mount at the beginning of a move, '
             'to prevent motion for a null move and speed up convergence for a small move. '
             'It primarily  compensates for systematic error in the mirror model.'),
    Key('primMountErr',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Error in mount position for a given iteration. '
             'Apply this delta to primCmdMount each iteration.'),
    Key('primDesOrient',
        Float(name='piston', invalid='nan', units='um', help='piston'),
        Float(name='xTilt', invalid='nan', units='as', help='x tilt'),
        Float(name='yTilt', invalid='nan', units='as', help='y tilt'),
        Float(name='xTransl', invalid='nan', units='um', help='x translation'),
        Float(name='yTransl', invalid='nan', units='um', help='y translation'),
        Float(name='rotation', invalid='nan', units='as',
              help='rotation about z (new TCC only)') * (0, 1),
        help='desired orientation of primary mirror'),
    Key('primDesOrientAge',
        Float(name='sec', invalid='nan', units='sec'),
        doCache=False,
        help='Time elapsed since this orient was commanded.'),
    Key('primF_BFTemp',
        Float(name='front', invalid='nan', units='C', help='front temperature'),
        Float(name='diff', invalid='nan', units='C',
              help='front-back temperature difference')),
    Key('primOrient',
        Float(name='pos', invalid='nan', units='um', help='piston'),
        Float(name='xTilt', invalid='nan', units='as', help='x tilt'),
        Float(name='yTilt', invalid='nan', units='as', help='y tilt'),
        Float(name='xTransl', invalid='nan', units='um', help='x translation'),
        Float(name='yTransl', invalid='nan', units='um', help='y translation'),
        Float(name='rotation', invalid='nan', units='as',
              help='rotation about z (new TCC only)') * (0, 1),
        help='actual orientation of primary mirror'),
    Key('primReply',
        String(),
        help='Unparsed reply from the primary mirror controller'),
    Key('primState',
        String(name='state',
               help='State of galil device, one of: Moving, Done, Homing, Failed, NotHomed'),
        UInt(name='iter', help='current iteration'),
        UInt(name='iterMax', help='max iterations'),
        Float(name='timeRemain',
              invalid='nan',
              units='seconds',
              help='remaining time on move or home'),
        Float(name='timeTotal',
              invalid='nan',
              units='seconds',
              help='total time for move or home'),
        help='summarizes current state of secondary galil and '
             'any remaning time or move iterations'),
    Key('primStatus',
        UInt(invalid='nan') * (1, 6),
        help='status word from the primiary mirror controller'),
    Key('ptCorr',
        Float(name='azCorr', invalid='nan', units='deg',
              help='az pointing correction on the sky'),
        Float(name='altCorr', invalid='nan', units='deg',
              help='alt pointing correction on the sky'),
        Float(name='xPos', invalid='nan', units='deg',
              help='x position in pointing frame'),
        Float(name='yPos', invalid='nan', units='deg',
              help='y position in pointing frame'),
        help='measured pointing error in a form suitable for guiding '
             '(thus, relative to current guide and calibration offsets).'
             'All values are in the pointing frame, which is the rotator '
             'frame rotated such that x = az'),
    Key('ptData',
        Float(name='azPhys', invalid='nan', units='deg',
              help='az desired physical position'),
        Float(name='altPhys', invalid='nan', units='deg',
              help='alt desired physical position'),
        Float(name='azMount', invalid='nan', units='deg',
              help='az mount position'),
        Float(name='altMount', invalid='nan', units='deg',
              help='alt mount position'),
        Float(name='rotPhys', invalid='nan', units='deg',
              help='rot physical angle'),
        help='measured pointing error in a form suitable recording pointing model data'),
    Key('ptErrProbe',
        Int(),
        help='guide probe to use for pointing error measurement; 0 if none'),
    Key('ptRefStar',
        Float(name='eqPos', invalid='nan', help='equatorial position', units='deg'),
        Float(name='polPos', invalid='nan', help='polar position', units='deg'),
        Float(name='parallax', invalid='nan', help='parallax', units='arcsec'),
        Float(name='eqMotion', invalid='nan',
              help='equatorial proper motion (dEquatAng/dt as arcsec/year)'),
        Float(name='polMotion', invalid='nan', help='polar proper motion (arcsec/year)'),
        Float(name='radVel', invalid='nan',
              help='radial velocity (km/sec, positive receding)'),
        String(name='coordSystem', invalid='?', help='coordinate system name'),
        Float(name='date', invalid='nan', help='coordinate system date'),
        Float(name='magnitude', invalid='nan', help='magnitude'),
        doCache=False,
        help='Information about a pointing reference star'),
    Key('ptRefPos',
        PVT(name='equatorial'),
        PVT(name='polar'),
        doCache=False,
        help='(deprecated; use ptRefStar instead) position of pointing '
             'reference star (equatorial PVT, polar PVT)'),
    Key('ptRefRadius',
        Float(invalid='nan', units='deg'), doCache=False, help='deprecated'),
    Key('ptScanSize',
        Float(invalid='nan', units='deg'), doCache=False, help='deprecated'),
    Key('received', String(), doCache=False,
        help='Text string read from a port. See also Expected.'),
    Key('rejectedAxisErrCode',
        String(name='az', invalid='?', help='azimuth'),
        String(name='alt', invalid='?', help='altitude'),
        String(name='rot', invalid='?', help='rotator'),
        doCache=False,
        help='Axis error codes for a move that was rejected. '
             'AxisErrCode would have had these values '
             'had the move been attempted, but the errors were too severe, '
             'so the move was rejected and the telescope was left doing '
             'whatever it was doing.'),
    Key('rotDTime', Float(invalid='nan', units='sec'),
        help='Approximate rotator controller clock time - TCC clock time. '
             'Warning: this has systematic error on the order of 0.1 seconds '
             'due to communication lag. It is primarily intended to indicate '
             'serious time discrepancies. Furthermore, some or '
             'all axes may show large error if any one axis controller '
             'delays the write or times out. To fix a time discrepancy, '
             'first set the TCC clock via the WWV clock (SET TIME), then '
             'set the controller clocks (AXIS INIT). has systematic error '
             'due to communication delays.'),
    Key('rotErr',
        Float(name='abs', invalid='nan', units='as',
              help='maximum absolute value'),
        Float(name='mean', invalid='nan', units='as',
              help='mean absolute value'),
        Float(name='std', invalid='nan', units='as',
              help='standard deviation absolute value'),
        doCache=False,
        help='Rotator servo error statistics: maximum absolute value, '
             'mean and standard deviation.'),
    Key('rotID',
        UInt(invalid='nan') * (1, 2),
        help='rotator ID (0 if no rotator); new TCC outputs one value, old TCC outputs two'),
    Key('rotInstXYAng',
        Float(name='x', invalid='nan', units='deg',
              help='x position in coordinate frame'),
        Float(name='y', invalid='nan', units='deg',
              help='y position in coordinate frame'),
        Float(name='rot', invalid='nan', units='deg',
              help='angle of instrument rotator x axis in coordinate frame.'),
        help='Position of the center of the instrument rotator in instrument coordinate frame.'),
    Key('rotLim',
        Float(name='min', invalid='nan', units='deg', help='minimum position'),
        Float(name='max', invalid='nan', units='deg', help='maximum position'),
        Float(name='speed', invalid='nan', units='deg/sec', help='maximum speed'),
        Float(name='acceler', invalid='nan',
              units='deg/sec^2', help='maximum acceleration'),
        Float(name='jerk', invalid='nan', units='deg/sec^3', help='maximum jerk'),
        help='Rotator motion limits used by the TCC (which are more '
             'restrictive than the limits used by the axis controller).'),
    Key('rotMount', PVT(), doCache=False,
        help='Angle of the instrument rotator in mount coordinates. See also TelMount.'),
    Key('rotOffsetScale',
        Float(name='units', invalid='nan', units='mount units'),
        Float(name='scale', invalid='nan', units='mount units/deg'),
        help='Parameters to transform instrument rotator physical angle '
             'to mount: mount = offset + (physical * scale). '
             'Thus the units of offset are mount units '
             '(typically but not necessarily degrees) '
             'and the units of scale are mount units/degrees.'),
    Key('rotPhys',
        PVT(), doCache=False,
        help='Angle of the instrument rotator in physical coordinates. See also TelPhys.'),
    Key('rotPos',
        PVT(),
        help='User-specifiec position of rotator.'),
    Key('rotReply',
        String(),
        help='Unparsed reply from the rotator axis controller'),
    Key('rotStat',
        Float(name='pos', invalid='nan', units='deg', help='position'),
        Float(name='vel', invalid='nan', units='deg/sec', help='velocity'),
        Float(name='time', invalid='nan', units='TAI (MJD, sec)', help='time'),
        UInt(name='status', invalid='nan', reprFmt='0x%x', help='status word'),
        help='Status reported by the axis controller.'),
    Key('rotTrackAdvTime',
        Int(name='sampl', invalid='nan', help='number of samples'),
        Float(name='min', invalid='nan', units='sec', help='minimum'),
        Float(name='max', invalid='nan', units='sec', help='maximum'),
        Float(name='mean', invalid='nan', units='sec', help='mean'),
        Float(name='std', invalid='nan', units='sec', help='standard deviation'),
        doCache=False,
        help='Statistics for how far in advance tracking updates '
             'are sent to the rotator controller'),
    Key('rotType', Enum('None', 'Obj', 'Horiz', 'Phys', 'Mount'),
        help='Mode (type of rotation) of instrument rotator. '
             'See TCC Commands: Rotate for more information.'),
    Key('rotWrapPref',
        Enum('None', 'Nearest', 'Negative', 'Middle', 'Positive', 'NoUnwrap'),
        doCache=False,
        help='Preferred wrap for the rotator axis.'),
    Key('scaleFac',
        Float(invalid='nan'),
        help='Current scale factor, defined as actual focal plate scale / nominal scale, '
             'where larger scale (and hence larger scale factor) gives higher resolution, '
             'e.g. more pixels/arcsec.'),
    Key('scaleFacRange',
        Float(name='min', invalid='nan', help='min'),
        Float(name='max', invalid='nan', help='max'),
        help='Allowed range of scale factor. Note: at present, '
             'the TCC only permits specifying a maximum scale factor; '
             'the minimum is computed from this as follows: minimum = 1/maximum.'),
    Key('secActMount',
        Float(units='microsteps', invalid='nan') * (1, 5),
        help='Actuator lengths determined from secEncMount and the mirror model. '
             'This may not match secCmdMount, even if the actuators move as commanded, '
             'due to systematic errors in the mirror model.'
             'For an actuator without an encoder, the commanded actuator mount is used. '),
    Key('secCmdMount',
        Float(invalid='nan') * (1, 5),
        help='commanded position of secondary mirror actuators', units='microsteps'),
    Key('secDesEncMount',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Desired encoder lengths, in actuator microsteps, based '
        'on secDesOrient and the mirror model. There is one entry per '
        'actuator, rather than per encoder: for an actuator without '
        'an encoder, the commanded actuator mount is used.'),
    Key('secEncMount',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Measured encoder lengths, in actuator microsteps, based '
             'on secDesOrient and the mirror model. There is one entry '
             'per actuator, rather than per encoder; for an actuator '
             'without an encoder, the commanded actuator mount is used.'),
    Key('secModelMount',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Actuator mount position determined from desOrient the the mirror model'),
    Key('secNetMountOffset',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Offset applied to a model mount at the beginning of a move, '
             'to prevent motion for a null move and speed up convergence '
             'for a small move. It primarily  compensates for systematic '
             'error in the mirror model.'),
    Key('secMountErr',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Error in mount position for a given iteration. '
             'Apply this delta to secCmdMount each iteration.'),
    Key('secDesOrient',
        Float(name='piston', invalid='nan', units='um', help='piston'),
        Float(name='xTilt', invalid='nan', units='as', help='x tilt'),
        Float(name='yTilt', invalid='nan', units='as', help='y tilt'),
        Float(name='xTransl', invalid='nan', units='um', help='x translation'),
        Float(name='yTransl', invalid='nan', units='um', help='y translation'),
        Float(name='rotation', invalid='nan', units='as',
              help='rotation about z (new TCC only)') * (0, 1),
        help='desired orientation of secondary mirror'),
    Key('secDesOrientAge',
        Float(invalid='nan', units='sec'), doCache=False,
        help='Time elapsed since this orient was commanded.'),
    Key('secOrient',
        Float(name='piston', invalid='nan', units='um', help='piston'),
        Float(name='xTilt', invalid='nan', units='as', help='x tilt'),
        Float(name='yTilt', invalid='nan', units='as', help='y tilt'),
        Float(name='xTransl', invalid='nan', units='um', help='x translation'),
        Float(name='yTransl', invalid='nan', units='um', help='y translation'),
        Float(name='rotation', invalid='nan', units='as',
              help='rotation about z (new TCC only)') * (0, 1),
        help='actual orientation of secondary mirror'),
    Key('secReply',
        String(),
        help='Unparsed reply from the secondary mirror controller'),
    Key('secState',
        String(name='state',
               help='State of galil device, one of: '
                    'Moving, Done, Homing, Failed, NotHomed'),
        UInt(name='iter', help='current iteration'),
        UInt(name='iterMax', help='max iterations'),
        Float(name='timeRemain',
              invalid='nan',
              units='seconds',
              help='remaining time on move or home'),
        Float(name='timeTotal',
              invalid='nan',
              units='seconds',
              help='total time for move or home'),
        help='summarizes current state of secondary galil and any '
             'remaning time or move iterations'),
    Key('secStatus',
        UInt(invalid='nan') * (1, 6),
        help='status word from the secondary mirror controller'),
    Key('secF_BFTemp',
        Float(name='front', invalid='nan', units='C', help='front temperature'),
        Float(name='diff', invalid='nan', units='C',
              help='front-back temperature difference')),
    Key('secFocus',
        Float(invalid='nan', units='um'),
        help='User-specified secondary mirror focus offset, '
             'as specified by the SET FOCUS command.'),
    Key('secTrussTemp',
        Float(invalid='nan', units='C'),
        help='Average temperature of the secondary truss elements. '
             'Used for automatic focus correction.'),
    Key('slewAdvTime',
        Float(invalid='nan', units='sec'),
        help='The amount of time in advance a slew was sent, '
             'in seconds. For safety, this must be less '
             'than Tune.MaxClockErr (and if it is not, SlewAdvTime will '
             'be part of a warning message). The advance time of a slew '
             'segment is the time at which the segment was sent to the axis '
             'controller minus the end time of the segment. The reported '
             'SlewAdvTime is the minimum advance time of all segments of all axes.'),
    Key('slewBeg',
        Double(invalid='nan', units='sec',
               help='correct, exact, and reliable time of the end of the slew'),
        doCache=False,
        help='Indicates that a slew has begun.'),
    Key('slewDuration',
        Float(invalid='nan', units='sec'),
        doCache=False, help='Indicates the duration of a slew.'),
    Key('slewEnd',
        help='Indicates the end of a slew.'),
    Key('slewNumIter',
        Int(),
        help='number of iterations for slew computation'),
    Key('slewSuperseded',
        help='Indicates that a slew was aborted to make way for another slew.'),
    Key('spiderInstAng',
        PVT(),
        help='Orientation of secondary spider on the instrument. '
             'Specifically, it is the angle from the instrument x axis '
             'to the secondary spider x axis, where the secondary spider '
             'x axis is the direction of increasing azimuth when the telescope '
             'is at the horizon. (Formerly AzInstAng, approximately).'),
    Key('stInterval',
        Float(invalid='nan', units='sec') * (2, 3),
        doCache=False,
        help='Interval between automatic status updates while tracking and '
             'while slewing. The intervals are in decimal seconds.'),
    Key('started',
        help='Background command started. Warning: not reliably output '
             'and not intended for automated use; please use the command '
             'status instead.'),
    Key('superseded',
        help='Background command superseded by another command.'),
    Key('tLapse',
        Float(invalid='nan', units='C/km')),
    Key('tai',
        Double(invalid='nan', units='sec'),
        refreshCmd='show time',
        help='International atomic time (TAI), in MJD seconds.'),
    Key('tccDTime',
        Float(invalid='nan', units='sec'),
        doCache=False,
        help='TCC clock adjustment, in seconds; new time = old time + TCCDTime. '
             'The TCC clock should only be adjusted when it is recalibrated to '
             'the radio clock, in which case TCCDTime indicates the clock error '
             'just before adjustment. The error should never exceed a few tenths '
             'of a second else the axis controller clocks may get mis-set.'),
    Key('tccPos',
        Float(name='az', invalid='nan', units='deg', strFmt='%+07.2f', help='azimuth'),
        Float(name='alt', invalid='nan', units='deg',
              strFmt='%+07.2f', help='altitude'),
        Float(name='rot', invalid='nan', units='deg', strFmt='%+07.2f', help='rotator'),
        help='The desired mount position as computed by the TCC. '
             'Not many digits past the decimal but very useful for status displays. '
             'Axes that are halted or not available are listed as \'nan\'. '
             'The state of the axes is given by AxisCmdState. See also AxePos. '
             'During a slew TCCPos gives the end position of the slew, '
             'not the current predicted position.'),
    Key('telMount',
        PVT(name='az'),
        PVT(name='alt'), doCache=False,
        help='Position of the telescope azimuth and altitude axes, '
             'in mount coordinates. See also RotMount'),
    Key('tertActMount',
        Float(units='microsteps', invalid='nan') * (1, 3),
        help='Actuator lengths determined from tertEncMount and the mirror model. '
             'This may not match tertCmdMount, even if the actuators move as commanded, '
             'due to systematic errors in the mirror model.'
             'For an actuator without an encoder, the commanded actuator mount is used. '),
    Key('tertCmdMount',
        Float(invalid='nan') * (1, 3),
        help='commanded position of tertiary mirror actuators', units='microsteps'),
    Key('tertDesEncMount',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Desired encoder lengths, in actuator microsteps, based on '
             'tertDesOrient and the mirror model. There is one entry per actuator, '
             'rather than per encoder: for an actuator without an encoder, '
             'the commanded actuator mount is used.'),
    Key('tertEncMount',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Measured encoder lengths, in actuator microsteps, based on '
             'tertDesOrient and the mirror model. There is one entry per '
             'actuator, rather than per encoder; for an actuator without '
             'an encoder, the commanded actuator mount is used.'),
    Key('tertModelMount',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Actuator mount position determined from desOrient the the mirror model'),
    Key('tertNetMountOffset',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Offset applied to a model mount at the beginning of a move, '
             'to prevent motion for a null move and speed up convergence for '
             'a small move. It primarily  compensates for systematic error '
             'in the mirror model.'),
    Key('tertMountErr',
        Float(units='microsteps', invalid='nan') * (3, 6),
        help='Error in mount position for a given iteration. '
             'Apply this delta to tertCmdMount each iteration.'),
    Key('tertDesOrient',
        Float(name='piston', invalid='nan', units='um', help='piston'),
        Float(name='xTilt', invalid='nan', units='as', help='x tilt'),
        Float(name='yTilt', invalid='nan', units='as', help='y tilt'),
        Float(name='xTransl', invalid='nan', units='um', help='x translation'),
        Float(name='yTransl', invalid='nan', units='um', help='y translation'),
        Float(name='rotation', invalid='nan', units='as',
              help='rotation about z (new TCC only)') * (0, 1),
        help='desired orientation of tertiary mirror'),
    Key('tertDesOrientAge', Float(invalid='nan', units='sec'),
        doCache=False, help='Time elapsed since this orient was commanded.'),
    Key('tertOrient',
        Float(name='piston', invalid='nan', units='um', help='piston'),
        Float(name='xTilt', invalid='nan', units='as', help='x tilt'),
        Float(name='yTilt', invalid='nan', units='as', help='y tilt'),
        Float(name='xTransl', invalid='nan', units='um', help='x translation'),
        Float(name='yTransl', invalid='nan', units='um', help='y translation'),
        Float(name='rotation', invalid='nan', units='as',
              help='rotation about z (new TCC only)') * (0, 1),
        help='actual orientation of tertiary mirror'),
    Key('tertReply', String(),
        help='Unparsed reply from the tertiary mirror controller'),
    Key('tertState',
        String(
            name='state',
            help='State of galil device, one of: '
                 'Moving, Done, Homing, Failed, NotHomed'),
        UInt(name='iter', help='current iteration'),
        UInt(name='iterMax', help='max iterations'),
        Float(
            name='timeRemain',
            invalid='nan',
            units='seconds',
            help='remaining time on move or home'),
        Float(
            name='timeTotal',
            invalid='nan',
            units='seconds',
            help='total time for move or home'),
        help='summarizes current state of tertiary galil and any '
             'remaning time or move iterations'),
    Key('tertStatus',
        UInt(invalid='nan') * (1, 6),
        help='status word from the tertiary mirror controller'),
    Key('text',
        String(), doCache=False,
        help='Explanatory text for a message.'),
    Key('timeStamp',
        Double(invalid='nan', units='sec'),
        doCache=False,
        help='Timestamp of associated data.'),
    Key('trackAdvTime', Float(invalid='nan', units='sec'), doCache=False,
        help='A tracking update occurred. In other words, a new position, '
             'velocity, time triplet was issued to one or more axis controllers. '
             'The value is the number of seconds in advance that the update '
             'occurred before the previous pvt triplets expired. Too small a value '
             'triggers a warning and suggests that you may need to modify the '
             'tuning parameters.'),
    Key('useCheby', Bool('F', 'T'),
        help='If T then the track an object whose position is specified using '
             'Chebyshev polynomial coefficients. See also ChebyFile, '
             'ChebyCoeffsUser1, ChebyCoeffsUser2, ChebyCoeffsDist and ChebyBegEndTime. '
             'If F then the other Chebyshev keywords are meaningless and should be ignored.'),
    Key('userAdded',
        help='The associated user (indicated by UserNum) '
             'has started running the TCC software.'),
    Key('userDeleted',
        help='The associated user (indicated by UserNum) has stopped '
             'running the TCC software.'),
    Key('userInfo',
        UInt(name='id', invalid='nan', help='user ID'),
        String(name='IPs') * (1, 4),
        help='Information about one user; new tcc outputs 2 values, '
             '2nd is user\'s IP address; old TCC outputs 4 values, '
             'see docs for details'),
    Key('userNum',
        UInt(invalid='nan'),
        help='User ID number. Each user has a unique user ID number '
             'which is used to tag commands initiated by that user. '
             'UserNum generally appears with other data such as UserAdded '
             'or UserDeleted. See also YourUserNum.'),
    Key('ut1',
        Double(invalid='nan', units='sec'),
        help='Universal time (UT1), in MJD seconds.'),
    Key('utc_TAI',
        Float(invalid='nan', units='sec'),
        help='The time difference: UTC - TAI, in seconds.'),
    Key('version',
        String(),
        help='TCC software version.'),
    Key('warnAltStatus',
        help='Indicates that a possibly bad bit is set in the altitude '
             'controller\'s status word. See also AxisWarnStatusMask '
             'and Bad<AxisName>Status.'),
    Key('warnAzStatus',
        help='Indicates that a possibly bad bit is set in the azimuth '
             'controller\'s status word. See also AxisWarnStatusMask '
             'and Bad<AxisName>Status.'),
    Key('warnRotStatus',
        help='Indicates that a possibly bad bit is set in the rotator '
             'controller\'s status word. See also AxisWarnStatusMask '
             'and Bad<AxisName>Status.'),
    Key('windDir',
        Float(invalid='nan', units='deg'),
        help='Outside wind direction (degrees, south = 0, east = 90).'),
    Key('windSpeed',
        Float(invalid='nan', units='m/sec'),
        help='Outside wind speed (m/s).'),
    Key('yourUserID',
        UInt(),
        help='Your user ID (use to identify messages meant for you); new TCC only'),
    Key('yourUserNum',
        UInt(),
        help='Synonym for yourUserID; deprecated for new TCC but required for old TCC'),

    # keywords not output by the new tcc that perhaps should be added
    # Key('altMSStat', Float(invalid='nan', units='as')*2, String()),
    # Key('azMSStat', Float(invalid='nan', units='as')*2, String()),
    # Key('rotMSStat', Float(invalid='nan', units='as')*2, String()),
    # Key('azAltDist', Float(units='degrees', invalid='nan'), doCache=False,
    #     help='The distance in azimuth or altitude (whichever is greater)'
    #          'from the pointing reference star to your object.'),
    # Key('spiderGImAng', PVT(), doCache=False),
    # Key('tdiCorr', Bool('F', 'T'),
    #     help='If T then the associated ObjArcOff is being rate-corrected for '
    #          'TDI (drift scanning). This correction adjusts the rate of the '
    #          'telescope along the scanning great circle for the'
    #          'effects of refraction, so that the instrument can be read '
    #          'out at a constant rate.'),
)
