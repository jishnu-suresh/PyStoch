"""Tests for the shared logging setup and its cluster-hardening behaviour."""
import logging

import pytest

from pystoch import _logging as L


@pytest.fixture(autouse=True)
def _reset_loggers():
    # Clean handler state before and after each test (loggers are global).
    L._reset(L.info_logger)
    L._reset(L.error_logger)
    yield
    L._reset(L.info_logger)
    L._reset(L.error_logger)


def test_setup_logging_is_idempotent():
    L.setup_logging("", "")
    L.setup_logging("", "")
    L.setup_logging("", "")
    assert len(L.info_logger.handlers) == 1
    assert len(L.error_logger.handlers) == 1


def test_info_stdout_error_file(tmp_path):
    errf = tmp_path / "run.err"
    L.setup_logging("", str(errf))
    ih = L.info_logger.handlers[-1]
    eh = L.error_logger.handlers[-1]
    # info -> plain stream (stdout), error -> file
    assert isinstance(ih, logging.StreamHandler) and not isinstance(ih, logging.FileHandler)
    assert isinstance(eh, logging.FileHandler)
    L.error_logger.error("boom")
    eh.flush()
    assert "boom" in errf.read_text()


def test_info_to_log_file(tmp_path):
    logf = tmp_path / "run.log"
    L.setup_logging(str(logf), str(tmp_path / "e.err"))
    assert isinstance(L.info_logger.handlers[-1], logging.FileHandler)


def test_unwritable_error_file_falls_back_to_stderr(tmp_path):
    bad = tmp_path / "missing_dir" / "run.err"  # parent dir does not exist
    L.setup_logging("", str(bad))               # must NOT raise
    eh = L.error_logger.handlers[-1]
    assert isinstance(eh, logging.StreamHandler) and not isinstance(eh, logging.FileHandler)
    assert not bad.exists()


def test_unwritable_log_file_falls_back_to_stdout(tmp_path):
    bad = tmp_path / "missing_dir" / "run.log"
    L.setup_logging(str(bad), str(tmp_path / "ok.err"))  # must NOT raise
    ih = L.info_logger.handlers[-1]
    assert isinstance(ih, logging.StreamHandler) and not isinstance(ih, logging.FileHandler)
