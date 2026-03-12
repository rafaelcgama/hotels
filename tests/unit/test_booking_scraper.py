import os
from unittest.mock import MagicMock
from selenium.common.exceptions import TimeoutException, WebDriverException

from src.scraper.booking_scraper import (
    create_webdriver,
    wait_for_page_load,
    collect_hotel_prices,
)


def test_create_webdriver(mocker):
    # Mock HEADLESS to True for consistent test behavior
    mocker.patch("src.scraper.booking_scraper.HEADLESS", True)
    mock_options = mocker.patch("src.scraper.booking_scraper.Options")
    mock_webdriver = mocker.patch("src.scraper.booking_scraper.WebDriver")

    # Test with CHROME_BINARY set
    mocker.patch.dict(os.environ, {"CHROME_BINARY": "/path/to/chrome"})
    mocker.patch("os.path.exists", return_value=True)

    driver = create_webdriver()

    assert mock_webdriver.called
    # Verify headless was added
    mock_options.return_value.add_argument.assert_any_call("--headless=new")
    assert driver.maximize_window.called


def test_create_webdriver_headful(mocker):
    # Mock HEADLESS to False
    mocker.patch("src.scraper.booking_scraper.HEADLESS", False)
    mock_options = mocker.patch("src.scraper.booking_scraper.Options")
    mocker.patch("src.scraper.booking_scraper.WebDriver")

    create_webdriver()

    # Verify headless was NOT added
    args = [
        call[0][0] for call in mock_options.return_value.add_argument.call_args_list
    ]
    assert "--headless=new" not in args


def test_wait_for_page_load_success(mocker):
    mock_wait = mocker.patch("src.scraper.booking_scraper.WebDriverWait")
    mock_until = MagicMock(return_value=True)
    mock_wait.return_value.until = mock_until

    driver = MagicMock()
    result = wait_for_page_load(driver)

    assert result is True
    assert mock_until.called


def test_wait_for_page_load_timeout(mocker):
    mock_wait = mocker.patch("src.scraper.booking_scraper.WebDriverWait")
    mock_wait.return_value.until.side_effect = TimeoutException()

    driver = MagicMock()
    result = wait_for_page_load(driver)

    assert result is False


def test_wait_for_page_load_exception(mocker):
    mock_wait = mocker.patch("src.scraper.booking_scraper.WebDriverWait")
    mock_wait.return_value.until.side_effect = Exception("Generic error")

    driver = MagicMock()
    result = wait_for_page_load(driver)

    assert result is False


def test_collect_hotel_prices_success(mocker):
    mocker.patch("src.scraper.booking_scraper.wait_for_page_load", return_value=True)

    driver = MagicMock()

    mock_hotel_1 = MagicMock()
    mock_name_1 = MagicMock()
    # The scraper returns the raw text from the page; normalization handles accent matching
    mock_name_1.text = "Faro Hotel Taubaté"
    mock_price_1 = MagicMock()
    mock_price_1.text = "R$ 250"

    mock_hotel_1.find_element.return_value = mock_name_1
    mock_hotel_1.find_elements.return_value = [mock_price_1]

    mock_hotel_2 = MagicMock()
    mock_name_2 = MagicMock()
    mock_name_2.text = "Unknown Hotel"  # Not a competitor — should be ignored
    mock_hotel_2.find_element.return_value = mock_name_2

    driver.find_elements.return_value = [mock_hotel_1, mock_hotel_2]

    city = "Taubate"
    checkin = "2024-05-10"
    checkout = "2024-05-11"
    # Names stored exactly as supplied — no .title() mangling
    competitors = ["Faro Hotel Taubaté", "Ibis Taubate"]

    result = collect_hotel_prices(driver, city, checkin, checkout, competitors)

    assert result["Check_in"] == checkin
    assert "Timestamp" in result
    # Name preserved exactly as in the competitors list
    assert result["Faro Hotel Taubaté"] == 250
    assert result["Ibis Taubate"] is None


def test_collect_hotel_prices_page_load_fail(mocker):
    # Mock to always return False for page load
    mocker.patch("src.scraper.booking_scraper.wait_for_page_load", return_value=False)
    mocker.patch("time.sleep")  # To avoid actually sleeping in tests

    driver = MagicMock()
    competitors = ["Faro Hotel Taubaté"]

    result = collect_hotel_prices(
        driver, "Taubate", "2024-05-10", "2024-05-11", competitors, retries=1
    )

    # Should retry and then return with None for prices
    assert result["Faro Hotel Taubaté"] is None
    assert driver.get.call_count == 2  # Initial + 1 retry


def test_collect_hotel_prices_webdriver_exception(mocker):
    driver = MagicMock()
    driver.get.side_effect = WebDriverException("Connection refused")
    mocker.patch("time.sleep")

    competitors = ["Faro Hotel Taubaté"]
    result = collect_hotel_prices(
        driver, "Taubate", "2024-05-10", "2024-05-11", competitors, retries=1
    )

    assert result["Faro Hotel Taubaté"] is None
    assert driver.get.call_count == 2


def test_collect_hotel_prices_element_exception(mocker):
    mocker.patch("src.scraper.booking_scraper.wait_for_page_load", return_value=True)

    driver = MagicMock()

    mock_hotel = MagicMock()
    # Simulate exception when finding name
    mock_hotel.find_element.side_effect = Exception("Element not found")
    driver.find_elements.return_value = [mock_hotel]

    competitors = ["Faro Hotel Taubaté"]
    result = collect_hotel_prices(
        driver, "Taubate", "2024-05-10", "2024-05-11", competitors, retries=0
    )

    assert result["Faro Hotel Taubaté"] is None
