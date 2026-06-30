#=============== detectors: a library of detector functions (location and antenna patterns) ===============#
# This code is a part of the PyStoch Package.
# authors: Anirban Ain (anirban.ain@ligo.org), Jishnu Suresh (jishnu.suresh@ligo.org),
# Sudhagar Suyamprakasam (sudhagar.suyamprakasam@ligo.org) and Sanjit Mitra (sanjit.mitra@ligo.org)
#------------------------------------------------------------------------------------------------------------

import sys
import numpy as np
import healpy as hp
from numpy import sin as SIN
from numpy import cos as COS
from numpy import array as ARRAY
from astropy.time import Time
from astropy.units.si import sday

#------------------------------------------------------------------------------------------------------------

# Speed of light in vacuum, m s^-1
C_SI = 299792458e0

def gmst_calculate(gps_time):
    """
    Convert Global Positioning System Time (GPST) to Greenwich Median
    Sidereal Time (GMST)

    GMST is calculated from astropy modules.
    Default GMST model is the latest IAU GMST precision model (IAU2006). 
    Default conversion scale from GPST is UT1.

    Parameters
    ----------
    gpsTime: float
             Global Positioning System Time

    Returns
    -------
    gmstw: float
           Greenwich Median Sidereal Time in radian
    """

    ### FIXME: Should be an option to choose GMST model in parameter.ini ###

    ## GMST Reference Time
    #reference_time =    630763213 #1126259462

    ##gmst_reference = gpstogmst(reference_time)
    #gmst_reference = Time(reference_time, format='gps',location=(0, 0)).sidereal_time('mean').rad

    ## Sideral Time
    #sday1 = float(sday.si.scale)

    ## Difference in phase
    #dphase = (gps_time - reference_time) / sday1 * (2.0 * np.pi)

    ## Greenwich Median Sideral Time (GMST)
    #gmst_estimate = (gmst_reference + dphase) % (2.0 * np.pi)

    # Matching matapps/packages/stochastic/trunk/Utilities/GPStoGreenwichMeanSiderealTime.m
    #wearth = 2.0*np.pi * (1/365.2425 +1) / 86400.0
    #same thing in hours / sec
    #w=wearth/pi*12

    # Earth's angular speed
    wearth = 7.292115838261945e-05

    # GPS time for 1/1/2000 00:00:00 UTC
    GPS2000 = 630720013.0

    #sidereal time at GPS2000,in rad
    # from http://www.csgnetwork.com/siderealjuliantimecalc.html
    #sT0=6+39/60+51.251406103947375/3600
    #sT0 = (6.0+39.0/60.0+51.251406103947375/3600.0) * np.pi/12.0
    sT0 = 1.7446930362926378

    gmst_estimate = wearth * (gps_time - GPS2000) + sT0;

    return gmst_estimate

