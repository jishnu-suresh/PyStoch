<p align="center">
  <img src="https://raw.githubusercontent.com/jishnu-suresh/PyStoch/main/docs/_static/pystoch_logo.png" alt="PyStoch" width="440">
</p>

<p align="center">
  <a href="https://pypi.org/project/pystoch/"><img src="https://img.shields.io/pypi/v/pystoch.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/pystoch/"><img src="https://img.shields.io/pypi/pyversions/pystoch.svg" alt="Python versions"></a>
  <a href="https://pystoch.readthedocs.io/en/latest/"><img src="https://readthedocs.org/projects/pystoch/badge/?version=latest" alt="Documentation Status"></a>
  <a href="https://github.com/jishnu-suresh/PyStoch/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/pystoch.svg" alt="License"></a>
</p>


[![](https://img.shields.io/badge/arXiv-1803.08285%20-red.svg)](https://arxiv.org/abs/1803.08285)
[![](https://img.shields.io/badge/arXiv-2011.05969%20-red.svg)](https://arxiv.org/abs/2011.05969)

# PyStoch - a Python-based code for SGWB mapping from GW interferometer data

  

Input is folded stochastic interferometric data (FSID)

authors: Anirban Ain, Jishnu Suresh, Sanjit Mitra, and Sudhagar Suyamprakasam 

email: anirban.ain@ligo.org, jishnu.suresh@ligo.org, 
sanjit.mitra@ligo.org, sudhagar.suyamprakasam@ligo.org

This code creates SGWB anisotropy maps using methods discussed in the following papers (we encourage you to cite these papers when you use PyStoch and its functionalities):

1.  "Very fast stochastic gravitational wave background map making using folded data."
```
@article{Ain:2018zvo,
author = "Ain, Anirban and Suresh, Jishnu and Mitra, Sanjit",
title = "{Very fast stochastic gravitational wave background map making using folded data}",
eprint = "1803.08285",
archivePrefix = "arXiv",
primaryClass = "gr-qc",
doi = "10.1103/PhysRevD.98.024001",
journal = "Phys. Rev. D",
volume = "98",
number = "2",
pages = "024001",
year = "2018"
}
```
2. "Unified mapmaking for an anisotropic stochastic gravitational wave background."
```
@article{Suresh:2020khz,
author = "Suresh, Jishnu and Ain, Anirban and Mitra, Sanjit",
title = "{Unified mapmaking for an anisotropic stochastic gravitational wave background}",
eprint = "2011.05969",
archivePrefix = "arXiv",
primaryClass = "gr-qc",
doi = "10.1103/PhysRevD.103.083024",
journal = "Phys. Rev. D",
volume = "103",
number = "8",
pages = "083024",
year = "2021"
}
```


## Installation

PyStoch is distributed on PyPI:

```
pip install pystoch
```

This installs the `pystoch` Python package and three command-line tools:
`read_frames`, `convert_frames`, and `pystoch`.

> **Note:** reading `.gwf` frames through `gwpy` additionally requires a frame
> backend (`lalframe` or `framel`), which is best installed via conda or your
> system package manager.

After installation, copy the bundled `parameters.ini` template into your
working directory and edit it for your run. Its location can be found with:

```
python -c "import pystoch, os; print(os.path.join(os.path.dirname(pystoch.__file__), 'data', 'parameters.ini'))"
```

## Instructions

###### See the following call recording for a detailed tutorial:
- https://dcc.ligo.org/LIGO-G2201754 (latest version)
- https://dcc.ligo.org/LIGO-G2000630 (old version, but contains the folding tutorial)
  
There are three steps to running this code:

1. Read `gwf` frames and collect parameters. (`read_frames`)

2. Convert `gwf` frames into hdf5 format. (`convert_frames`)

3. Making maps. (`pystoch`)

The parameter file for the calculation is `parameters.ini`

  
The steps are discussed in detail in the following.

### Read gwf frames and collect parameters. (read_frames)


All the frames you want to process should be kept in a subdirectories. These subdirectories are the framesets.

e.g., If you have some FSID frames (gwf format) for O2 run from the H1L1 baseline, keep them in a directory ./frames/O2_H1L1. So now you have a frameset O2_H1L1.
If you have another set of frames for O2 run from the H1L1 baseline with other parameters, you can keep them in a directory ./frames/O2_H1L1_NoOverlap.
Now you have another frameset O2_H1L1_NoOverlap. You can name framesets at your convenience, e.g., O2_H1L1_Albert, O2_H1L1_25September, use_this_one, etc.

You can have framesets of different baselines, e.g., O2_H1V1, O1_L1V1, etc.

*Remember*: All frames in a frameset are assumed to have the same parameters (duration, sampling rate, etc.).
  
After you copy the frames, you can just look at the **frames_location** field in parameters.ini. This should be the parent of the framesets.

Next is to run `read_frames` 
This function uses **gwpy** and **lalframe**. 

Run `./read_frames`
  
After it runs successfully, it will create/modify the `framesets.ini` file. Finally, all the framesets and their relevant parameters will be written.

Everything should be fine if your frames follow the standard collaboration and group conventions of channel and file names.
*But you should double-check all the parameters.*
The `framesets.ini` file has a parameter 'process' for all framesets. If this is 'True,' that frameset will be included in the map calculation. If it is False, that frameset will be ignored.
```
./read_frames --help

A code to check the available frames and prepare parameter list for PyStoch

usage: read_frames [-h] [--param_file PARAM_FILE] [--log_file LOG_FILE] [--err_file ERR_FILE]

Read parameters.ini file path from command line
optional arguments:
  -h, --help            show this help message and exit
  --param_file PARAM_FILE
                        Path to the parameters.ini file
  --log_file LOG_FILE   Path to the log file (optional)
  --err_file ERR_FILE   Path to the error file (optional)
```
### Convert gwf frames into hdf5 format. (convert_frames)

After ensuring you have the correct **process** in the `framesets.ini` file and the parameters are correct, run `convert_frames`.

Run `./convert_frames`

This will read the gwf files and create an hdf5 file inside the frameset directory. This will speed up the process because hdf5 files are faster to read. And you have to do it only once.
```
./convert_frames --help
usage: convert_frames [-h] [--param_file PARAM_FILE] [--datasets [DATASETS ...]] [--log_file LOG_FILE]
                      [--err_file ERR_FILE]

Read parameters.ini file path from command line

optional arguments:
  -h, --help            show this help message and exit
  --param_file PARAM_FILE
                        Path to the parameters.ini file
  --datasets [DATASETS ...]
                        Space-separated list of datasets to process
  --log_file LOG_FILE   Path to the log file (optional)
  --err_file ERR_FILE   Path to the error file (optional)

```

### Making maps. (pystoch)
  
Now you should thoroughly check parameters.ini and framesets.ini and run `./pystoch`

*The framesets with **process** True will be processed.*

After completing all three steps successfully, you will find the results in a pickle file format.

You can also pass the parameters as command line options if required:
```./pystoch --help```
```
  ____        ____  _             _     
 |  _ \ _   _/ ___|| |_ ___   ___| |__  
 | |_) | | | \___ \| __/ _ \ / __| '_ \ 
 |  __/| |_| |___) | || (_) | (__| | | |
 |_|    \__, |____/ \__\___/ \___|_| |_|
        |___/                           
Stochastic Gravitational-Wave Background Map-making Pipeline

usage: pystoch [-h] [--param_file PARAM_FILE] [--datasets [DATASETS ...]] [--output_prefix OUTPUT_PREFIX]
               [--log_file LOG_FILE] [--err_file ERR_FILE] [--param_nside PARAM_NSIDE]
               [--param_f_min PARAM_F_MIN] [--param_f_max PARAM_F_MAX] [--param_notching PARAM_NOTCHING]
               [--param_notch_list PARAM_NOTCH_LIST] [--param_pixel PARAM_PIXEL] [--param_sph PARAM_SPH]
               [--param_lmax PARAM_LMAX] [--param_beam PARAM_BEAM]
               [--param_output_map_path PARAM_OUTPUT_MAP_PATH] [--param_multi_thread PARAM_MULTI_THREAD]
               [--param_n_thread PARAM_N_THREAD] [--param_nbr PARAM_NBR] [--param_raHr PARAM_RAHR]
               [--param_decDeg PARAM_DECDEG] [--param_direction PARAM_DIRECTION] [--param_alpha PARAM_ALPHA]
               [--param_fRef PARAM_FREF] [--param_Hf_file PARAM_HF_FILE]
               [--param_GW_polarization PARAM_GW_POLARIZATION] [--param_injection PARAM_INJECTION]
               [--param_inj_map_path PARAM_INJ_MAP_PATH]

Data set and Output file prefix. Other parameters should be changed in the parameter.ini file

optional arguments:
  -h, --help            show this help message and exit
  --param_file PARAM_FILE
                        Path to the parameter file (must end with .ini)
  --datasets [DATASETS ...]
                        Names of the datasets to process
  --output_prefix OUTPUT_PREFIX
                        Output file prefix (optional)
  --log_file LOG_FILE   Path to the log file (optional)
  --err_file ERR_FILE   Path to the error file (optional)
  --param_nside PARAM_NSIDE
                        Override nside parameter
  --param_f_min PARAM_F_MIN
                        Override f_min parameter
  --param_f_max PARAM_F_MAX
                        Override f_max parameter
  --param_notching PARAM_NOTCHING
                        Override notching parameter
  --param_notch_list PARAM_NOTCH_LIST
                        Override notch_list parameter
  --param_pixel PARAM_PIXEL
                        Override pixel parameter
  --param_sph PARAM_SPH
                        Override sph parameter
  --param_lmax PARAM_LMAX
                        Override lmax parameter
  --param_beam PARAM_BEAM
                        Override beam parameter
  --param_output_map_path PARAM_OUTPUT_MAP_PATH
                        Override output_map_path parameter
  --param_multi_thread PARAM_MULTI_THREAD
                        Override multi_thread parameter
  --param_n_thread PARAM_N_THREAD
                        Override n_thread parameter
  --param_nbr PARAM_NBR
                        Override nbr parameter
  --param_raHr PARAM_RAHR
                        Override raHr parameter
  --param_decDeg PARAM_DECDEG
                        Override decDeg parameter
  --param_direction PARAM_DIRECTION
                        Override direction parameter
  --param_alpha PARAM_ALPHA
                        Override alpha parameter
  --param_fRef PARAM_FREF
                        Override fRef parameter
  --param_Hf_file PARAM_HF_FILE
                        Override Hf_file parameter
  --param_GW_polarization PARAM_GW_POLARIZATION
                        Override GW_polarization parameter
  --param_injection PARAM_INJECTION
                        Override injection parameter
  --param_inj_map_path PARAM_INJ_MAP_PATH
                        Override inj_map_path parameter
