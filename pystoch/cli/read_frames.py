#!/usr/bin/env python

import glob
import sys
import os
import logging
import argparse
import configparser
from typing import List, Tuple
from gwpy.timeseries import TimeSeriesDict

# Define separate loggers for info and error (as global variable)
info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')

# Prevent log messages from propagating to the root logger
info_logger.propagate = False
error_logger.propagate = False

def process_directory(root: str, name: str, parameter_file) -> None:
    try:
        dir_full = os.path.join(root, name)
        files = [ff for ff in os.listdir(dir_full) if os.path.isfile(os.path.join(dir_full, ff))]
        files_full_path = sorted(glob.glob(dir_full+'/*.gwf'))
    except Exception as e:
        error_logger.error(f"Error while reading files: {e}", exc_info=True)
        return
    info_logger.info(f"Frame directory: {dir_full}")

    if not files_full_path:
        info_logger.info(f"There are no frames in {dir_full}\n")
        return

    nn = len(files_full_path)
    info_logger.info(f"{nn} Frames available for processing in this directory.")
    ifo_info = files[0].split("_")[1]
    ifo1_name, ifo2_name = ifo_info[:2], ifo_info[2:]
    baseline = ifo1_name+ifo2_name

    try:
        chnl_list = [baseline+':deltaF',baseline+':fhigh', baseline+':flow',baseline+':foldedSegmentDuration',baseline+':GPStime',baseline+':winFactor',baseline+':w1w2bar',baseline+':bias' ]
        deltaF, fhigh, flow, segDuration, GPSStart, winFactor, w1w2bar, bias =  read_channels(files_full_path[0], chnl_list)
        write_frame_parameters(name, dir_full, nn, ifo1_name, ifo2_name, deltaF, fhigh, flow, winFactor, w1w2bar, bias, segDuration, GPSStart, parameter_file)
    except Exception as e:
        error_logger.error(f"One or more expected channel(s) not found.\nError: {e}\n")

    info_logger.info(f"Baseline: {baseline}\n")

def write_frame_parameters(name: str, dir_full: str, nn: int, ifo1_name: str, ifo2_name: str, deltaF: float, 
                           fhigh: float, flow: float, winFactor: float, w1w2bar: float, bias: float, 
                           segDuration: int, GPSStart: int, parameter_file) -> None:
    GPSEnd = GPSStart + segDuration*nn
    info_logger.info(f"Frequency Information: deltaF {float(deltaF)}, flow {float(flow)}, fhigh {float(fhigh)}.")
    info_logger.info(f"Time Information: segDuration {int(segDuration)}, GPSStart {int(GPSStart)}, GPSEnd {int(GPSEnd)}.")
    parameter_file.write("[{}]".format(name))
    parameter_file.write(f"\npath:  {dir_full}")
    parameter_file.write(f"\ntotal_frames: {nn}")
    parameter_file.write("\nprocess:  True")
    parameter_file.write(f"\nifo1:  {ifo1_name}")
    parameter_file.write(f"\nifo2:  {ifo2_name}")
    parameter_file.write(f"\ndeltaF:  {float(deltaF)}")
    parameter_file.write(f"\nfhigh:  {float(fhigh)}")
    parameter_file.write(f"\nflow:  {float(flow)}")
    parameter_file.write(f"\nwinFactor: {float(winFactor)}")
    parameter_file.write(f"\nw1w2bar: {float(w1w2bar)}")
    parameter_file.write(f"\nbias: {float(bias)}")
    parameter_file.write(f"\nsegDuration:  {int(segDuration)}")
    parameter_file.write(f"\nGPSStart:  {int(GPSStart)}")
    parameter_file.write(f"\nGPSEnd:  {int(GPSEnd)}\n")

def read_channels(frame: str, chnl_list: List[str]) -> List[float]:
    '''A wrapper function that uses gwpy to get data from frames.'''
    data = TimeSeriesDict.read(frame, chnl_list)
    output = [data[chnl].value for chnl in chnl_list]
    return output

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read parameters.ini file path from command line")
    parser.add_argument('--param_file', type=str, default="./parameters.ini",
                        help="Path to the parameters.ini file")
    parser.add_argument('--log_file', type=str, default='', help='Path to the log file (optional)')
    parser.add_argument('--err_file', type=str, default='readframe.err', help='Path to the error file (optional)')
    return parser.parse_args()

def main() -> None:
    print(f"\nA code to check the available frames and prepare parameter list for PyStoch\n")
    args = parse_arguments()

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


    try:
        if not os.path.isfile(args.param_file):
            error_logger.error(f"Error: parameters.ini file not found: {args.param_file}", exc_info=True)
            sys.exit(1)
    except Exception as e:
        error_logger.error(f"Error: Failed to check if the file exists: {args.param_file}\nError: {e}", exc_info=True)
        sys.exit(1)

    param = configparser.ConfigParser()
    param.read(args.param_file)
    frames_path = param.get('parameters', 'frames_location')

    with open("./framesets.ini", "w") as parameter_file:
        for root, dirs, _ in os.walk(frames_path, topdown=False):
            for name in dirs:
                process_directory(root, name, parameter_file)

    info_logger.info(f"Frame list prepared\n")
    print(f"Frame list prepared. Check frame details and edit parameter file (if needed) before running PyStoch.\n")
    
    logging.shutdown() # ensure all logging output has been flushed

if __name__ == "__main__":
    main()
