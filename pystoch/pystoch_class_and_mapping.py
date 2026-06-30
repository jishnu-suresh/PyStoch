import healpy as hp
import numpy as np
from numpy import exp
import sys, os
import configparser
import time
from tqdm import tqdm
from astropy.units.si import sday

# From PyStoch
from pystoch.pystoch_functions import (
    ENDC,
    TCYAN,
    TRED,
    complex_getlm,
    complex_map2alm,
    fisher_zeros,
    load_frame_data,
    make_notch_array,
    part_alm,
    seed_matrices,
    spectral_index,
)

class PystochParam:
    '''Class to pack all the PyStoch parameters.
     Initialized by location of the parameter file.'''
    def __init__(self,param_file,override_params=None,info_logger=None):
        param = configparser.ConfigParser()
        param.read(param_file)
        
        self.nside = param.getint('parameters','nside',fallback=None) # help = 'HEALPix nside parameter (power of 2)'
        self.f_min = param.getfloat('parameters','f_min',fallback=20.0) #help='Minimum of the frequency range for which maps will be calculated (default: 20Hz)'
        self.f_max = param.getfloat('parameters','f_max',fallback=None) #help='Maximum of the frequency range for which maps will be calculated'
        self.notching = param.getboolean('parameters','notching',fallback=False) #help='Enable frequency notching (default: False)'
        self.notch_list = param.get('parameters', 'notch_list',fallback=None)#help='Text file with list of notch frequencies')
        self.pixel = param.getboolean('parameters','pixel',fallback=None) #help='Select pixel basis for PyStoch mapping')
        self.sph = param.getboolean('parameters','sph',fallback=None) #help='Select SpH basis for PyStoch mapping')
        self.lmax = param.getint('parameters', 'lmax',fallback=None) #help='Maximum value of ell (default: 2 * nside)'
        self.beam =  param.getboolean('parameters','beam', fallback=False) #help='Compute the broadband beam matrix (default: False')
        self.output_map_path = param.get('parameters','output_map_location',fallback=None) #help='Output path where all the results will be saved'
        self.multi_thread = param.getboolean('parameters','multithreading',fallback=True) #help='Use multithreading (default: True)'
        self.n_thread = param.getint('parameters','multi_threads',fallback=4) #help='Number of threads for multithreading (default: 4)'
        self.nbr = param.getboolean('parameters', 'nbr', fallback = False) #help='Perform the NBR analysis (default: False)'
        self.raHr = param.getfloat('parameters','raHr', fallback=None)
        self.decDeg = param.getfloat('parameters','decDeg', fallback=None)
        self.direction = param.get('parameters','direction', fallback=None)
        self.alpha = param.getfloat('parameters','alpha', fallback=None)  #help='Spectral index alpha (for directional search)'
        self.fRef = param.getfloat('parameters','fRef', fallback=25.0) #help='Reference frequency of the analysis (default:25Hz)
        self.Hf_file = param.get('parameters','Hf_file', fallback=None) #help='If user want to provide the H(f) file directly as txt file'
        self.numerical_Hf = self.Hf_file is not None
        self.GW_polarization = param.get('parameters', 'GW_polarization', fallback='T') #help='GW_polarization to use (default: Tensor polarization)'
        self.injection =  param.getboolean('parameters','injection', fallback = False) #help='Perform an injection study (default: False)'
        self.inj_map_path = param.get('parameters','inj_map_path', fallback=None) #help='Text file with HEALPix map details for injection'
        if self.injection:
            if self.inj_map_path is None:
                raise ValueError("inj_map_path must be provided when injection is True.")
            if not os.path.isfile(self.inj_map_path):
                raise ValueError(f"inj_map_path '{self.inj_map_path}' does not exist.")
            self.inj_map = np.loadtxt(self.inj_map_path)
            self.inj_map = hp.ud_grade(self.inj_map, self.nside)
            if info_logger:
                info_logger.warning('Warning: The injected map will be downgraded or upgraded to match the user-defined Nside.')

        #list of required parameters
        required_params = ['nside','pixel','sph','beam','f_max']
        
        # The following lines will override the parameters if they are present in the dictionary
        if override_params is not None:
            for key, value in override_params.items():
                if hasattr(self, key):
                    old_value = getattr(self, key)
                    setattr(self, key, value)
                    if info_logger:
                        info_logger.warning(f"Overriding parameter {key}: {old_value} -> {value}")
                else:
                    if info_logger:
                        info_logger.warning(f"Tried to override non-existing parameter {key}")
        
        
        for param in required_params:
            if getattr(self, param) is None:
                raise ValueError(f"Parameter '{param}' must be provided in the parameter file or via command line.")

        
        # Check and conditions after parameters have been overridden
        if not hp.isnsideok(self.nside,nest=True):
            raise ValueError("nside should be power of 2")

        if self.notching and self.notch_list is None:
            raise ValueError("notch_list must be provided when notching is True")
        
        self.lmax = self.lmax if self.lmax is not None else 2 * self.nside

        if self.nbr:
            self.pixel = True
            self.sph = self.beam = self.injection = False
            if self.raHr is None or self.decDeg is None or self.direction is None:
                raise ValueError("raHr, decDeg, and direction must be provided when nbr is True")

        if self.Hf_file is None and self.alpha is None:
            raise ValueError("Either Hf_file or alpha must be provided.")

        if self.numerical_Hf:
            if not os.path.isfile(self.Hf_file):
                raise ValueError(f"Hf_file '{self.Hf_file}' does not exist.")



