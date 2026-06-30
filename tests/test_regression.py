"""End-to-end regression tests against the frozen golden baselines.

Each test runs the full pipeline (read_frames -> convert_frames -> pystoch) on
the reference 5-frame H1L1 dataset with a fixed configuration and compares the
output pickles, array-by-array, against baseline/*.pkl.

These tests need the reference .gwf frames and a working GWF backend
(gwpy + lalframe), so they are skipped unless:
  * the env var PYSTOCH_TEST_FRAMES points to a directory with the 5 .gwf files, and
  * gwpy can be imported.
"""
import glob
import os
import pickle
import shutil
import subprocess
import tempfile

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "baseline")
FRAMES = os.environ.get("PYSTOCH_TEST_FRAMES", "")

IGNORE = {
    "computer", "datetime", "run_duration", "run_duration(cpu)", "user",
    "path", "output_map_path", "notch_list", "n_thread", "multi_thread",
}

_HEADER = "[parameters]\n"
_COMMON = """f_min: 20.0
f_max: 50.0
alpha: 0.6666666666666666
fRef: 25.0
multithreading: False
multi_threads: 1
frames_location: {frames_root}
output_map_location: ./output/
notching: False
notch_list: ./notch.txt
"""

CONFIG_DEFAULT = _HEADER + "nside: 4\npixel: True\nsph: True\nbeam: True\n" + _COMMON

CONFIG_NBR = _HEADER + (
    "nside: 4\npixel: True\nsph: False\nbeam: False\n"
    "nbr: True\nraHr: 16.33196388888889\ndecDeg: -15.640222222222222\n"
    "direction: scox1\n" + _COMMON
)

gwpy_ok = True
try:
    import gwpy  # noqa: F401
except Exception:
    gwpy_ok = False

requires_setup = pytest.mark.skipif(
    not (FRAMES and glob.glob(os.path.join(FRAMES, "*.gwf")) and gwpy_ok),
    reason="set PYSTOCH_TEST_FRAMES to the 5 reference .gwf files and install gwpy+lalframe",
)


def _compare(baseline_path, new_path):
    with open(baseline_path, "rb") as f:
        a = pickle.load(f)
    with open(new_path, "rb") as f:
        b = pickle.load(f)
    diffs = []
    for k in (set(a) - IGNORE) | (set(b) - IGNORE):
        if k not in a or k not in b:
            diffs.append(f"key {k!r} missing in one output")
            continue
        va, vb = a[k], b[k]
        if isinstance(va, np.ndarray) or isinstance(vb, np.ndarray):
            va, vb = np.asarray(va), np.asarray(vb)
            if va.shape != vb.shape or not np.array_equal(va, vb):
                diffs.append(f"{k}: arrays differ (shapes {va.shape} vs {vb.shape})")
        elif va != vb:
            diffs.append(f"{k}: {va!r} != {vb!r}")
    return diffs


def _need(*names):
    """Skip if any required baseline fixture is missing from baseline/."""
    missing = [n for n in names if not os.path.exists(os.path.join(BASELINE, n))]
    if missing:
        pytest.skip("baseline file(s) not present: " + ", ".join(missing))


def _run_pipeline(config_text):
    """Run the full pipeline in a temp dir and return its output directory."""
    work = tempfile.mkdtemp(prefix="pystoch_reg_")
    fr = os.path.join(work, "frames_root", "H1L1_test")
    os.makedirs(fr)
    os.makedirs(os.path.join(work, "output"))
    for f in glob.glob(os.path.join(FRAMES, "*.gwf")):
        shutil.copy(f, fr)
    with open(os.path.join(work, "parameters.ini"), "w") as fh:
        fh.write(config_text.format(frames_root=os.path.join(work, "frames_root")))
    for cmd in (["read_frames"], ["convert_frames"], ["pystoch"]):
        subprocess.run(cmd, cwd=work, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return work


@requires_setup
def test_default_pipeline_matches_baseline():
    _need("Pixel_baseline.pkl", "SpH_baseline.pkl")
    work = _run_pipeline(CONFIG_DEFAULT)
    try:
        out = os.path.join(work, "output")
        pix = glob.glob(os.path.join(out, "Pixel_*.pkl"))[0]
        sph = glob.glob(os.path.join(out, "SpH_*.pkl"))[0]
        diffs = _compare(os.path.join(BASELINE, "Pixel_baseline.pkl"), pix)
        diffs += _compare(os.path.join(BASELINE, "SpH_baseline.pkl"), sph)
        assert not diffs, "Default output differs from baseline:\n" + "\n".join(diffs)
    finally:
        shutil.rmtree(work, ignore_errors=True)


@requires_setup
def test_nbr_pipeline_matches_baseline():
    _need("NBR_Pixel_NBR_baseline.pkl", "NBR_Pixel_baseline.pkl")
    work = _run_pipeline(CONFIG_NBR)
    try:
        out = os.path.join(work, "output")
        pix_nbr = glob.glob(os.path.join(out, "Pixel_NBR_*.pkl"))[0]
        pix = [f for f in glob.glob(os.path.join(out, "Pixel_*.pkl"))
               if "Pixel_NBR_" not in os.path.basename(f)][0]
        diffs = _compare(os.path.join(BASELINE, "NBR_Pixel_NBR_baseline.pkl"), pix_nbr)
        diffs += _compare(os.path.join(BASELINE, "NBR_Pixel_baseline.pkl"), pix)
        assert not diffs, "NBR output differs from baseline:\n" + "\n".join(diffs)
    finally:
        shutil.rmtree(work, ignore_errors=True)
