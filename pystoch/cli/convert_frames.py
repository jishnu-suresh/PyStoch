#!/usr/bin/env python

import os
import glob
import h5py
import numpy as np
import time
import sys
import logging
import argparse
import configparser
from gwpy.timeseries import TimeSeriesDict

# Define separate loggers for info and error (as global variable)
info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')

# Prevent log messages from propagating to the root logger
info_logger.propagate = False
error_logger.propagate = False

def read_ini_file(file_path: str) -> configparser.ConfigParser:
    if not os.path.isfile(file_path):
        error_logger.error(f"Error: Parameter file not found: {file_path}")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(file_path)
    return config


def process_frameset(frameset: configparser.SectionProxy, parameters: configparser.ConfigParser):
    frames_path = frameset.get('path')
    files = sorted(glob.glob(frames_path+'/*.gwf'))
    file_names = [ff for ff in os.listdir(frames_path) if os.path.isfile(os.path.join(frames_path, ff))]
    ifo_info = file_names[0].split("_")[1]
    ifo1_name, ifo2_name = ifo_info[:2], ifo_info[2:]
    baseline = ifo1_name + ifo2_name
    csd_cnl_rl = baseline + ':' + parameters.get('parameters','csd_channel_real', fallback='ReCSD')
    csd_cnl_im = baseline + ':' + parameters.get('parameters','csd_channel_imaginary', fallback='ImCSD')
    single_psd_cnl = parameters.getboolean('parameters','psd_combined', fallback=False)
    time_cnl = baseline + ':GPStime'
    
    if single_psd_cnl:
        psd_cnl = baseline + ':' + parameters.get('parameters','psd_channel', fallback='AdjacentPSD')
    else:
        psd_cnl1 = ifo1_name + ':' + parameters.get('parameters','psd_channel', fallback='AdjacentPSD')
        psd_cnl2 = ifo2_name + ':' + parameters.get('parameters','psd_channel', fallback='AdjacentPSD')

    csd = []
    sigma_sq_inv = []
    gps_times = []
    info_logger.info(f"\nDataset: {frameset.name}, total {frameset.getint('total_frames')} frames")
    frame_data_name = frames_path + '/' + baseline + '_compressed'  +'.hdf5'
    
    if os.path.exists(frame_data_name):
        info_logger.info(f"File {frame_data_name} already exists.")
        return

    info_logger.info(f'Reading and converting frames.')
    start = time.time()

    for ii, frame in enumerate(files):
        if single_psd_cnl:
            data = TimeSeriesDict.read(frame,[csd_cnl_rl,csd_cnl_im ,psd_cnl,time_cnl])
            csd.append(data[csd_cnl_rl].value+(1j*data[csd_cnl_im].value))
            sigma_sq_inv.append(data[psd_cnl].value)
            gps_times.append(data[time_cnl].value)
        else:
            data = TimeSeriesDict.read(frame,[csd_cnl_rl,csd_cnl_im ,psd_cnl1,psd_cnl2,time_cnl])
            csd.append(data[csd_cnl_rl].value+(1j*data[csd_cnl_im].value))
            sigma_sq_inv.append(np.reciprocal(np.multiply(data[psd_cnl1].value, data[psd_cnl2].value)))
            gps_times.append(data[time_cnl].value)

        print(f"{ii} frames loaded.")
        sys.stdout.write("\033[F")

    # Shift GPS time to the midpoint of the segment
    half_seg = float(frameset.get('segDuration'))/2.0
    gps_times_mid = [x + half_seg for x in gps_times]

    frames_preloaded = h5py.File(frame_data_name, "w")
    frames_preloaded.create_dataset('csd', data = csd)
    frames_preloaded.create_dataset('sigma_sq_inv', data = sigma_sq_inv)
    frames_preloaded.create_dataset('gps_times_mid', data = gps_times_mid)
    frames_preloaded.close()

    info_logger.info(f"frames loaded and saved in {int(time.time() - start)} seconds.")
    print(f"frames loaded and saved in {int(time.time() - start)} seconds.")

def main():
    # Define command-line argument parser
    parser = argparse.ArgumentParser(description="Read parameters.ini file path from command line")
    parser.add_argument('--param_file', type=str, default="./parameters.ini",
                        help="Path to the parameters.ini file")
    parser.add_argument('--datasets', type=str, nargs='*', default=None,
                        help="Space-separated list of datasets to process")
    parser.add_argument('--log_file', type=str, default='', help='Path to the log file (optional)')
    parser.add_argument('--err_file', type=str, default='convertframe.err', help='Path to the error file (optional)')
    args = parser.parse_args()

    # Set up the info logger
    info_handler = logging.FileHandler(args.log_file, mode='a') if args.log_file else logging.StreamHandler(sys.stdout)
    info_handler.setLevel(logging.INFO)
    info_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    info_handler.setFormatter(info_formatter)
    info_logger.addHandler(info_handler)
    info_logger.setLevel(logging.INFO)

    # Set up the error logger
    err_handler = logging.FileHandler(args.err_file, mode='a')
    err_handler.setLevel(logging.ERROR)
    err_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    err_handler.setFormatter(err_formatter)
    error_logger.addHandler(err_handler)
    error_logger.setLevel(logging.ERROR)
    
    parameters = read_ini_file(args.param_file)
    framesets = read_ini_file("./framesets.ini")

    if args.datasets is not None:
        datasets_to_process = args.datasets
    else:
        datasets_to_process = [frameset for frameset in framesets.sections() 
                               if framesets.getboolean(frameset, 'process')]

    for frameset in datasets_to_process:
        if framesets.has_section(frameset):
            process_frameset(framesets[frameset], parameters)

if __name__ == "__main__":
    main()

