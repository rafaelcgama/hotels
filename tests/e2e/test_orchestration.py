from unittest.mock import MagicMock

# Import the orchestrator's main flow
from main import main


def test_main_orchestration(mocker):
    """
    End-to-End Test for the Orchestrator loop without hitting actual external services.
    We mock the Scraper, Database dependencies, and the Email mechanism.
    """

    # 1. Mock DB Initialization
    mock_init_db = mocker.patch("main.init_db")

    # 2. Mock the Webdriver creation
    mock_driver_instance = MagicMock()
    mock_create_webdriver = mocker.patch(
        "main.create_webdriver", return_value=mock_driver_instance
    )

    # 3. Mock the Scraper loop
    # Simulate scraper returning valid dictionaries
    mock_collect = mocker.patch(
        "main.collect_hotel_prices",
        return_value={"Check_in": "2024-05-10", "Faro Hotel Taubaté": 300},
    )

    # 4. Mock the DB ingestion function
    mock_insert_prices = mocker.patch("main.insert_hotel_prices")

    # Run the orchestrator!
    main()

    # Validations
    mock_init_db.assert_called_once()
    mock_create_webdriver.assert_called_once()

    # Expect drivers to be closed
    mock_driver_instance.quit.assert_called_once()

    # Expect the scraper to be called explicitly
    assert mock_collect.call_count > 0
    assert mock_insert_prices.call_count > 0
