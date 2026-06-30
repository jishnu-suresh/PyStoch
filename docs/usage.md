# Usage

Running PyStoch is a three-step process. All commands read `parameters.ini`
(and, after step 1, `framesets.ini`) from the current working directory unless
told otherwise.

## 1. Read frames — `read_frames`

Keep the frames you want to process in **subdirectories**; each subdirectory is
a *frameset*. For example, FSID frames for the O3 run from the H1L1 baseline can
live in `./frames/O3_H1L1/`, giving a frameset named `O3_H1L1`. You can have
framesets for different baselines (e.g. `O3_H1V1`, `O3_L1V1`).

> All frames within a frameset are assumed to share the same parameters
> (duration, sampling rate, etc.).

Point the `frames_location` field in `parameters.ini` at the **parent** of the
framesets, then run:

```bash
read_frames
```

This creates (or updates) `framesets.ini` with each frameset and its parameters.
Every frameset has a `process` flag: if `True`, it is included in the map
calculation; if `False`, it is ignored. Always double-check the detected
parameters.

```text
usage: read_frames [-h] [--param_file PARAM_FILE] [--log_file LOG_FILE] [--err_file ERR_FILE]
```

## 2. Convert frames — `convert_frames`

Once `framesets.ini` is correct, convert the `.gwf` frames to a compressed HDF5
file (this only has to be done once per frameset, and speeds up reading):

```bash
convert_frames
```

```text
usage: convert_frames [-h] [--param_file PARAM_FILE] [--datasets [DATASETS ...]]
                      [--log_file LOG_FILE] [--err_file ERR_FILE]
```

## 3. Make maps — `pystoch`

Check `parameters.ini` and `framesets.ini`, then run:

```bash
pystoch
```

Framesets whose `process` flag is `True` are processed. Results are written as
pickle (`.pkl`) files in `output_map_location`, along with a `run_parameters.ini`
recording the exact settings used.

Most parameters can also be overridden on the command line (these take
precedence over `parameters.ini`), for example:

```bash
pystoch --param_nside 8 --param_f_min 20 --param_f_max 100 \
        --param_sph True --param_pixel True --output_prefix run1_
```

Run `pystoch --help` for the full list of overrides.

## Outputs

Depending on the selected bases, PyStoch writes:

- `Pixel_<dataset>_<nside>_<date>.pkl` — pixel-basis dirty map and Fisher information.
- `SpH_<dataset>_<lmax>_<date>.pkl` — spherical-harmonic dirty map and Fisher.
- `Pixel_NBR_<dataset>_<nside>_<date>.pkl` — narrowband-radiometer point estimate and sigma (when `nbr` is enabled).

Each pickle is a dictionary that also stores the run parameters and frameset
metadata.

## Using PyStoch as a library

The main building blocks are available directly from the top-level `pystoch`
namespace, so PyStoch can be scripted as well as run from the command line.
They are imported lazily, so `import pystoch` itself stays lightweight (it does
not pull in healpy/gwpy until you actually use a function that needs them).

```python
import pystoch

# detector geometry and antenna response
location = pystoch.gwdetectors("H1")["Location"]
gmst = pystoch.gmst_calculate(1369056000)

# build the parameter object from a parameters.ini file
params = pystoch.PystochParam("parameters.ini")

# spherical-harmonic index table, notching, spectral index, ...
lm = pystoch.complex_getlm(params.lmax)
```

The map-making pieces (`FramesetParam`, `FramesetIntermediates`,
`calculate_maps`, `calculate_fisher_diag`) are exposed the same way. See the
{doc}`api` reference for the complete list.
