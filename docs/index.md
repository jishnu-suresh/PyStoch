# PyStoch

**A Python-based code for Stochastic Gravitational-Wave Background (SGWB)
mapping from gravitational-wave interferometer data.**

PyStoch makes SGWB anisotropy maps from *folded* stochastic interferometric
data (FSID). It supports map-making in the **pixel** (HEALPix) basis and the
**spherical-harmonic (SpH)** basis, optional **broadband beam / Fisher**
computation, frequency **notching**, narrowband-radiometer (**NBR**) analysis,
and **injection** studies.

```{toctree}
:maxdepth: 2
:caption: Contents

installation
usage
parameters
api
citing
```

## Pipeline at a glance

PyStoch is run as three command-line steps:

1. `read_frames` — scan the `.gwf` framesets and collect their parameters into `framesets.ini`.
2. `convert_frames` — convert the `.gwf` frames into a compressed HDF5 file (faster to read).
3. `pystoch` — make the maps; results are written as pickle (`.pkl`) files.

See {doc}`usage` for the full walkthrough.
