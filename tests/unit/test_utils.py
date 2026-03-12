from src.config import HOTEL_COMPETITORS, CITY, DAYS_AHEAD
from src.scraper.booking_scraper import normalize_string


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


def test_normalize_string():
    """Verify string normalization drops accents and lowercase."""
    assert normalize_string("Taubaté") == "taubate"
    assert normalize_string("  São Paulo  ") == "sao paulo"
    assert normalize_string("Faro Hotel Taubaté") == "faro hotel taubate"
