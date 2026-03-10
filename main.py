import time
import traceback
from datetime import datetime, timedelta

from src.config import CITY, HOTEL_COMPETITORS, DAYS_AHEAD
from src.utils.logger import get_logger
from src.pipeline.database import init_db, insert_hotel_prices
from src.scraper.booking_scraper import create_webdriver, collect_hotel_prices
from src.notifications.email_sender import send_notification_email

logger = get_logger(__name__)

def main():
    logger.info("Starting Hotel Price Tracker orchestrator...")
    start_time = time.time()

    # 1. Initialize DB Cache
    init_db()

    # Generate dates
    date_list = [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(DAYS_AHEAD)]
    
    driver = None
    try:
        # 2. Init Webdriver
        logger.info("Initializing Webdriver...")
        driver = create_webdriver()
        
        fetch_date = datetime.now().strftime("%Y-%m-%d")

        # 3. Scrape and Ingest
        for i in range(len(date_list) - 1):
            checkin = date_list[i]
            checkout = date_list[i + 1]
            try:
                # Scrape
                prices = collect_hotel_prices(
                    driver=driver,
                    city=CITY,
                    checkin_date=checkin,
                    checkout_date=checkout,
                    hotel_competitors=HOTEL_COMPETITORS,
                    retries=3
                )
                
                # Ingest into SQLite
                insert_hotel_prices(
                    fetch_date=fetch_date,
                    city=CITY,
                    checkin_date=checkin,
                    hotel_prices=prices
                )
                
            except Exception as e:
                logger.error(f"Failed processing dates {checkin} to {checkout}")
                logger.error(traceback.format_exc())
                
    except Exception as e:
        logger.critical(f"Critical error in orchestration: {e}")
        logger.critical(traceback.format_exc())
    finally:
        if driver:
            logger.info("Closing Webdriver...")
            driver.quit()

    # 4. Notify
    logger.info("Executing Notification phase...")
    send_notification_email()

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Orchestration completed in {elapsed}s.")

if __name__ == "__main__":
    main()
