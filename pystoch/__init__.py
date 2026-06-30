"""PyStoch - a Python-based code for SGWB mapping from GW interferometer data.

Input is folded stochastic interferometric data (FSID).

Authors: Anirban Ain, Jishnu Suresh, Sudhagar Suyamprakasam and Sanjit Mitra.

Public API
----------
The main building blocks are available directly from the top level, e.g.::

    import pystoch
    params = pystoch.PystochParam("parameters.ini")
    H1 = pystoch.gwdetectors("H1")

These names are imported lazily (only when first accessed), so ``import pystoch``
itself stays lightweight and does not pull in healpy/gwpy/etc.
"""

# Keep this in sync with the version in pyproject.toml.
# tests/test_version.py fails the build if the two ever drift apart.
__version__ = "1.2.5"

# name -> submodule it lives in (imported on first access; see __getattr__)
_LAZY = {
    # parameters, framesets, results, and map-making
    "PystochParam": "pystoch.pystoch_class_and_mapping",
    "FramesetParam": "pystoch.pystoch_class_and_mapping",
    "FramesetIntermediates": "pystoch.pystoch_class_and_mapping",
    "PystochResults": "pystoch.pystoch_class_and_mapping",
    "calculate_maps": "pystoch.pystoch_class_and_mapping",
    "calculate_maps_wrapper": "pystoch.pystoch_class_and_mapping",
    "calculate_fisher_diag": "pystoch.pystoch_class_and_mapping",
    # frame loading, spectral index, notching, SpH helpers
    "load_frame_data": "pystoch.pystoch_functions",
    "seed_matrices": "pystoch.pystoch_functions",
    "make_notch_array": "pystoch.pystoch_functions",
    "spectral_index": "pystoch.pystoch_functions",
    "complex_getlm": "pystoch.pystoch_functions",
    "complex_map2alm": "pystoch.pystoch_functions",
    "part_alm": "pystoch.pystoch_functions",
    "fisher_zeros": "pystoch.pystoch_functions",
    # detector geometry and antenna response
    "gwdetectors": "pystoch.detectors",
    "gmst_calculate": "pystoch.detectors",
    "combined_antenna_response_t_delay": "pystoch.detectors",
    "arrival_time": "pystoch.detectors",
    "ehat": "pystoch.detectors",
    "display_time": "pystoch.detectors",
}

__all__ = ["__version__", *sorted(_LAZY)]


def __getattr__(name):
    """Lazily import and cache a public API name from its submodule (PEP 562)."""
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    obj = getattr(importlib.import_module(module), name)
    globals()[name] = obj  # cache so subsequent lookups skip __getattr__
    return obj


def __dir__():
    return sorted([*globals(), *_LAZY])
