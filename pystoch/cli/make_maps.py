#!/usr/bin/env python

import os
import signal
import sys
import time
import pickle
import configparser
from functools import partial

import argparse
import healpy as hp
import numpy as np
from multiprocessing import cpu_count
from tqdm.contrib.concurrent import process_map

# From PyStoch
from pystoch.detectors import display_time
from pystoch.pystoch_functions import ascii_art
from pystoch.pystoch_class_and_mapping import (
    PystochParam,
    FramesetParam,
    FramesetIntermediates,
    calculate_fisher_diag,
    calculate_maps_wrapper,
)

from pystoch._logging import info_logger, error_logger, setup_logging


def keyboard_interrupt_handler(signal, frame):
    info_logger.info(f"\nKeyboard interrupt received. Exiting...")
    sys.exit(0)

def write_pickle(file_name, data):
    try:
        with open(file_name, 'wb') as f:
            pickle.dump(data, f, protocol=-1)
    except (pickle.PicklingError,FileNotFoundError) as e:
        error_logger.error(f"Failed to write pickle file: {e}", exc_info=True)

def str2bool(v):
    """Convert string to boolean"""
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError(f'Boolean value expected, got {v} instead.')

# Parameters overridable from the command line (--param_<name>) and the type
# used to parse each. Single source of truth for both the argparse options and
# the override dictionary, so the two can never drift out of sync.
ARG_TYPES = {
        'nside': int,
        'f_min': float,
        'f_max': float,
        'notching': str2bool,
        'notch_list': str,
        'pixel': str2bool,
        'sph': str2bool,
        'lmax': int,
        'beam': str2bool,
        'output_map_path': str,
        'multi_thread': str2bool,
        'n_thread': int,
        'nbr': str2bool,
        'raHr': float,
        'decDeg': float,
        'direction': str,
        'alpha': float,
        'fRef': float,
        'Hf_file': str,
        'GW_polarization': str,
        'injection': str2bool,
        'inj_map_path': str,
}

def write_final_parameters(parameters, framesets, datasets, output_dir):
    # Construct the final filename
    final_filename = os.path.join(output_dir, 'run_parameters.ini')

    config = configparser.ConfigParser()

    # Add the parameters to the Final_Parameters section
    config["Run_Parameters"] = {k: str(v) for k, v in vars(parameters).items()}

    # Add sections for each frameset only if it is in the datasets list
    for section in framesets.sections():
        if section in datasets:
            config[section] = {k: str(v) for k, v in framesets[section].items()}

    with open(final_filename, 'w') as configfile:
        config.write(configfile)

def build_parser(param_default):
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description='Data set and Output file prefix. Other parameters should be changed in the parameter.ini file')
    parser.add_argument('--param_file', type=str, default=param_default, help='Path to the parameter file (must end with .ini)')
    parser.add_argument('--datasets', type=str, nargs='*', default=[], help='Names of the datasets to process')
    parser.add_argument('--output_prefix', type=str, default='', help='Output file prefix (optional)')
    parser.add_argument('--log_file', type=str, default='', help='Path to the log file (optional)')
    parser.add_argument('--err_file', type=str, default='pystoch.err', help='Path to the error file (optional)')

    # Add argument definitions for each of the PystochParam parameters
    for param, arg_type in ARG_TYPES.items():
        parser.add_argument(f'--param_{param}', type=arg_type, help=f'Override {param} parameter')
    return parser

def build_overrides(args):
    """Collect the --param_<name> overrides that were actually provided."""
    return {param: getattr(args, f'param_{param}') for param in ARG_TYPES
            if getattr(args, f'param_{param}') is not None}

def select_datasets(args, framesets, datasets_full, param_file):
    """Pick which framesets to process; a passed .ini overrides param_file."""
    datasets = []
    passed_arg = args.datasets
    if len(passed_arg) > 0:
        for item in passed_arg:
            if item.endswith('.ini'):
                param_file = item
            else:
                if item in datasets_full:
                    datasets.append(item)
                else:
                    info_logger.warning(f'Dataset not found: {item}')
    else:
        datasets = [dataset for dataset in datasets_full if framesets.getboolean(dataset, 'process')]
    return datasets, param_file

