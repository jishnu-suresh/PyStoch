# Parameter reference

PyStoch runs are configured by a `parameters.ini` file under a single
`[parameters]` section. The descriptions and defaults below are taken directly
from the code (`PystochParam`). The parameters `nside`, `pixel`, `sph`, `beam`,
and `f_max` are **required**.

## Map basis and resolution

| Parameter | Type | Default | Description |
|---|---|---|---|
| `nside` | int | *(required)* | HEALPix `nside` (a power of 2). |
| `pixel` | bool | *(required)* | Compute maps in the pixel (HEALPix) basis. |
| `sph` | bool | *(required)* | Compute maps in the spherical-harmonic basis. |
| `lmax` | int | `2 * nside` | Maximum multipole for the SpH basis. |
| `beam` | bool | `False` | Compute the broadband beam / full Fisher matrix. |

## Frequency range and spectral index

| Parameter | Type | Default | Description |
|---|---|---|---|
| `f_min` | float | `20.0` | Minimum frequency (Hz) for which maps are made. |
| `f_max` | float | *(required)* | Maximum frequency (Hz) for which maps are made. |
| `alpha` | float | `None` | Power-law spectral index. Either `alpha` or `Hf_file` must be given. |
| `fRef` | float | `25.0` | Reference frequency (Hz) of the analysis. |
| `Hf_file` | str | `None` | Path to a text file giving `H(f)` directly (overrides `alpha`). |
| `GW_polarization` | str | `T` | GW polarization. Tensor (`T`) is the currently active option. |

## Notching

| Parameter | Type | Default | Description |
|---|---|---|---|
| `notching` | bool | `False` | Enable frequency notching. |
| `notch_list` | str | `None` | Path to the notch-list file (required when `notching` is `True`). |

## Narrowband radiometer (NBR)

When `nbr` is `True`, PyStoch forces `pixel=True` and `sph=beam=injection=False`,
and `raHr`, `decDeg`, and `direction` must all be provided.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `nbr` | bool | `False` | Perform a narrowband-radiometer analysis. |
| `raHr` | float | `None` | Right ascension of the source (hours). |
| `decDeg` | float | `None` | Declination of the source (degrees). |
| `direction` | str | `None` | Name/label of the source direction. |

## Injection

| Parameter | Type | Default | Description |
|---|---|---|---|
| `injection` | bool | `False` | Perform an injection study. |
| `inj_map_path` | str | `None` | Path to a text HEALPix map for injection (required when `injection` is `True`; regridded to `nside`). |

## Threading and I/O

| Parameter | Type | Default | Description |
|---|---|---|---|
| `multithreading` | bool | `True` | Use multithreading. |
| `multi_threads` | int | `4` | Number of threads (`0` uses all available CPUs). |
| `frames_location` | str | — | Parent directory of the framesets (used by `read_frames`). |
| `output_map_location` | str | *(required)* | Directory where results are written. |

## Frame conversion channels

These optional fields control which frame channels `convert_frames` reads
(defaults shown):

| Parameter | Default | Description |
|---|---|---|
| `csd_channel_real` | `ReCSD` | Real part of the cross-spectral density. |
| `csd_channel_imaginary` | `ImCSD` | Imaginary part of the cross-spectral density. |
| `psd_combined` | `False` | Whether a single combined PSD channel is stored. |
| `psd_channel` | `AdjacentPSD` | PSD channel name. |
