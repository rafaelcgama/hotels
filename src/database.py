"""
Database abstraction layer.

Engine selection is automatic based on environment:
  - DATABASE_URL not set  →  SQLite  (local file, no server needed)
  - DATABASE_URL is set   →  PostgreSQL (requires psycopg2-binary installed)

To migrate from SQLite to PostgreSQL, set DATABASE_URL in your .env:
    DATABASE_URL=postgresql://user:password@host:5432/hotels_db

No other code needs to change.
"""

from contextlib import contextmanager
from typing import Dict, Union

from src.config import DATABASE_URL, DB_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Engine detection
# ---------------------------------------------------------------------------
_USE_POSTGRES = bool(DATABASE_URL)

if _USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        raise ImportError(
            "DATABASE_URL is set but 'psycopg2-binary' is not installed.\n"
            "Run:  pip install psycopg2-binary"
        )
else:
    import sqlite3


# ---------------------------------------------------------------------------
# Connection context manager
# ---------------------------------------------------------------------------
@contextmanager
def get_db_connection():
    """
    Yields a database connection for the configured engine.
    Always commits on success, rolls back on error, and closes when done.
    """
    if _USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect(DB_PATH)

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema — placeholder token differs between engines
# ---------------------------------------------------------------------------
def _placeholder() -> str:
    """Returns the SQL parameter placeholder for the active engine."""
    return "%s" if _USE_POSTGRES else "?"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def init_db() -> None:
    """
    Creates the hotel_prices table if it does not already exist.
    Safe to call on every startup (idempotent).

    Schema (long/tall format — one row per hotel per date):
        id           SERIAL / INTEGER  primary key
        fetch_date   TEXT              date the scraper ran (YYYY-MM-DD)
        city         TEXT              destination city searched
        hotel_name   TEXT              exact name from the competitors list
        checkin_date TEXT              check-in date (YYYY-MM-DD)
        price        INTEGER           lowest price found (NULL = not listed)
        inserted_at  TIMESTAMP         auto-set on insert, updated on upsert
    """
    if _USE_POSTGRES:
        ddl = """
            CREATE TABLE IF NOT EXISTS hotel_prices (
                id           SERIAL PRIMARY KEY,
                fetch_date   TEXT NOT NULL,
                city         TEXT NOT NULL,
                hotel_name   TEXT NOT NULL,
                checkin_date TEXT NOT NULL,
                price        INTEGER,
                inserted_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (fetch_date, city, hotel_name, checkin_date)
            )
        """
    else:
        ddl = """
            CREATE TABLE IF NOT EXISTS hotel_prices (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                fetch_date   TEXT NOT NULL,
                city         TEXT NOT NULL,
                hotel_name   TEXT NOT NULL,
                checkin_date TEXT NOT NULL,
                price        INTEGER,
                inserted_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (fetch_date, city, hotel_name, checkin_date)
            )
        """

    with get_db_connection() as conn:
        conn.execute(ddl)

    engine = "PostgreSQL" if _USE_POSTGRES else f"SQLite ({DB_PATH})"
    logger.info(f"Database initialized/verified — engine: {engine}")


def insert_hotel_prices(
        fetch_date: str,
        city: str,
        checkin_date: str,
        hotel_prices: Dict[str, Union[int, None]],
) -> None:
    """
    Inserts or updates scraped hotel prices into the database.

    The UPSERT logic ensures re-running the scraper for the same day is safe:
    it updates the price rather than inserting a duplicate row.

    Args:
        fetch_date:   Date the scraping ran (YYYY-MM-DD).
        city:         City that was searched.
        checkin_date: Check-in date for the hotel stay (YYYY-MM-DD).
        hotel_prices: Mapping of hotel_name → price (None if not found).
    """
    if not hotel_prices:
        return

    # Strip out internal metadata keys — only actual hotel names go to the DB
    records = [
        (fetch_date, city, hotel_name, checkin_date, price)
        for hotel_name, price in hotel_prices.items()
        if hotel_name not in ("Check_in", "Timestamp")
    ]

    if not records:
        return

    p = _placeholder()

    if _USE_POSTGRES:
        sql = f"""
            INSERT INTO hotel_prices (fetch_date, city, hotel_name, checkin_date, price)
            VALUES ({p}, {p}, {p}, {p}, {p})
            ON CONFLICT (fetch_date, city, hotel_name, checkin_date)
            DO UPDATE SET price = EXCLUDED.price,
                          inserted_at = CURRENT_TIMESTAMP
        """
    else:
        sql = f"""
            INSERT INTO hotel_prices (fetch_date, city, hotel_name, checkin_date, price)
            VALUES ({p}, {p}, {p}, {p}, {p})
            ON CONFLICT (fetch_date, city, hotel_name, checkin_date)
            DO UPDATE SET price = excluded.price,
                          inserted_at = CURRENT_TIMESTAMP
        """

    try:
        with get_db_connection() as conn:
            conn.executemany(sql, records)
        logger.info(f"Upserted {len(records)} records for check-in {checkin_date}")
    except Exception as e:
        logger.error(f"Error inserting records for {checkin_date}: {e}")
        raise