class FramesetParam:
    ''''Class to pack all relevant parameters for a set of framesets.
        Initialized by location of framesets file and name of frameset folder.'''
    def __init__(self,framesets_file,set_name):
        framesets = configparser.ConfigParser()
        framesets.read(framesets_file)
        try:
            self.frameset_name = set_name #help='Location of the frame files'
            self.path =  framesets.get(set_name,'path')
            self.total_frames = framesets.getint(set_name,'total_frames') #help='Total number of gwf files'
            self.process =  framesets.getboolean(set_name,'process') #help='Whether to process (i.e. use these frames to make maps) or not'
            self.ifo1 =  framesets.get(set_name,'ifo1') #help='Interferometer 1 name'
            self.ifo2 =  framesets.get(set_name,'ifo2') #help='Interferometer 2 name'
            #self.overlap =  framesets.getboolean(set_name,'overlap') #help='Whether the frames are with overlap or not'
            self.deltaF =  framesets.getfloat(set_name,'deltaF') #help='Size of frequency bins in the frames'
            self.fhigh =  framesets.getfloat(set_name,'fhigh') #help='Maximum frequency available in the frames'
            self.flow =  framesets.getfloat(set_name,'flow') #help='Minimum frequency available in the frames'
            self.segDuration = framesets.getint(set_name,'segDuration') #help='Length of data (seconds) in each frames'
            self.GPSStart =  framesets.getint(set_name,'GPSStart') #help='Begininng of the data set (in GPStime) --> virtual if folded data'
            self.GPSEnd =  framesets.getint(set_name,'GPSEnd') #help='End time of the data set (in GPStime) --> virtual if folded data'
            self.winFactor = framesets.getfloat(set_name,'winFactor') #help='Reading windown factors'
            self.w1w2bar = framesets.getfloat(set_name,'w1w2bar') #help='Reading windown factors'
            self.bias = framesets.getfloat(set_name,'bias') #help='Reading bias factor from the frames'
        except configparser.NoOptionError as e:
            sys.exit(f"{TRED}Error: Required parameter '{e.option}' is missing in the framesets file.{ENDC}")


