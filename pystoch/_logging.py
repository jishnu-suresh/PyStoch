"""Shared logging setup for the PyStoch command-line tools.

The ``info_logger`` and ``error_logger`` are shared by name across all CLIs
(``read_frames``, ``convert_frames``, ``pystoch``); ``setup_logging`` attaches
the standard handlers.

Cluster-hardening notes
-----------------------
* If a requested log/error file cannot be opened (e.g. a read-only or networked
  working directory on a compute node), PyStoch falls back to the console
  (stdout/stderr) with a warning instead of crashing before the run starts.
* ``setup_logging`` is idempotent: calling it again replaces the handlers rather
  than stacking duplicates (which would otherwise double every log line when a
  command's ``main`` runs more than once in the same process).

On a writable working directory the behaviour is identical to the original
inline setup (info -> stdout or log file, error -> error file).
"""
import logging
import sys

# Separate loggers for info and error messages (shared by logger name).
info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')

# Prevent log messages from propagating to the root logger.
info_logger.propagate = False
error_logger.propagate = False

_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'


def _file_handler(path):
    """Return a FileHandler for ``path`` (append mode), or ``None`` if it
    cannot be opened (so the caller can fall back to the console)."""
    try:
        return logging.FileHandler(path, mode='a')
    except OSError as exc:
        sys.stderr.write(
            f"Warning: could not open log file {path!r} ({exc}); "
            f"logging to console instead.\n"
        )
        return None


def _reset(logger):
    """Detach and close any handlers already attached to ``logger``."""
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass


def setup_logging(log_file='', err_file=''):
    """Attach the standard info and error handlers.

    * info  -> ``log_file`` (append) if given and writable, otherwise stdout
    * error -> ``err_file`` (append) if given and writable, otherwise stderr

    Safe to call more than once: previous handlers are replaced, not stacked.
    """
    _reset(info_logger)
    _reset(error_logger)
    formatter = logging.Formatter(_FORMAT)

    # Info handler: log file if requested (and writable), else stdout.
    info_handler = _file_handler(log_file) if log_file else None
    if info_handler is None:
        info_handler = logging.StreamHandler(sys.stdout)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    info_logger.addHandler(info_handler)
    info_logger.setLevel(logging.INFO)

    # Error handler: error file if requested (and writable), else stderr.
    err_handler = _file_handler(err_file) if err_file else None
    if err_handler is None:
        err_handler = logging.StreamHandler(sys.stderr)
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(formatter)
    error_logger.addHandler(err_handler)
    error_logger.setLevel(logging.ERROR)