def gwdetectors(detector):
    """
    Location and response matrix data for the specified
    gravitational wave detectors

    References
    ----------
    https://dcc.ligo.org/public/0072/P000006/000/P000006-D.pdf

    https://journals.aps.org/prd/pdf/10.1103/PhysRevD.63.042003

    Parameters
    ----------
    detector: string
              Gravitational wave detector name
              Valid detector name string
              ["GEO", "G1", "G", "LHO", "H1", "H2", "H",
              "LLO", "L1", "L", "VIRGO", "V1", "V", "KAGRA", "K1", "LIGO-INDIA", "LIO", "I1"]

    Returns
    -------
    detector_location: numpy array
                       Detector location data corresponding to the speed of
                       light travel time from the center of the Earth.

    detector_response: numpy array
                       Detector response matrices are dimensionless.
    """

    # GEO600 detector
    if bool(set([detector]).issubset(set(["GEO", "G1", "G"]))):
        g_location = ARRAY([+3856309.94926000, +666598.95631699,
                            +5019641.41724999], dtype='float64')

        g_response = ARRAY([-0.096824981272, -0.365782320499, 0.122137293220,
                           -0.365782320499, 0.222968116403, 0.249717414379,
                           0.122137293220, 0.249717414379, -0.126143142581],
                           dtype='float64')

        GEO = {'Detector Name': detector, 'Response': g_response,
               'Location': g_location}

        return GEO

    # LIGO Hanford 2k and 4km detectors
    if bool(set([detector]).issubset(set(["LHO", "H1", "H2", "H"]))):
        h_location = ARRAY([-2161414.92635999, -3834695.17889000,
                            4600350.22664000], dtype='float64')

        h_response = ARRAY([-0.392614096403, -0.077613413334, -0.247389048338,
                           -0.077613413334, 0.319524079561, 0.227997839451,
                           -0.247389048338, 0.227997839451, 0.073090031743],
                           dtype='float64')

        LHO = {'Detector Name': detector, 'Response': h_response,
               'Location': h_location}

        return LHO

    # LIGO Livingston 2k detector
    if bool(set([detector]).issubset(set(["LLO", "L1", "L"]))):
        l_location = ARRAY([-74276.04472380, -5496283.71970999,
                            3224257.01744000], dtype='float64')

        l_response = ARRAY([0.411280870438, 0.140210270882, 0.247294589877,
                           0.140210270882, -0.109005689621, -0.181615635753,
                           0.247294589877, -0.181615635753, -0.302275151014],
                           dtype='float64')

        LLO = {'Detector Name': detector, 'Response': l_response,
               'Location': l_location}

        return LLO

    # Virgo detector
    if bool(set([detector]).issubset(set(["VIRGO", "V1", "V"]))):
        v_location = ARRAY([4546374.09900000, 842989.69762600,
                            4378576.96241000], dtype='float64')

        v_response = ARRAY([0.243874043226, -0.099083781242, -0.232576221228,
                           -0.099083781242, -0.447825849056, 0.187833100557,
                           -0.232576221228, 0.187833100557, 0.203951805830],
                           dtype='float64')

        VIRGO = {'Detector Name': detector, 'Response': v_response,
                 'Location': v_location}

        return VIRGO



    # KAGRA detector
    if bool(set([detector]).issubset(set(["KAGRA", "K1"]))):
        v_location = ARRAY([-3777336.024,  3484898.411,  3765313.697],dtype='float32')

        v_response = ARRAY([-0.18598965,  0.1531668 , -0.32495147,
                            0.1531668 ,  0.3495183 , -0.1708744,
                            -0.32495147, -0.1708744 , -0.16352864], dtype='float32')

        KAGRA = {'Detector Name': detector, 'Response': v_response,
                 'Location': v_location}

        return KAGRA


    # LIGO-INDIA detector
    if bool(set([detector]).issubset(set(["LIGO-INDIA","LIO", "I1"]))):
        v_location = ARRAY([1450526.82294155, 6011058.39047265, 1558018.27884102], dtype='float32')
        
        v_response = ARRAY([0.47082368, -0.12090825,  0.0279526,
                            -0.12090825, -0.00105003, 0.11583696,
                            0.0279526 ,  0.11583696, -0.46977365],dtype='float32')

        LIO = {'Detector Name': detector, 'Response': v_response,
                 'Location': v_location}

        return LIO


    else:
        detector_list = ["GEO", "G1", "G", "LHO", "H1", "H2", "H",
                         "LLO", "L1", "L", "VIRGO", "V1", "V", "KAGRA", "K1", "LIGO-INDIA", "LIO", "I1"]

        print("      !---- Detector name should be from the list")

        print("           ", detector_list)

        sys.exit()

def ehat(phi, theta):
    """
    Cartesian source direction

    Parameters
    ----------
    phi: float
         Range = [0, 2 pi)

    theta: float
           Range = [0, pi]

    Returns
    -------
    ehat_src: numpy array
              Source direction
    """

    COStheta = COS(theta)
    SINtheta = SIN(theta)
    COSphi   = COS(phi)
    SINphi   = SIN(phi)


    ehat_x =  COSphi * COStheta
    ehat_y = -SINphi * COStheta
    ehat_z =  SINtheta
    ehat_src = np.array([ehat_x, ehat_y, ehat_z], dtype=object)

    return ehat_src

intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
    )

def display_time(seconds, granularity=2):
    """
    FIXME: Function used to display the time
    """
    result = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])

def arrival_time(detNAME, gpsTIME, phi, theta):
    """
    Arrival time of Gravitational Wave at the detector with respect to a given
    GPS time, right ascension, and declination.

    The velocity of light in vacuum
    C_SI  = 299792458e0    m s^-1

    Parameters
    ----------
    detNAME: string
             Gravitational Wave detector name

             Valid detector name string
              ["GEO", "G1", "G", "LHO", "H1", "H2", "H",
              "LLO", "L1", "L", "VIRGO", "V1", "V", "KAGRA", "K1", "LIGO-INDIA", "LIO", "I1"]

    gpsTIME: float or int
             Global Positioning System Time.

    phi: float
         Range = [0, 2 pi)
         The right ascension angle (in rad) of the signal.

    theta: float
           Range = [0, pi]
           The declination angle (in rad) of the signal

    Returns
    -------
    tarrival: float
              Time of arrival at the detector
    """

    # Right ascension
    ra = gmst_calculate(gpsTIME) - phi

    # Declination
    dec = (np.pi/2) - theta

    # Time of arrival
    tarrival = np.dot(ehat(ra, dec), gwdetectors(detNAME)['Location']) / C_SI

    return tarrival