class FramesetIntermediates:
    ''' Class to pack all relevant data required for map calculation for a frameset.'''
    def __init__(self,frame_param,pystoch_param):
        dataset = frame_param.frameset_name
        # Loading GPS, Frequency, CSD, and PSD information from frames
        GPSmid,f_all,csd,sigma_sq_inv = load_frame_data(pystoch_param,frame_param,dataset)
        self.csd = np.array(csd)
        self.sigma_sq_inv = np.array(sigma_sq_inv)
        self.GPSmid = GPSmid
        self.f_all = f_all

        t_delay, combined_antenna_response = seed_matrices(GPSmid,pystoch_param,frame_param,dataset)
        self.t_delay = t_delay
        self.combined_antenna_response = combined_antenna_response

        # Nomralizations for dirty maps and Fisher matrix
        self.norm_map = (frame_param.deltaF*frame_param.winFactor)*2.0
        self.norm_fisher = (frame_param.deltaF*frame_param.winFactor)/frame_param.segDuration

        # All about spectral index
        if pystoch_param.numerical_Hf:
            Hf_data = np.loadtxt(pystoch_param.Hf_file)
            print (' H(f) file loaded from file.')
            self.H_f = spectral_index(f_all,Hf_data)
        else:
            self.H_f = np.power((np.array(f_all)  / pystoch_param.fRef), (pystoch_param.alpha - 3))
        self.notch_array = make_notch_array(f_all,pystoch_param.notching,pystoch_param.notch_list)
        self.f_size = np.size(f_all)
        self.sph_map_size = (pystoch_param.lmax+1)**2
        self.pix_map_size = hp.nside2npix(pystoch_param.nside)

        if pystoch_param.sph:
            tt = GPSmid - GPSmid[0]
            tt_mat = np.repeat(tt,self.sph_map_size,axis=1)
            m_mat = np.repeat(np.expand_dims(complex_getlm(pystoch_param.lmax)[1],axis=1),np.size(tt),axis=1).T
            self.sph_phase_neg = exp(-1j * (2*np.pi/(float(sday.si.scale))) * m_mat * tt_mat)

class PystochResults:
    ''' Class to pack all the results.'''
    def __init__(self,pystoch_param):
        pix_map_size = hp.nside2npix(pystoch_param.nside)
        sph_map_size = (pystoch_param.lmax+1)**2
        self.fisher_f_pix = np.zeros((pix_map_size,pix_map_size), dtype = 'complex128')
        self.fisher_f_sph = np.zeros((sph_map_size,sph_map_size), dtype = 'complex128')

        if pystoch_param.nbr:
            self.map_dirty_f_pix = 0.0j
        else:
            self.map_dirty_f_pix = np.zeros((pix_map_size), dtype = 'complex128')
        self.map_dirty_f_sph = np.zeros((sph_map_size), dtype = 'complex128')
        self.map_inj_f_pix = np.zeros((pix_map_size), dtype = 'complex128')
        self.map_inj_f_sph = np.zeros((sph_map_size), dtype = 'complex128')
        self.f_rearrange = 0.0

