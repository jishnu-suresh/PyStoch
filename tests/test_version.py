"""Guard against version drift between pystoch/__init__.py and pyproject.toml.

This is exactly the failure that shipped once before (pyproject said 1.2.3 while
__init__ still said 1.1.3): the two version strings must always match.
"""
import pathlib
import re

import pystoch

PYPROJECT = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"


def _pyproject_version():
    text = PYPROJECT.read_text()
    # the first `version = "..."` under [project]
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert m, "could not find version in pyproject.toml"
    return m.group(1)


def test_version_matches_pyproject():
    assert pystoch.__version__ == _pyproject_version(), (
        f"__version__ ({pystoch.__version__}) != pyproject.toml "
        f"version ({_pyproject_version()}) -- keep them in sync"
    )
