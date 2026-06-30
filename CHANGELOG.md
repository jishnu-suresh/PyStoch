# Changelog

All notable changes to PyStoch are documented in this file. The format is based
on [Keep a Changelog](https://keepachangelog.com/), and the project aims to
follow semantic versioning.

## [1.2.5] - 2026-06-30

### Fixed
- `f_min`/`f_max = 0` now correctly fall back to the full band available in the
  frames (`flow`/`fhigh`) instead of producing an empty frequency array.
- A single-row notch list no longer raises `NameError` (`desc`).
- A missing compressed HDF5 file now raises a clear, actionable error
  (`... Did you run convert_frames first?`) instead of a confusing `NameError`.

### Changed
- The ASCII-art banner uses raw strings, removing the invalid-escape-sequence
  `SyntaxWarning` (a future `SyntaxError`).

### Added
- A public top-level Python API: the main classes and functions
  (`PystochParam`, `calculate_maps`, `gwdetectors`, ...) are now importable
  directly from `pystoch`. They are loaded lazily, so `import pystoch` stays
  lightweight.
- Pinned conservative minimum dependency versions.
- A version-drift guard test (`__version__` must match `pyproject.toml`).

## [1.2.4]

### Added
- A test suite (unit tests for the pure functions, logging tests, and an
  end-to-end regression test) plus a GitHub Actions CI workflow.

### Changed
- Replaced all `from ... import *` star imports with explicit imports.
- Factored the duplicated CLI logging setup into a shared `pystoch._logging`
  helper, with cluster-safe fallback (logs to console if the log/error file
  cannot be opened) and idempotent setup.
- Decomposed the long `make_maps.main` into focused functions and made the
  overridable-parameter list a single source of truth.

### Removed
- Dead code (`make_notch_array_old`) and unused imports.

### Fixed
- `__version__` now matches the published distribution version.

## [1.2.3]

### Added
- Project logo, README status badges, and corrected project URLs
  (Homepage / Documentation / Source / Issues).

## [1.1.1]

### Fixed
- Removed `os.getlogin()`, which raised on headless / batch (cluster) runs with
  no controlling terminal.

## [1.1.0]

### Added
- First pip-installable packaging of the PyStoch pipeline, with the
  `read_frames`, `convert_frames`, and `pystoch` command-line tools.
