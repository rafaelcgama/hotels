import os
import sqlite3
import pytest
from src.pipeline.database import init_db, insert_hotel_prices
from src.config import DB_PATH

@pytest.fixture
def mock_db_path(monkeypatch, tmp_path):
    """Overrides DB_PATH to use a temporary SQLite file for testing."""
    test_db = tmp_path / "test_prices.db"
    monkeypatch.setattr("src.pipeline.database.DB_PATH", str(test_db))
    return str(test_db)

def test_init_db(mock_db_path):
    """Verify that init_db creates the file and appropriate schema."""
    init_db()
    
    assert os.path.exists(mock_db_path)
    
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hotel_prices'")
    assert cursor.fetchone()[0] == 'hotel_prices'
    conn.close()

def test_insert_hotel_prices(mock_db_path):
    """Verify inserting and updating capabilities of the schema."""
    init_db()
    
    fetch_date = "2024-05-01"
    city = "Taubate"
    checkin_date = "2024-05-10"
    prices = {
        "Check_in": checkin_date,
        "Timestamp": fetch_date,
        "Faro Hotel Taubaté": 250,
        "Ibis Taubate": None
    }
    
    insert_hotel_prices(fetch_date, city, checkin_date, prices)
    
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT hotel_name, price FROM hotel_prices")
    rows = cursor.fetchall()
    conn.close()
    
    # We should have two inserted records
    assert len(rows) == 2
    
    # Converting array of tuples to dict for easy assert
    result_dict = {k: v for k, v in rows}
    
    assert result_dict["Faro Hotel Taubaté"] == 250
    assert result_dict["Ibis Taubate"] is None
    
    # Test UPSERT behavior 
    # If we insert again on the same fetch_date + city + checkin + hotel with different price, it updates
    updated_prices = {"Faro Hotel Taubaté": 300}
    insert_hotel_prices(fetch_date, city, checkin_date, updated_prices)
    
    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT hotel_name, price FROM hotel_prices WHERE hotel_name='Faro Hotel Taubaté'")
    update_row = cursor.fetchone()
    conn.close()
    
    assert update_row[1] == 300
