"""Tests for the top-level public API (lazy re-exports)."""
import subprocess
import sys

import pystoch


def test_public_names_resolve_to_submodule_objects():
    from pystoch import pystoch_class_and_mapping as M
    from pystoch import pystoch_functions as F
    from pystoch import detectors as D

    assert pystoch.PystochParam is M.PystochParam
    assert pystoch.calculate_maps is M.calculate_maps
    assert pystoch.make_notch_array is F.make_notch_array
    assert pystoch.gwdetectors is D.gwdetectors
    # `from pystoch import name` must also work (exercises __getattr__)
    from pystoch import FramesetParam, complex_getlm, gmst_calculate  # noqa: F401


def test_all_lists_public_names():
    assert "PystochParam" in pystoch.__all__
    assert "gwdetectors" in pystoch.__all__
    assert "__version__" in pystoch.__all__
    # everything advertised in __all__ must actually be accessible
    for name in pystoch.__all__:
        getattr(pystoch, name)


def test_unknown_attribute_raises():
    import pytest
    with pytest.raises(AttributeError):
        pystoch.does_not_exist


def test_import_pystoch_is_lightweight():
    # `import pystoch` must NOT eagerly import the heavy scientific stack.
    code = (
        "import sys, pystoch;"
        "assert pystoch.__version__;"
        "assert 'healpy' not in sys.modules, 'healpy imported eagerly';"
        "assert 'gwpy' not in sys.modules, 'gwpy imported eagerly';"
        "print('ok')"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_lazy_access_triggers_import():
    code = (
        "import sys, pystoch;"
        "assert 'pystoch.pystoch_class_and_mapping' not in sys.modules;"
        "pystoch.PystochParam;"
        "assert 'pystoch.pystoch_class_and_mapping' in sys.modules;"
        "print('ok')"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
