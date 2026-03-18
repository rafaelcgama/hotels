from unittest.mock import MagicMock
from main import main


def test_main_success(mocker):
    """Full happy path — DB, driver, scraper, and insert all succeed."""
    mock_init_db = mocker.patch("main.init_db")
    mock_driver = MagicMock()
    mock_create_webdriver = mocker.patch(
        "main.create_webdriver", return_value=mock_driver
    )
    mock_collect = mocker.patch(
        "main.collect_hotel_prices",
        return_value={"Check_in": "2024-05-10", "Faro Hotel Taubaté": 250},
    )
    mock_insert = mocker.patch("main.insert_hotel_prices")

    main()

    mock_init_db.assert_called_once()
    mock_create_webdriver.assert_called_once()
    assert mock_collect.call_count > 0
    assert mock_insert.call_count > 0
    mock_driver.quit.assert_called_once()


def test_main_collect_prices_exception(mocker):
    """A single date-pair failure should be logged but not abort the whole run."""
    mocker.patch("main.init_db")
    mock_driver = MagicMock()
    mocker.patch("main.create_webdriver", return_value=mock_driver)
    mocker.patch("main.collect_hotel_prices", side_effect=Exception("Scraping failed"))
    mock_logger = mocker.patch("main.logger")

    main()

    assert mock_logger.error.called
    mock_driver.quit.assert_called_once()


def test_main_critical_exception(mocker):
    """A failure during WebDriver creation triggers a critical log and graceful exit."""
    mocker.patch("main.init_db")
    mocker.patch("main.create_webdriver", side_effect=Exception("WebDriver failed"))
    mock_logger = mocker.patch("main.logger")

    main()

    assert mock_logger.critical.called


def test_main_driver_always_quit(mocker):
    """WebDriver.quit() must be called even when collect_hotel_prices raises."""
    mocker.patch("main.init_db")
    mock_driver = MagicMock()
    mocker.patch("main.create_webdriver", return_value=mock_driver)
    mocker.patch("main.collect_hotel_prices", side_effect=Exception("Loop fail"))
    mocker.patch("main.logger")

    main()

    mock_driver.quit.assert_called_once()
