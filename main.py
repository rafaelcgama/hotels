import time
import traceback
from datetime import datetime, timedelta

from src.config import CITY, HOTEL_COMPETITORS, DAYS_AHEAD
from src.utils.logger import get_logger
from src.database import init_db, insert_hotel_prices
from src.scraper.booking_scraper import create_webdriver, collect_hotel_prices

logger = get_logger(__name__)


def main() -> None:
    """
    Orchestrates the hotel price tracking pipeline:
      1. Initialises the database.
      2. Generates the list of check-in / check-out date pairs to scrape.
      3. Launches a single Selenium WebDriver session.
      4. For each date pair: scrapes prices → inserts into DB.
      5. Always closes the WebDriver, even on failure.
    """
    logger.info("Starting Hotel Price Tracker orchestrator...")
    start_time = time.time()
    driver = None

    try:
        # 1. Initialise DB schema (idempotent — safe to run every time)
        init_db()

        # 2. Build consecutive (checkin, checkout) date pairs starting from today.
        #    DAYS_AHEAD=31 → 31 nightly pairs (today→tomorrow, tomorrow→day after, etc.)
        today = datetime.today()
        dates = [
            (today + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(DAYS_AHEAD + 1)
        ]
        date_pairs = list(zip(dates, dates[1:]))

        fetch_date = today.strftime("%Y-%m-%d")

        # 3. Launch WebDriver once for the entire run
        logger.info("Initializing WebDriver...")
        driver = create_webdriver()

        # 4. Scrape and ingest each date pair
        for checkin, checkout in date_pairs:
            try:
                prices = collect_hotel_prices(
                    driver=driver,
                    city=CITY,
                    checkin_date=checkin,
                    checkout_date=checkout,
                    hotel_competitors=HOTEL_COMPETITORS,
                    retries=3,
                )
                insert_hotel_prices(
                    fetch_date=fetch_date,
                    city=CITY,
                    checkin_date=checkin,
                    hotel_prices=prices,
                )
            except Exception:
                logger.error(f"Failed processing dates {checkin} → {checkout}")
                logger.error(traceback.format_exc())
                # Continue to next date pair rather than aborting the whole run

    except Exception:
        logger.critical("Critical error in orchestration — aborting.")
        logger.critical(traceback.format_exc())

    finally:
        if driver:
            logger.info("Closing WebDriver...")
            driver.quit()

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Orchestration completed in {elapsed}s.")


if __name__ == "__main__":
    main()
