import sqlite3
from unittest.mock import MagicMock

from main import main


def test_main_orchestration_with_real_db(mocker, tmp_path):
    """
    End-to-End test: runs the full orchestrator with a real SQLite database.
    Only the WebDriver and Selenium scraping are mocked (can't hit Booking.com).
    The database layer runs for real against a temporary SQLite file.
    """
    # Point the DB to a temp file — real SQLite, not mocked
    test_db = str(tmp_path / "e2e_prices.db")
    mocker.patch("src.database.DB_PATH", test_db)
    mocker.patch("src.database._USE_POSTGRES", False)

    # Limit to 2 days so the test finishes fast
    mocker.patch("main.DAYS_AHEAD", 2)

    # Mock the WebDriver
    mock_driver = MagicMock()
    mocker.patch("main.create_webdriver", return_value=mock_driver)

    # Mock the scraper to return realistic data
    def fake_scrape(driver, city, checkin_date, checkout_date, hotel_competitors, retries):
        return {
            "Check_in": checkin_date,
            "Timestamp": "2024-05-01",
            "Faro Hotel Taubaté": 250,
            "Ibis Taubate": 180,
        }

    mocker.patch("main.collect_hotel_prices", side_effect=fake_scrape)

    # Run the full orchestrator
    main()

    # Verify: driver was created and cleaned up
    mock_driver.quit.assert_called_once()

    # Verify: real data was written to the real SQLite DB
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM hotel_prices")
    total_rows = cursor.fetchone()[0]
    # 2 date pairs x 2 hotels = 4 rows
    assert total_rows == 4

    cursor.execute("SELECT DISTINCT hotel_name FROM hotel_prices ORDER BY hotel_name")
    hotels = [row[0] for row in cursor.fetchall()]
    assert hotels == ["Faro Hotel Taubaté", "Ibis Taubate"]

    cursor.execute("SELECT price FROM hotel_prices WHERE hotel_name='Faro Hotel Taubaté'")
    prices = [row[0] for row in cursor.fetchall()]
    assert all(p == 250 for p in prices)

    conn.close()


def test_main_orchestration_partial_failure(mocker, tmp_path):
    """
    E2E: one date-pair fails, the rest still succeed and get written to the DB.
    """
    test_db = str(tmp_path / "e2e_prices.db")
    mocker.patch("src.database.DB_PATH", test_db)
    mocker.patch("src.database._USE_POSTGRES", False)
    mocker.patch("main.DAYS_AHEAD", 3)

    mock_driver = MagicMock()
    mocker.patch("main.create_webdriver", return_value=mock_driver)

    call_count = 0

    def fake_scrape_with_failure(driver, city, checkin_date, checkout_date, hotel_competitors, retries):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception("Simulated scraper failure")
        return {
            "Check_in": checkin_date,
            "Timestamp": "2024-05-01",
            "Faro Hotel Taubaté": 300,
        }

    mocker.patch("main.collect_hotel_prices", side_effect=fake_scrape_with_failure)

    main()

    mock_driver.quit.assert_called_once()

    # 3 date pairs, 1 failed => 2 succeeded x 1 hotel = 2 rows
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hotel_prices")
    total_rows = cursor.fetchone()[0]
    conn.close()

    assert total_rows == 2