def combined_antenna_response_t_delay(*args, GW_polarization="T"):
    """
    Combined antenna response and the time delay between two Gravitational wave
    detectors in the given GPS time

    Parameters
    ----------
    *args:  Variable length argument list.
            ifo1: string
                  The First interferometer name.

            ifo2: string
                  The Second interferometer name.

            gpstARRAY: array-like
                       Global Positioning System Time.

            phi: list or array-like
                 Range = [0, 2 pi)
                 The right ascension angle (in rad) of the signal.

            theta: list or array-like
                   Range = [0, pi]
                   The declination angle (in rad) of the signal

            psi: list or array-like
                 Range = [0, pi)
                 The polarization angle (in rad) of the source.

            GW_polarization: string
                Gravitational Wave Polarization
                Default value: T for Tensor.
                values: T for Tensor, S for Scalar, and V for Vector

    Returns
    -------
    combined_response: array-like
                       Combined Antenna Response FPlus and FCross (for Tensor),
                       Fb and Fl (for Scalar), and Fx and Fy (for Vector)
                       from the two Gravitational wave  detectors

    time_delay: array-like
                The time delay between two Gravitational wave detectors.
    """

    # Condition for single process analysis
    if len(args) == 5:
        ifo1, ifo2, gpsTIME, phi, theta = args
        psi = 0
    if len(args) == 6:
        ifo1, ifo2, gpsTIME, phi, theta, psi = args

    # Right ascension
    gha = gmst_calculate(gpsTIME) - phi

    # Declination
    #dec = (np.pi/2) - theta


    SINgha = SIN(gha)
    COSgha = COS(gha)

    SINtheta = SIN(theta)
    COStheta = COS(theta)


    # Unit vectors (when psi is non zero)
    #m1 = -COSpsi * SINgha - SINpsi * COSgha * SINdec
    #m2 = -COSpsi * COSgha + SINpsi * SINgha * SINdec
    #m3 = SINpsi * COSdec

    m1 = -SINgha
    m2 = -COSgha
    m3 =  0.0
    m123 = ARRAY([m1, m2, m3], dtype=object)

    # when psi is non zero
    #n1 = SINpsi * SINgha - COSpsi * COSgha * SINdec
    #n2 = SINpsi * COSgha + COSpsi * SINgha * SINdec
    #n3 = COSpsi * COSdec

    # Allen Romano
    #n1 =  COSgha * COStheta
    #n2 = -SINgha * COStheta
    #n3 = -SINtheta

    n1 = -COSgha * COStheta
    n2 =  SINgha * COStheta
    n3 =  SINtheta
    n123 = ARRAY([n1, n2, n3], dtype=object)

    #Following Nishizawa et. al. arXiv:0903.0528 & Romano Living Review

    l1 = -COSgha * SINtheta
    l2 =  SINgha * SINtheta
    l3 =  -COStheta
    l123 = ARRAY([l1, l2, l3], dtype=object)


    if GW_polarization == "T": # Source direction - Plus (+) and Cross (x) --> tensor-type (spin-2) GWs

        # Combined response plus
        # eplus = mm - nn
        eplus = np.tensordot(m123, m123, axes=0).flatten() - np.tensordot(n123, n123, axes=0).flatten()
        combined_response = np.dot(eplus, gwdetectors(ifo1)['Response']) * np.dot(eplus, gwdetectors(ifo2)['Response'])
        eplus = None

        # Combined response cross
        # ecross = mn + nm
        ecross = np.tensordot(m123, n123, axes=0).flatten() + np.tensordot(n123, m123, axes=0).flatten()
        combined_response = combined_response + np.dot(ecross, gwdetectors(ifo1)['Response']) * np.dot(ecross, gwdetectors(ifo2)['Response'])
        ecross = None

#    elif GW_polarization == "S": # Source direction - Breathing (B) and Longitudinal (L) --> scalar-type (spin-0) GWs
#
#        # Combined response B
#        # eB = mm + nn
#        eB = np.tensordot(m123, m123, axes=0).flatten() + np.tensordot(n123, n123, axes=0).flatten()
#        combined_response = np.dot(eB, gwdetectors(ifo1)['Response']) * np.dot(eB, gwdetectors(ifo2)['Response'])
#        eB = None
#
#        # Combined response L
#        # eL = sqrt(2) ll
#        eL = np.sqrt(2) * np.tensordot(l123, l123, axes=0).flatten()
#        combined_response = combined_response + np.dot(eL, gwdetectors(ifo1)['Response']) * np.dot(eL, gwdetectors(ifo2)['Response'])
#        eL = None
#
#    elif GW_polarization == "V": # Source direction - X and Y --> vector-type (spin-1) GWs
#
#        # Combined response X
#        # eX = ml +lm
#        eX = np.tensordot(m123, l123, axes=0).flatten() + np.tensordot(l123, m123, axes=0).flatten()
#        combined_response = np.dot(eX, gwdetectors(ifo1)['Response']) * np.dot(eX, gwdetectors(ifo2)['Response'])
#        eX = None
#
#        # Combined response Y
#        # eY = nl + ln
#        eY = np.tensordot(n123, l123, axes=0).flatten() + np.tensordot(l123, n123, axes=0).flatten()
#        combined_response = combined_response + np.dot(eY, gwdetectors(ifo1)['Response']) * np.dot(eY, gwdetectors(ifo2)['Response'])
#        eY = None

    else:
        print('Acceptable values of Polarization are: T = Tensor (default), S = Scalar, V = Vector')
        sys.exit('Error: unknown polarization')

    time_delay = arrival_time(ifo2, gpsTIME, phi, theta) - arrival_time(ifo1, gpsTIME, phi, theta)

    return np.squeeze(combined_response), np.squeeze(time_delay)