def write_pixel_output(dataset, args, parameters, frame_param, frameset,
                       dict_output, map_dirty_mat_pix, map_inj_mat_pix, fisher_pix):
    """Build and write the pixel-basis (and NBR, if enabled) output pickle(s)."""
    map_dirty_mat = np.array(map_dirty_mat_pix,dtype=np.complex128)
    fisher_diag_pix = calculate_fisher_diag(frameset,frame_param)

    if parameters.nbr:
       info_logger.info(f"Normalized point-estimate and sigma will be saved in Pixel_NBR data set.")

       fisher_diag_pix = fisher_diag_pix * frameset.notch_array
       fisher_diag_mat = np.array(fisher_diag_pix)
       with np.errstate(divide='ignore', invalid='ignore'):
           ptEst_nbr = frame_param.deltaF * np.true_divide(np.real(np.squeeze(map_dirty_mat)),np.squeeze(fisher_diag_mat))
           ptEst_nbr = np.nan_to_num(ptEst_nbr, nan=0.0, posinf=0.0, neginf=0.0)

           sig_nbr = frame_param.deltaF * frame_param.bias * np.true_divide(1.0,np.sqrt(np.real(np.squeeze(fisher_diag_mat))))
           sig_nbr = np.nan_to_num(sig_nbr, nan=0.0, posinf=0.0, neginf=0.0)
           map_snr_nbr = np.true_divide(ptEst_nbr,sig_nbr)
           map_snr_nbr = np.nan_to_num(map_snr_nbr, nan=0.0, posinf=0.0, neginf=0.0)
       dict_nbr = dict_output
       dict_nbr.update({"ptEst": ptEst_nbr,"sig" :sig_nbr, "map_snr":map_snr_nbr,"map_dirty":map_dirty_mat, "fisher_diag":fisher_diag_mat, "f_actual":(frameset.notch_array * frameset.f_all),"f_all": frameset.f_all})
       file_name = os.path.join(parameters.output_map_path,f'{args.output_prefix}Pixel_NBR_{dataset}_{parameters.nside}_{time.strftime("%d%m%Y")}.pkl')
       write_pickle(file_name, dict_nbr)
    else:
        fisher_diag_pix = fisher_diag_pix * np.expand_dims(frameset.notch_array,axis=1)
        fisher_diag_mat = np.array(fisher_diag_pix)

    dict_pix = dict_output.copy()
    if parameters.injection:
        dict_pix.update({"map_inj_mat_pix": map_inj_mat_pix,"map_inj":parameters.inj_map})
    dict_pix.update({"map_dirty_pix": map_dirty_mat,"fisher_full_pix" :fisher_pix, "fisher_diag":fisher_diag_pix,"notch_array":frameset.notch_array,"f_all": frameset.f_all})
    file_name = os.path.join(parameters.output_map_path,f'{args.output_prefix}Pixel_{dataset}_{parameters.nside}_{time.strftime("%d%m%Y")}.pkl')
    write_pickle(file_name, dict_pix)

def write_sph_output(dataset, args, parameters, frameset, dict_output,
                     map_dirty_mat_sph, map_inj_mat_sph, fisher_sph):
    """Build and write the spherical-harmonic output pickle."""
    map_dirty_sph_mat = np.array(map_dirty_mat_sph)
    map_dirty_sph = np.sum(map_dirty_sph_mat,axis=0)

    dict_sph = dict_output.copy()
    if parameters.injection:
        dict_sph.update({"map_inj_mat_sph": map_inj_mat_sph,"map_inj":parameters.inj_map})
    dict_sph.update({"map_dirty_sph": map_dirty_sph_mat,"fisher_full_sph" :fisher_sph, "f_actual":(frameset.notch_array * frameset.f_all),"f_all": frameset.f_all})
    file_name = os.path.join(parameters.output_map_path,f'{args.output_prefix}SpH_{dataset}_{parameters.lmax}_{time.strftime("%d%m%Y")}.pkl')
    write_pickle(file_name, dict_sph)

