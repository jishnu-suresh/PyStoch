# Installation

PyStoch is distributed on [PyPI](https://pypi.org/project/pystoch/):

```bash
pip install pystoch
```

This installs the `pystoch` Python package and three command-line tools:
`read_frames`, `convert_frames`, and `pystoch`.

## Frame-reading backend

Reading `.gwf` frames through `gwpy` additionally requires a GWF backend
(`lalframe` or `framel`). These are most reliably installed with conda or your
system package manager, e.g.:

```bash
conda install -c conda-forge python-lalframe
# or
pip install lalsuite   # provides lalframe on supported platforms
```

## The parameter file

PyStoch runs are configured through a `parameters.ini` file. A template ships
with the package; print its location with:

```bash
python -c "import pystoch, os; print(os.path.join(os.path.dirname(pystoch.__file__), 'data', 'parameters.ini'))"
```

Copy it into your working directory and edit it for your run (see
{doc}`parameters`).
