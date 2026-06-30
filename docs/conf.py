# Configuration file for the Sphinx documentation builder.
import os
import sys

# Make the package importable for autodoc (repo root contains the pystoch/ package).
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------
project = "PyStoch"
copyright = "2025, Anirban Ain, Jishnu Suresh, Sudhagar Suyamprakasam, Sanjit Mitra"
author = "Anirban Ain, Jishnu Suresh, Sudhagar Suyamprakasam, Sanjit Mitra"

try:
    from pystoch import __version__ as release
except Exception:
    release = "1.1.1"
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",      # understands NumPy-style docstrings
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",              # Markdown support
]

# Heavy / compiled scientific dependencies are mocked so the docs build
# without installing them on Read the Docs.
autodoc_mock_imports = [
    "numpy", "scipy", "healpy", "astropy", "h5py", "tqdm", "gwpy",
    "lal", "lalframe",
]

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
napoleon_numpy_docstring = True
napoleon_google_docstring = False

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "healpy": ("https://healpy.readthedocs.io/en/latest/", None),
}

# -- HTML output -------------------------------------------------------------
html_theme = "furo"
html_title = f"PyStoch {release}"