def calculate_maps(ll,f,frameset,frame_param,pystoch_param):
    ''' Computing all the maps (in both pixel and sph) along with the beam function.'''
    results = PystochResults(pystoch_param)
    results.f_rearrange = frameset.f_all[ll]
    if ~frameset.notch_array[ll]:
        return results

    # Overlap Reduction Function (ORF) is calculated using the ORF seed matrices
    gamma_star = frameset.combined_antenna_response * np.exp(-1j*(2*np.pi*f)*frameset.t_delay)

    if pystoch_param.pixel:
    # pixel maps
        map_dirty_f_pix = np.dot(frameset.csd[ll]*frameset.sigma_sq_inv[ll],gamma_star)*frame_param.segDuration * frameset.H_f[ll]
        results.map_dirty_f_pix = np.squeeze(map_dirty_f_pix)*frameset.norm_map

    if pystoch_param.sph:
        # ORF in SpH basis for the first segment
        gamma_star_sph_0 = complex_map2alm(gamma_star[0], pystoch_param.lmax)
        # Repeating the first SpH map by number of segments
        gamma_star_sph_0_mat = np.repeat(np.expand_dims(gamma_star_sph_0,axis=1),np.size(frameset.GPSmid),axis=1).T
        # Calculating ORF in SpH basis for all segments by multiplying exp(-i * m * sky_rotation * t) with the first ORF in SpH
        gamma_star_sph = gamma_star_sph_0_mat * frameset.sph_phase_neg
        # Map calculation in SpH
        map_dirty_f_sph = np.dot(frameset.csd[ll]*frameset.sigma_sq_inv[ll],gamma_star_sph)*frame_param.segDuration * frameset.H_f[ll]
        map_dirty_f_sph, _ = part_alm(np.squeeze(map_dirty_f_sph))
        results.map_dirty_f_sph = map_dirty_f_sph*frameset.norm_map


    # Full Fisher Matrix:
    if pystoch_param.beam:
        if pystoch_param.pixel:
            fisher_f_pix =  np.dot((frameset.sigma_sq_inv[ll]*gamma_star.T).conjugate(), gamma_star).squeeze() * (frame_param.segDuration ** 2) * (frameset.H_f[ll] ** 2)
            results.fisher_f_pix = fisher_f_pix * frameset.norm_fisher
            if pystoch_param.injection:
                results.map_inj_f_pix = np.dot(fisher_f_pix, pystoch_param.inj_map) * frameset.norm_fisher

        if pystoch_param.sph:
            fisher_f_sph = np.dot((frameset.sigma_sq_inv[ll]*gamma_star_sph.T), gamma_star_sph.conjugate()).squeeze() * (frame_param.segDuration ** 2) * (frameset.H_f[ll] ** 2)
            results.fisher_f_sph = fisher_zeros(fisher_f_sph*frameset.norm_fisher)
            if pystoch_param.injection:
                results.map_inj_f_sph = np.dot(fisher_f_sph, complex_map2alm(pystoch_param.inj_map,pystoch_param.lmax)).squeeze() * frameset.norm_fisher

    return results

def calculate_fisher_diag(frameset,frame_param):
    ''' Calculating the fisher diagonal matrix.'''
    fisher_diag_pix = np.matmul(frameset.sigma_sq_inv,np.square(frameset.combined_antenna_response))*(frame_param.segDuration**2)

    return (fisher_diag_pix*frameset.norm_fisher)

def calculate_maps_wrapper(frameset,frame_param,pystoch_param,f_chunk):
    ''' A wrapper for all the map computations.'''
    map_dirty_mat_pix = []
    map_dirty_mat_sph = []
    map_inj_mat_pix = []
    map_inj_mat_sph = []
    fisher_sph = np.zeros((frameset.sph_map_size,frameset.sph_map_size), dtype = 'complex128')
    fisher_pix = np.zeros((frameset.pix_map_size,frameset.pix_map_size), dtype = 'complex128')
    f_rearrange = []
    notched_f = 0
    time.sleep(0.5)
    pid = int((pystoch_param.n_thread*(f_chunk[0]-frameset.f_all[0]))/(frameset.f_all[-1]-frameset.f_all[0]))
    chunksize = int(np.floor(float(np.size(frameset.f_all))/pystoch_param.n_thread))+1
    freq_iter = tqdm(f_chunk,miniters=1,unit='f_bin(s)',leave=False,position = pid,smoothing=0,bar_format='{l_bar}%s{bar}%s{r_bar}' % (TCYAN, ENDC))
    for ll,f in enumerate(freq_iter):
        freq_iter.set_description("Freq:%9.5f Hz"%f)
        if ~frameset.notch_array[(pid*chunksize) +ll]:
            notched_f += 1
            freq_iter.set_postfix({'Notched bins':notched_f})
        results = calculate_maps(((pid*chunksize) + ll),f,frameset,frame_param,pystoch_param)
        map_dirty_mat_pix.append(results.map_dirty_f_pix)
        map_dirty_mat_sph.append(results.map_dirty_f_sph)
        map_inj_mat_pix.append(results.map_inj_f_pix)
        map_inj_mat_sph.append(results.map_inj_f_sph)
        fisher_pix += results.fisher_f_pix
        fisher_sph += results.fisher_f_sph
        f_rearrange.append(results.f_rearrange)

    return map_dirty_mat_pix,map_dirty_mat_sph,fisher_pix,fisher_sph,f_rearrange,map_inj_mat_pix,map_inj_mat_sph,notched_f
