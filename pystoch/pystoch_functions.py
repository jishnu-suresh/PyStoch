import healpy as hp
import numpy as np
from scipy import interpolate
import sys
import time
import h5py

# From PyStoch
from pystoch.detectors import combined_antenna_response_t_delay

# text color formatting
BOLD = '\033[1m' #Bold text
TGREEN =  '\033[32m' # Green Text
TRED = '\033[31m' # Red Text
TCYAN = '\033[36m' # Cyan text
TYELLOW = '\033[33m' # Yellow Text
ENDC = '\033[m' # reset to the defaults


def ascii_art():
    print("  ____        ____  _             _     ")
    print(" |  _ \ _   _/ ___|| |_ ___   ___| |__  ")
    print(" | |_) | | | \___ \| __/ _ \ / __| '_ \ ")
    print(" |  __/| |_| |___) | || (_) | (__| | | |")
    print(" |_|    \__, |____/ \__\___/ \___|_| |_|")
    print("        |___/                           ")
    print(f"\n{BOLD+TCYAN}Stochastic Gravitational-Wave Background Map-making Pipeline{ENDC}")
    print()

# Spectral index H(f)
# Keep the H(f) data loaded once and for all
# Call this function only once in the code; otherwise it will read the file everytime
def spectral_index (freq,Hf_data):
    ''' Linear interpolation '''

    H_f = interpolate.interp1d(np.log(Hf_data[:,0]), np.log(Hf_data[:,1]))
    H = np.exp(H_f(np.log(freq)))
    return H

def calculate_t_delay_antenna_response_maps(frame_param,parameters,tt):
    ''' Calculates the seed matrices for Overlap Reduction Function '''

    print ('Calculating ORF seed maps for time {:12.2f}. '.format(float(tt)))
    sys.stdout.write("\033[F")
    # If nbr is true, only compute pixtheta and pixphi for the given pixel or direction.
    if parameters.nbr:
        pixtheta, pixphi = hp.pix2ang(256, hp.ang2pix(256, (parameters.raHr*15), parameters.decDeg, lonlat=True))
    else:
        pixtheta, pixphi = hp.pix2ang(parameters.nside, np.arange(hp.nside2npix(parameters.nside)))

    combined_antenna_resp, t_delay = combined_antenna_response_t_delay(frame_param.ifo1, frame_param.ifo2, np.array([[tt]]), pixphi, pixtheta, GW_polarization = parameters.GW_polarization)

    # These two matrices are the seed matrices for the given GPStime
    return t_delay, combined_antenna_resp

def load_frame_data(parameters,frame_param,dataset):
    ''' Function to load CSD and PSD (inv sigma2) and frequency and time Information. '''

    # Time and frequency mesh (series) of the CSD and PSD
    f_data = np.arange(frame_param.flow, frame_param.fhigh+frame_param.deltaF/2.0, frame_param.deltaF)

    # This string is the first part of a channel name (H1L1, V1L1, etc.)
    baseline = frame_param.ifo1 + frame_param.ifo2

    # File name: the file where the data will be stored in hdf5 format (using convert_frames.py)
    frame_data_name = frame_param.path + '/' + baseline + '_compressed'  +'.hdf5'
    # Check if the tmp file exists; if yes, load CSD and PSD from there
    try:
        print(f'Loading Frame data for {parameters.f_min} Hz to {parameters.f_max} Hz from following file.')
        print (frame_data_name)
        with h5py.File(frame_data_name, "r") as frames_preloaded:
            # If the previous action does not fail, then the file exists. Now loading CSD, and PSD
            csd_data = frames_preloaded['csd'][:]
            sigma_sq_inv_data = frames_preloaded['sigma_sq_inv'][:]
            GPSmid = frames_preloaded['gps_times_mid'][:]
    except FileNotFoundError:
        print(f'No data found for frameset {dataset}')


    # Creating an array for the frequencies that will be processed. Trimming the CSD and PSD according to the frequency range
    f_all = []
    csd = []
    sigma_sq_inv = []
    for ii,f in enumerate(f_data):
        if f >= parameters.f_min and f <= parameters.f_max:
            f_all.append(f)
            csd.append(list(csd_data[:,ii]))
            sigma_sq_inv.append(list(sigma_sq_inv_data[:,ii]))

    return GPSmid,f_all,csd,sigma_sq_inv

def seed_matrices(GPSmid,parameters,frame_param,dataset):
    ''' Function to calculate the seed seed_matrices
    time series for which ORF seeds are to be calculated.'''

    start = time.time()
    print ('Calculating ORF seeds for {} time segments (from {:12.2f} to {:12.2f}).'.format(GPSmid.size,float(GPSmid[0]),float(GPSmid[-1])))

    t_delay = []
    combined_antenna_response = []
    # Looping over all GPS times
    for tt in GPSmid:
        t_delay_tt, combined_antenna_response_tt = calculate_t_delay_antenna_response_maps(frame_param,parameters,tt)
        t_delay.append(t_delay_tt)
        combined_antenna_response.append(combined_antenna_response_tt)
    t_delay = np.array(t_delay)
    combined_antenna_response = np.array(combined_antenna_response)

    return t_delay, combined_antenna_response

