import os
import sqlite3
import pytest
from src.database import init_db, insert_hotel_prices, get_db_connection


@pytest.fixture
def mock_db_path(monkeypatch, tmp_path):
    """
    Overrides DB_PATH and ensures DATABASE_URL is empty so the
    tests always run against a clean temporary SQLite file.
    """
    test_db = tmp_path / "test_prices.db"
    monkeypatch.setattr("src.database.DB_PATH", str(test_db))
    monkeypatch.setattr("src.database._USE_POSTGRES", False)
    return str(test_db)


# ---------------------------------------------------------------------------
# Schema / init tests
# ---------------------------------------------------------------------------
def test_init_db_creates_schema(mock_db_path):
    """init_db must create the file and the hotel_prices table."""
    init_db()

    assert os.path.exists(mock_db_path)

    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='hotel_prices'"
    )
    assert cursor.fetchone()[0] == "hotel_prices"
    conn.close()


def test_init_db_is_idempotent(mock_db_path):
    """Calling init_db twice must not raise."""
    init_db()
    init_db()

    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='hotel_prices'")
    assert cursor.fetchone()[0] == 1
    conn.close()


# ---------------------------------------------------------------------------
# Connection context manager tests
# ---------------------------------------------------------------------------
def test_get_db_connection_commits_on_success(mock_db_path):
    """Connection must auto-commit when the context block succeeds."""
    init_db()

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO hotel_prices (fetch_date, city, hotel_name, checkin_date, price) "
            "VALUES (?, ?, ?, ?, ?)",
            ("2024-01-01", "Taubate", "Test Hotel", "2024-01-10", 100),
        )

    # Verify data was committed
    verify_conn = sqlite3.connect(mock_db_path)
    cursor = verify_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hotel_prices")
    assert cursor.fetchone()[0] == 1
    verify_conn.close()


def test_get_db_connection_rolls_back_on_error(mock_db_path):
    """Connection must rollback when an exception occurs inside the context."""
    init_db()

    with pytest.raises(ValueError):
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO hotel_prices (fetch_date, city, hotel_name, checkin_date, price) "
                "VALUES (?, ?, ?, ?, ?)",
                ("2024-01-01", "Taubate", "Test Hotel", "2024-01-10", 100),
            )
            raise ValueError("Simulated error")

    # Verify data was NOT committed
    verify_conn = sqlite3.connect(mock_db_path)
    cursor = verify_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hotel_prices")
    assert cursor.fetchone()[0] == 0
    verify_conn.close()


# ---------------------------------------------------------------------------
# Insert / upsert tests
# ---------------------------------------------------------------------------
def test_insert_hotel_prices(mock_db_path):
    """Records are inserted correctly and metadata keys are filtered out."""
    init_db()

    fetch_date = "2024-05-01"
    city = "Taubate"
    checkin_date = "2024-05-10"
    prices = {
        "Check_in": checkin_date,  # metadata — must NOT be inserted
        "Timestamp": fetch_date,  # metadata — must NOT be inserted
        "Faro Hotel Taubaté": 250,
        "Ibis Taubate": None,
    }

    insert_hotel_prices(fetch_date, city, checkin_date, prices)

    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT hotel_name, price FROM hotel_prices")
    rows = cursor.fetchall()
    conn.close()

    # Only actual hotel rows — metadata keys excluded
    assert len(rows) == 2
    result = dict(rows)
    assert result["Faro Hotel Taubaté"] == 250
    assert result["Ibis Taubate"] is None


def test_upsert_updates_existing_price(mock_db_path):
    """Re-inserting the same key with a new price updates rather than duplicates."""
    init_db()

    fetch_date = "2024-05-01"
    city = "Taubate"
    checkin_date = "2024-05-10"

    insert_hotel_prices(fetch_date, city, checkin_date, {"Faro Hotel Taubaté": 250})
    insert_hotel_prices(fetch_date, city, checkin_date, {"Faro Hotel Taubaté": 300})

    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price FROM hotel_prices WHERE hotel_name='Faro Hotel Taubaté'"
    )
    rows = cursor.fetchall()
    conn.close()

    # Should be exactly one row with the updated price
    assert len(rows) == 1
    assert rows[0][0] == 300


def test_insert_empty_dict_is_noop(mock_db_path):
    """Calling insert_hotel_prices with an empty dict must not raise or insert."""
    init_db()
    insert_hotel_prices("2024-05-01", "Taubate", "2024-05-10", {})

    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hotel_prices")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0


def test_insert_only_metadata_keys_is_noop(mock_db_path):
    """A dict containing only Check_in/Timestamp keys must not insert any rows."""
    init_db()
    insert_hotel_prices(
        "2024-05-01",
        "Taubate",
        "2024-05-10",
        {"Check_in": "2024-05-10", "Timestamp": "2024-05-01"},
    )

    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hotel_prices")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0


def test_insert_multiple_hotels_single_call(mock_db_path):
    """Multiple hotels in a single call should all be inserted."""
    init_db()

    prices = {
        "Hotel A": 100,
        "Hotel B": 200,
        "Hotel C": 300,
    }
    insert_hotel_prices("2024-05-01", "Taubate", "2024-05-10", prices)

    conn = sqlite3.connect(mock_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hotel_prices")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 3
