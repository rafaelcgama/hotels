import sqlite3
from typing import Dict, Union, List
from src.config import DB_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)

def init_db():
    """
    Initializes the SQLite database schema if it doesn't exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # We will use a flexible EAV (Entity-Attribute-Value) style or standard denormalized table
    # Since hotels list can change from .env, a long format table is best.
    # Columns: id, fetch_date, city, hotel_name, checkin_date, price, inserted_at
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hotel_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetch_date TEXT NOT NULL,
            city TEXT NOT NULL,
            hotel_name TEXT NOT NULL,
            checkin_date TEXT NOT NULL,
            price INTEGER,
            inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(fetch_date, city, hotel_name, checkin_date)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized/verified at {DB_PATH}")

def insert_hotel_prices(fetch_date: str, city: str, checkin_date: str, hotel_prices: Dict[str, Union[int, None]]):
    """
    Inserts or updates the scraped hotel prices into the database.
    
    :param fetch_date: The date when the scraping ran (YYYY-MM-DD)
    :param city: The city that was searched
    :param checkin_date: The checkin date for the hotel stay
    :param hotel_prices: Dictionary Mapping hotel_name to price
    """
    if not hotel_prices:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Iterate over the scraped results (excluding internal keys like Check_in/Timestamp which we handle differently)
    records_to_insert = []
    
    for hotel_name, price in hotel_prices.items():
        if hotel_name in ("Check_in", "Timestamp"):
            continue
            
        records_to_insert.append((fetch_date, city, hotel_name, checkin_date, price))
        
    try:
        cursor.executemany('''
            INSERT INTO hotel_prices (fetch_date, city, hotel_name, checkin_date, price)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(fetch_date, city, hotel_name, checkin_date) 
            DO UPDATE SET price=excluded.price, inserted_at=CURRENT_TIMESTAMP
        ''', records_to_insert)
        
        conn.commit()
        logger.info(f"Inserted {len(records_to_insert)} records for check-in {checkin_date}")
    except Exception as e:
        logger.error(f"Error inserting records for {checkin_date}: {e}")
    finally:
        conn.close()