def complex_getlm(l_max):
    ''' Creates a list of l and m in the order they appear in a a_lm array.
    Replacement for hp.Alm.getlm. Now we are including -m contribution'''

    lvec, mvec = [], []
    for mm in range(l_max+1):
        lvec += range(mm, l_max+1)
        mvec += [mm]*(l_max+1-mm)
    lvec = np.hstack((np.flipud(lvec[1+l_max:]), lvec))
    mvec = np.hstack((-np.flipud(mvec[1+l_max:]), mvec))
    q = (l_max+1)**2
    return (np.array(lvec.tolist()+mvec.tolist())).reshape(2,q)

def complex_map2alm(m,lmax):
    ''' Converts a HealPix pixel map to Spherical harmonic a_lm.
        Replacement for hp.map2alm.  Now we do not ignore complex input. The output contains -m  contributions'''

    map_real = np.real(m)
    map_imag = np.imag(m)

    alm_real = hp.map2alm(map_real,lmax)
    alm_imag = hp.map2alm(map_imag,lmax)

    alm = []

    l_all = complex_getlm(lmax)[0]
    m_all = complex_getlm(lmax)[1]

    for ll,mm in zip(l_all,m_all):
        ii = hp.Alm.getidx(lmax,ll,abs(mm))
        if mm < 0:
            alm.append((1-2*(mm%2)) * np.conj((alm_real[ii] - (1j * alm_imag[ii]))))
        else:
            alm.append(alm_real[ii] + (1j * alm_imag[ii]))
    return alm

def part_alm(alm):
    '''Parts/separates a given set of a_lm into the sum of two a_lm s
    which corresponds to a purely real and purely imaginary map.'''

    lmax=int(np.sqrt(np.size(alm))-1)
    minus_m = int((lmax*(lmax+1))/2)

    c1 = alm[:minus_m]
    c2 = alm[minus_m:minus_m+lmax+1]
    c3 = alm[minus_m+lmax+1:]

    mm = complex_getlm(lmax)[1][:minus_m]
    d = 1- 2*(mm%2)
    cc1 = np.flip(np.conj(c1)*d)

    alm_real = np.concatenate([np.flip(np.conj(0.5*(c3+cc1)))*d,np.real(c2),(0.5*(c3+cc1))])
    alm_imag = alm-alm_real

    return alm_real,alm_imag

def fisher_zeros(fisher):
    '''If l+l' is odd,  make the Fisher matrix elements to be zero'''

    lmax=int(np.sqrt(np.shape(fisher)[1])-1)
    a=complex_getlm(lmax)[0]
    b = np.transpose([a])
    c = np.tile(a,(np.size(a),1)) + np.tile(b,(1,np.size(b)))
    d = 1 - c%2
    fisher = fisher*d
    return fisher

# Notching functions to use the pygwb notchlist as the input
#FIXME: Make this function as the deafult one, once the notchlist format is finalized!
def make_notch_array(frequency_array, notching, notch_list):
    '''Returns an array having the same size as the frequency list.
    The elements corresponding to a notched frequency are False, rest are True.
    This version of the code support the pygwb options'''

    f_min = frequency_array[0]
    f_max = frequency_array[-1]
    deltaf = frequency_array[1] - frequency_array[0]
    numFreqs = np.size(frequency_array)
    notching_array = np.ones(np.size(frequency_array), dtype=bool)

    if notching:
        # Load the notching list file
        fmin, fmax = np.loadtxt(notch_list, delimiter=",", unpack=True, usecols=(0, 1))

        # Handle the case where only one notching range is provided
        if isinstance(fmin, np.float64):
            fmin, fmax, desc = [fmin], [fmax], [desc]

        # Calculate the boundaries of each frequency bin
        df = np.abs(frequency_array[1] - frequency_array[0])
        frequencies_below = np.concatenate([frequency_array[:1] - df, frequency_array[:-1]])
        frequencies_above = np.concatenate([frequency_array[1:], frequency_array[-1:] + df])

        # Update the mask for each notching range
        for f_start, f_end in zip(fmin, fmax):
            # Check if the notch frequencies are within the range of f_all
            if f_start < f_min or f_end > f_max:
                #print(f"Warning: Notch from {f_start} to {f_end} is outside the range of the frequency array. Skipping this notch.")
                continue
            
            # Determine which frequency bins are within the notching range
            lower = frequencies_below + df / 2 <= f_end
            upper = frequencies_above - df / 2 >= f_start
            notch_mask = [not elem for elem in (lower & upper)]

            # Apply the notch
            notching_array = notching_array & notch_mask

    return notching_array
