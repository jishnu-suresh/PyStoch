"""Edge-case tests for frame loading and notching (the fixed latent bugs).

These cover paths the end-to-end regression does not exercise:
  * a single-row notch list,
  * f_min/f_max == 0 meaning "use the full available band",
  * a missing compressed HDF5 file.
"""
import os
from types import SimpleNamespace

import h5py
import numpy as np
import pytest

from pystoch import pystoch_functions as F


# --------------------------------------------------------------------------- #
# notching: single-row list must not raise NameError ('desc')
# --------------------------------------------------------------------------- #
def test_make_notch_array_single_row(tmp_path):
    fa = np.arange(20.0, 30.0, 0.5)
    notch = tmp_path / "notch.txt"
    notch.write_text("22.5,23.5\n")  # exactly ONE row -> loadtxt returns scalars
    out = F.make_notch_array(fa, True, str(notch))  # previously raised NameError: desc
    assert out.dtype == bool
    assert not out[np.argmin(np.abs(fa - 23.0))]   # inside the notch -> removed
    assert out[np.argmin(np.abs(fa - 20.0))]       # far away -> kept


# --------------------------------------------------------------------------- #
# load_frame_data: f_min/f_max == 0 -> full band; missing file -> clear error
# --------------------------------------------------------------------------- #
def _write_frames(path, baseline, n_time, n_freq):
    fname = os.path.join(path, baseline + "_compressed.hdf5")
    with h5py.File(fname, "w") as h:
        h.create_dataset("csd", data=np.zeros((n_time, n_freq), dtype=complex))
        h.create_dataset("sigma_sq_inv", data=np.ones((n_time, n_freq)))
        h.create_dataset("gps_times_mid", data=np.zeros((n_time, 1)))


def _frame_param(path):
    # flow=20, fhigh=24, deltaF=1 -> f_data = [20,21,22,23,24]
    return SimpleNamespace(flow=20.0, fhigh=24.0, deltaF=1.0,
                           path=str(path), ifo1="H1", ifo2="L1")


def test_fmax_zero_uses_full_band(tmp_path):
    _write_frames(tmp_path, "H1L1", n_time=3, n_freq=5)
    fp = _frame_param(tmp_path)
    params = SimpleNamespace(f_min=21.0, f_max=0)   # f_max=0 -> up to fhigh (24)
    _, f_all, _, _ = F.load_frame_data(params, fp, "ds")
    assert np.allclose(f_all, [21.0, 22.0, 23.0, 24.0])


def test_fmin_zero_uses_full_band(tmp_path):
    _write_frames(tmp_path, "H1L1", n_time=3, n_freq=5)
    fp = _frame_param(tmp_path)
    params = SimpleNamespace(f_min=0, f_max=22.0)    # f_min=0 -> from flow (20)
    _, f_all, _, _ = F.load_frame_data(params, fp, "ds")
    assert np.allclose(f_all, [20.0, 21.0, 22.0])


def test_explicit_band_unchanged(tmp_path):
    # non-zero bounds behave exactly as before (regression-equivalent)
    _write_frames(tmp_path, "H1L1", n_time=3, n_freq=5)
    fp = _frame_param(tmp_path)
    params = SimpleNamespace(f_min=21.0, f_max=23.0)
    _, f_all, _, _ = F.load_frame_data(params, fp, "ds")
    assert np.allclose(f_all, [21.0, 22.0, 23.0])


def test_missing_file_raises_clear_error(tmp_path):
    fp = _frame_param(tmp_path)            # tmp_path has no hdf5
    params = SimpleNamespace(f_min=20.0, f_max=24.0)
    with pytest.raises(FileNotFoundError) as exc:
        F.load_frame_data(params, fp, "ds")
    assert "convert_frames" in str(exc.value)
