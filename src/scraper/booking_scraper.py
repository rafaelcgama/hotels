import random
import time
import os
from typing import List, Dict, Union
from datetime import datetime
from unidecode import unidecode
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from src.config import HEADLESS
from src.utils.logger import get_logger

logger = get_logger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


def normalize_string(s: str) -> str:
    """Strips accents, lowercases, and trims whitespace for fuzzy matching."""
    return unidecode(s.strip().lower())


def create_webdriver() -> WebDriver:
    """Creates and returns a Selenium Chrome WebDriver with anti-detection options."""
    options = Options()

    chrome_binary = os.environ.get("CHROME_BINARY")
    if chrome_binary and os.path.exists(chrome_binary):
        options.binary_location = chrome_binary

    if HEADLESS:
        logger.info("Running in HEADLESS mode.")
        options.add_argument("--headless=new")
    else:
        logger.info("Running in visible (HEADFUL) mode.")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={random.choice(_USER_AGENTS)}")

    driver = WebDriver(options=options)
    driver.maximize_window()
    return driver


def wait_for_page_load(driver: WebDriver, timeout: int = 15) -> bool:
    """
    Waits for hotel property cards to appear on the Booking.com results page.

    Returns:
        True if the page loaded successfully, False on timeout or error.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@data-testid="property-card"]')
            )
        )
        return True
    except TimeoutException:
        logger.warning(f"Page load timeout — no property cards after {timeout}s.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error waiting for page load: {e}")
        return False


def collect_hotel_prices(
    driver: WebDriver,
    city: str,
    checkin_date: str,
    checkout_date: str,
    hotel_competitors: List[str],
    retries: int = 2,
) -> Dict[str, Union[int, None]]:
    """
    Scrapes prices for a list of target hotels from Booking.com.

    Stores hotel names exactly as provided in hotel_competitors (no .title() mangling).
    Returns a dict mapping hotel_name → lowest price found (or None if not found).

    Args:
        driver:            An active Selenium WebDriver instance.
        city:              The destination city to search.
        checkin_date:      Check-in date string (YYYY-MM-DD).
        checkout_date:     Check-out date string (YYYY-MM-DD).
        hotel_competitors: List of hotel names to track.
        retries:           Number of retry attempts on failure.

    Returns:
        Dict with metadata keys ("Check_in", "Timestamp") plus hotel_name → price entries.
    """
    normalized_competitors = {normalize_string(h): h for h in hotel_competitors}

    search_url = (
        f"https://www.booking.com/searchresults.html?"
        f"ss={city}&checkin={checkin_date}&checkout={checkout_date}"
        f"&group_adults=2&no_rooms=1&group_children=0"
    )

    # Initialise result dict — hotels default to None (not found)
    hotel_prices: Dict[str, Union[int, None]] = {
        "Check_in": checkin_date,
        "Timestamp": datetime.now().strftime("%Y-%m-%d"),
        **{name: None for name in hotel_competitors},
    }

    for attempt in range(retries + 1):
        try:
            logger.info(
                f"Scraping '{city}' — check-in: {checkin_date} "
                f"(attempt {attempt + 1}/{retries + 1})"
            )
            driver.get(search_url)

            if not wait_for_page_load(driver):
                if attempt < retries:
                    logger.warning("Page did not load — retrying...")
                    time.sleep(2)
                    continue
                logger.error(
                    f"Failed to load results for {checkin_date} "
                    f"after {retries + 1} attempts."
                )
                return hotel_prices

            # Scroll to bottom to get all cards into the DOM (triggers lazy loading)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            previous_count = 0
            stable_checks = 0
            for _ in range(20):  # max ~10s wait
                time.sleep(0.5)
                current_count = len(
                    driver.find_elements(
                        By.XPATH, '//div[@data-testid="property-card"]'
                    )
                )
                if current_count == previous_count:
                    stable_checks += 1
                    if stable_checks >= 2:
                        break
                else:
                    stable_checks = 0
                previous_count = current_count

            hotel_elements = driver.find_elements(
                By.XPATH, '//div[@data-testid="property-card"]'
            )
            logger.info(f"Total property cards found on page: {len(hotel_elements)}")
            found_count = 0

            for hotel_el in hotel_elements:
                try:
                    # Scroll card into view — Booking.com renders text only when visible
                    driver.execute_script(
                        "arguments[0].scrollIntoView(true);", hotel_el
                    )
                    time.sleep(0.1)

                    name_el = hotel_el.find_element(
                        By.XPATH, './/div[@data-testid="title"]'
                    )
                    raw_name = name_el.text.strip()
                    if not raw_name:
                        continue  # Card text still not rendered — skip
                    normalized_name = normalize_string(raw_name)

                    original_name = normalized_competitors.get(normalized_name)
                    if original_name is None:
                        logger.debug(
                            f"  No match: '{raw_name}' (normalized: '{normalized_name}')"
                        )
                        continue  # Not a target competitor

                    logger.info(f"  Matched: '{raw_name}' → '{original_name}'")

                    price_els = hotel_el.find_elements(
                        By.XPATH, './/span[@data-testid="price-and-discounted-price"]'
                    )
                    prices = []
                    for price_el in price_els:
                        raw = normalize_string(price_el.text)
                        digits = "".join(filter(str.isdigit, raw))
                        if digits:
                            prices.append(int(digits))

                    if prices:
                        hotel_prices[original_name] = min(prices)
                        found_count += 1

                except Exception as e:
                    logger.debug(f"Skipping a property card due to error: {e}")

            logger.info(
                f"Found {found_count} target prices for check-in {checkin_date}."
            )
            break  # Success — exit retry loop

        except WebDriverException as e:
            logger.error(f"WebDriver error on attempt {attempt + 1}: {e}")
            if attempt == retries:
                return hotel_prices
            time.sleep(2)

    return hotel_prices
