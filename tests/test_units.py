"""Unit tests for PyStoch's pure (deterministic) functions.

These lock the current numerical behaviour of the building-block functions and
require no GW frame data or frame backend (gwpy/lalframe) -- only numpy/healpy/
scipy/astropy -- so they run fast in CI.
"""
import numpy as np
import pytest

from pystoch import detectors as D
from pystoch import pystoch_functions as F


# --------------------------------------------------------------------------- #
# detectors
# --------------------------------------------------------------------------- #
def test_gwdetectors_H1_location():
    loc = D.gwdetectors("H1")["Location"]
    np.testing.assert_allclose(
        loc, [-2161414.92635999, -3834695.17889000, 4600350.22664000]
    )


def test_gwdetectors_aliases_match():
    ref = D.gwdetectors("H1")["Location"]
    for name in ("H", "LHO", "H2"):
        assert np.array_equal(D.gwdetectors(name)["Location"], ref)


def test_gmst_calculate_matches_closed_form():
    gps = 1.2e9
    expected = 7.292115838261945e-05 * (gps - 630720013.0) + 1.7446930362926378
    assert D.gmst_calculate(gps) == pytest.approx(expected)


def test_display_time():
    assert D.display_time(3661) == "1 hour, 1 minute"
    assert D.display_time(0) == ""


def test_same_detector_zero_time_delay():
    _, td = D.combined_antenna_response_t_delay(
        "H1", "H1", np.array([[1.2e9]]), 0.5, 1.0
    )
    assert float(np.squeeze(td)) == pytest.approx(0.0, abs=1e-12)


def test_unknown_polarization_exits():
    with pytest.raises(SystemExit):
        D.combined_antenna_response_t_delay(
            "H1", "L1", np.array([[1.2e9]]), 0.5, 1.0, GW_polarization="Z"
        )


# --------------------------------------------------------------------------- #
# spherical-harmonic index helpers
# --------------------------------------------------------------------------- #
def test_complex_getlm_lmax2_exact():
    expected = np.array(
        [[2, 2, 1, 0, 1, 2, 1, 2, 2],
         [-2, -1, -1, 0, 0, 0, 1, 1, 2]]
    )
    assert np.array_equal(F.complex_getlm(2), expected)


@pytest.mark.parametrize("lmax", [1, 4, 8, 16])
def test_complex_getlm_shape(lmax):
    out = F.complex_getlm(lmax)
    assert out.shape == (2, (lmax + 1) ** 2)
    # m runs from -lmax..lmax, l from |m|..lmax
    l, m = out
    assert np.all(np.abs(m) <= l)
    assert l.max() == lmax and m.min() == -lmax and m.max() == lmax


def test_fisher_zeros_structure():
    lmax = 3
    q = (lmax + 1) ** 2
    fz = F.fisher_zeros(np.ones((q, q)))
    l = F.complex_getlm(lmax)[0]
    odd = (l[:, None] + l[None, :]) % 2 == 1
    assert np.all(fz[odd] == 0.0)
    assert np.all(fz[~odd] == 1.0)


def test_part_alm_reconstructs_input():
    lmax = 4
    q = (lmax + 1) ** 2
    rng = np.random.default_rng(0)
    alm = rng.standard_normal(q) + 1j * rng.standard_normal(q)
    a_real, a_imag = F.part_alm(alm)
    np.testing.assert_allclose(a_real + a_imag, alm, atol=1e-12)
    assert len(a_real) == q and len(a_imag) == q


# --------------------------------------------------------------------------- #
# spectral index and notching
# --------------------------------------------------------------------------- #
def test_spectral_index_constant():
    Hf = np.array([[10.0, 2.0], [100.0, 2.0]])  # flat in log-log
    np.testing.assert_allclose(F.spectral_index(np.array([20.0, 50.0]), Hf), [2.0, 2.0])


def test_spectral_index_power_law():
    # H(f) = f^2  -> log H = 2 log f ; check an interpolated point
    f = np.array([10.0, 100.0])
    Hf = np.column_stack([f, f ** 2])
    out = F.spectral_index(np.array([50.0]), Hf)
    np.testing.assert_allclose(out, [50.0 ** 2], rtol=1e-12)


def test_make_notch_array_no_notching():
    fa = np.linspace(20.0, 30.0, 11)
    out = F.make_notch_array(fa, False, None)
    assert out.dtype == bool and out.size == fa.size and out.all()


def test_make_notch_array_with_list(tmp_path):
    fa = np.arange(20.0, 30.0, 0.5)
    notch = tmp_path / "notch.txt"
    notch.write_text("22.0,23.0\n26.0,26.4\n")  # two ranges (avoids 1-row branch)
    out = F.make_notch_array(fa, True, str(notch))
    assert out.dtype == bool
    # an interior bin of the [22,23] notch is removed
    assert not out[np.argmin(np.abs(fa - 22.5))]
    # a bin far from any notch is kept
    assert out[np.argmin(np.abs(fa - 20.0))]
