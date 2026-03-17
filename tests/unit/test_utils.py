import logging
import os

from src.config import HOTEL_COMPETITORS, CITY, DAYS_AHEAD, DATA_DIR, LOGS_DIR
from src.scraper.booking_scraper import normalize_string


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------
def test_config_loads_defaults():
    """Verify that configuration loads correctly even if .env is missing."""
    assert CITY is not None
    assert DAYS_AHEAD > 0
    assert isinstance(HOTEL_COMPETITORS, list)
    assert len(HOTEL_COMPETITORS) > 0
    assert "Faro Hotel Taubaté" in HOTEL_COMPETITORS


def test_config_types():
    assert isinstance(CITY, str)
    assert isinstance(DAYS_AHEAD, int)


def test_config_dirs_are_strings():
    assert isinstance(DATA_DIR, str)
    assert isinstance(LOGS_DIR, str)


# ---------------------------------------------------------------------------
# Normalize string tests
# ---------------------------------------------------------------------------
def test_normalize_string():
    """Verify string normalization drops accents and lowercases."""
    assert normalize_string("Taubaté") == "taubate"
    assert normalize_string("  São Paulo  ") == "sao paulo"
    assert normalize_string("Faro Hotel Taubaté") == "faro hotel taubate"


def test_normalize_string_already_ascii():
    assert normalize_string("hello world") == "hello world"


def test_normalize_string_empty():
    assert normalize_string("") == ""


# ---------------------------------------------------------------------------
# Logger tests
# ---------------------------------------------------------------------------
def test_get_logger_returns_logger(tmp_path, monkeypatch):
    """get_logger returns a logging.Logger with file + console handlers."""
    log_file = str(tmp_path / "test.log")
    monkeypatch.setattr("src.utils.logger.LOG_FILE", log_file)

    # Force fresh logger by using a unique name
    from src.utils.logger import get_logger

    logger = get_logger("test_logger_fresh")

    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO
    # Should have exactly 2 handlers (file + console)
    assert len(logger.handlers) == 2


def test_get_logger_does_not_duplicate_handlers(tmp_path, monkeypatch):
    """Calling get_logger twice with same name must not add duplicate handlers."""
    log_file = str(tmp_path / "test.log")
    monkeypatch.setattr("src.utils.logger.LOG_FILE", log_file)

    from src.utils.logger import get_logger

    name = "test_no_dup"
    logger1 = get_logger(name)
    logger2 = get_logger(name)

    assert logger1 is logger2
    assert len(logger2.handlers) == 2


def test_logger_writes_to_file(tmp_path, monkeypatch):
    """Logger must write messages to the configured log file."""
    log_file = str(tmp_path / "test.log")
    monkeypatch.setattr("src.utils.logger.LOG_FILE", log_file)

    from src.utils.logger import get_logger

    logger = get_logger("test_file_write")
    logger.info("hello from test")

    assert os.path.exists(log_file)
    with open(log_file) as f:
        content = f.read()
    assert "hello from test" in content