def process_dataset(dataset, framesets_file, parameters, args):
    """Compute and write the maps for a single frameset."""
    # Loop over all framesets
    start = time.time()
    start_cpu = time.process_time()
    info_logger.info(f" *** Processing {dataset} ***\n")

    frame_param = FramesetParam(framesets_file,dataset)
    frameset = FramesetIntermediates(frame_param,parameters)

    # Printing some info to display which frameset and what parameters
    info_logger.info(f"Data from {frame_param.ifo1}{frame_param.ifo2} Baseline. Total {frame_param.total_frames} frames of {frame_param.segDuration} seconds are available.")
    info_logger.info(f'{frameset.f_size} narrow-band maps for frequency range {parameters.f_min} Hz to {parameters.f_max} Hz will be calculated.\n')

    f_size = np.size(frameset.f_all)
    sph_map_size = (parameters.lmax+1)**2
    pix_map_size = hp.nside2npix(parameters.nside)

    if parameters.multi_thread:
        n_thread = parameters.n_thread
        if n_thread == 0:
            n_thread = cpu_count()
        info_logger.info(f'Multithreading enabled. Using {n_thread} simultaneous threads.')
    else:
        n_thread = 1
    parameters.n_thread = n_thread
    chunksize = int(np.floor(float(np.size(frameset.f_all))/n_thread))+1
    f_chunked=[frameset.f_all[i:i + chunksize] for i in range(0, len(frameset.f_all), chunksize)]

    calculate_maps_ready = partial(calculate_maps_wrapper,frameset,frame_param,parameters)

    try:
        all_results = process_map(calculate_maps_ready, f_chunked, max_workers=n_thread,unit='thread', disable=True)
    except Exception as e:
        error_logger.error(f"Failed to process framesets: {e}", exc_info=True)
        sys.exit(1)
    map_dirty_mat_pix = []
    map_dirty_mat_sph = []
    map_inj_mat_pix = []
    map_inj_mat_sph = []
    fisher_pix = np.zeros((pix_map_size,pix_map_size), dtype = 'complex128')
    fisher_sph = np.zeros((sph_map_size,sph_map_size), dtype = 'complex128')
    f_rearrange = []
    notched_f = 0
    for multip_results in all_results:
        map_dirty_mat_pix+=(multip_results[0])
        map_dirty_mat_sph+=(multip_results[1])
        fisher_pix += multip_results[2]
        fisher_sph += multip_results[3]
        f_rearrange += multip_results[4]
        map_inj_mat_pix+=(multip_results[5])
        map_inj_mat_sph+=(multip_results[6])
        notched_f += (multip_results[7])

    all_results = None

    if n_thread > 1:
        if sorted(f_rearrange) == f_rearrange:
            info_logger.info('\nAll the threads joined in order.')
        else:
            info_logger.info(f"WARNING: multi-threading has changed the frequency ordering")


    stop = time.time()-start
    stop_cpu = time.process_time()-start_cpu
    info_logger.info(f'\nAll calculation done in {display_time(stop)}. Average time per frequency bin is {round(stop/np.count_nonzero(frameset.notch_array* frameset.f_all),2)} seconds. Total number of notched bins are {notched_f}.')
    dict_output = vars(parameters)
    dict_output.update(vars(frame_param))
    dict_output.update({'computer':os.uname()[1],'datetime':time.strftime("date: %d/%m/%Y, time: %Hhr %Mmin %Ssec"),'run_duration':stop,'run_duration(cpu)':stop_cpu,'f_rearrange':f_rearrange})

    if parameters.pixel:
        write_pixel_output(dataset, args, parameters, frame_param, frameset,
                           dict_output, map_dirty_mat_pix, map_inj_mat_pix, fisher_pix)

    if parameters.sph:
        write_sph_output(dataset, args, parameters, frameset, dict_output,
                         map_dirty_mat_sph, map_inj_mat_sph, fisher_sph)

def main():

    # Register the keyboard interrupt handler
    signal.signal(signal.SIGINT, keyboard_interrupt_handler)

    framesets = configparser.ConfigParser()
    framesets_file = os.path.join(".","framesets.ini")
    if not os.path.exists(framesets_file):
        error_logger.error(f"{framesets_file} not found.")
        sys.exit(1)

    framesets.read(framesets_file)
    datasets_full = framesets.sections()

    param_default = os.path.join(".","parameters.ini")
    param_file = param_default

    if not os.path.exists(param_file):
        error_logger.error(f"{param_file} not found.")
        sys.exit(1)

    # ASCII art when user access --help option
    if '--help' in sys.argv or '-h' in sys.argv:
        ascii_art()

    # Check if the user provided an output_prefix, otherwise use the default values
    parser = build_parser(param_default)
    args = parser.parse_args()

    # Create a dictionary of override parameters
    override_params = build_overrides(args)

    setup_logging(args.log_file, args.err_file)

    datasets, param_file = select_datasets(args, framesets, datasets_full, param_file)

    try:
        parameters = PystochParam(param_file,override_params,info_logger=info_logger)
        info_logger.warning(f'Using parameters from {param_file}')
    except ValueError as e:
        error_message = str(e)
        error_logger.error(error_message)
        parser.error(error_message)
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        error_logger.error(error_message)
        parser.error(error_message)

    if len(datasets) == 0:
        error_logger.error(f"ERROR:No frameset found.")
        sys.exit(1)

    info_logger.info(f'\nFollowing framesets will be processed. \n {datasets} \n')

    # Check whether the output directory already exists. If not, create the directory.
    if not os.path.isdir(parameters.output_map_path):
        try:
            os.makedirs(parameters.output_map_path)
        except Exception as e:
            error_logger.error(f"Failed to create directory: {e}",exc_info=True)
            sys.exit(1)
    # Save the final parameters to the output directory.
    write_final_parameters(parameters, framesets, datasets, parameters.output_map_path)

    info_logger.info(f" To be calculated: pixel = {parameters.pixel}, sph = {parameters.sph}, beam = {parameters.beam}.")

    if parameters.pixel and parameters.sph:
        info_logger.info(f' Map Resolution: nside = {parameters.nside}, lmax = {parameters.lmax}. \n')
    elif parameters.pixel:
        info_logger.info(f' Pixel Resolution: nside = {parameters.nside}. \n')
    elif parameters.sph:
        info_logger.info(f' Spherical Harmonic Resolution: lmax = {parameters.lmax}. \n')

    for dataset in datasets:
        process_dataset(dataset, framesets_file, parameters, args)

    print (f"\nEverything finished successfully.")
    info_logger.info(f"Everything finished successfully.")

if __name__ == "__main__":
    main()
