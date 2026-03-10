import random
import time
from typing import List, Dict, Union
from datetime import datetime
from unidecode import unidecode
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from src.utils.logger import get_logger

logger = get_logger(__name__)

def normalize_string(s: str) -> str:
    return unidecode(s.strip().lower())

def create_webdriver() -> WebDriver:
    """Creates and returns a Selenium WebDriver Chrome instance with predefined options."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"
    ]
    chosen_user_agent = random.choice(user_agents)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--enable-webgl")
    options.add_argument("--use-gl=desktop")
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={chosen_user_agent}")

    driver = WebDriver(options=options)
    driver.maximize_window()
    return driver

def wait_for_page_load(driver: WebDriver, timeout: int = 15) -> bool:
    """
    Ensures that the Booking.com page is fully loaded by waiting for hotel listings to appear.
    Returns True if loaded, False on timeout.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-testid="property-card"]'))
        )
        return True
    except TimeoutException:
        logger.warning(f"Page load timeout or elements not found after {timeout} seconds.")
        return False
    except Exception as e:
        logger.error(f"Error waiting for page load: {e}")
        return False

def collect_hotel_prices(driver: WebDriver,
                         city: str,
                         checkin_date: str,
                         checkout_date: str,
                         hotel_competitors: List[str],
                         retries: int = 2
                         ) -> Dict[str, Union[int, None]]:
    """
    Scrapes the prices of a list of hotels from Booking.com for a given city in a given date.
    Implements retry logic for robustness.
    """
    
    hotel_competitors_normalized = [normalize_string(h) for h in hotel_competitors]
    
    search_url = (f"https://www.booking.com/searchresults.html?"
                  f"ss={city}&checkin={checkin_date}&checkout={checkout_date}"
                  f"&group_adults=2&no_rooms=1&group_children=0")
                  
    # Base dictionary to return
    hotel_prices = {
        "Check_in": checkin_date,
        "Timestamp": datetime.now().strftime("%Y-%m-%d")
    }
    
    for h in hotel_competitors:
        hotel_prices[h.title()] = None
        
    for attempt in range(retries + 1):
        try:
            logger.info(f"Scraping '{city}' - Check-in: {checkin_date} (Attempt {attempt + 1}/{retries + 1})")
            driver.get(search_url)
            
            if not wait_for_page_load(driver):
                if attempt < retries:
                    logger.warning("Retrying...")
                    time.sleep(2)
                    continue
                else:
                    logger.error(f"Failed to load properties for {checkin_date} after {retries + 1} attempts.")
                    return hotel_prices
                    
            hotel_elements = driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')
            found_count = 0
            
            for hotel in hotel_elements:
                try:
                    name_element = hotel.find_element(By.XPATH, './/div[@data-testid="title"]')
                    hotel_name = normalize_string(name_element.text)

                    # Only process targeted competitors
                    if hotel_name not in hotel_competitors_normalized:
                        continue

                    # Extract hotel price
                    price_elements = hotel.find_elements(By.XPATH, './/span[@data-testid="price-and-discounted-price"]')

                    prices = []
                    for price in price_elements:
                        if price.text:
                            # Extract only digits from price string
                            digits = "".join(filter(str.isdigit, normalize_string(price.text)))
                            if digits:
                                prices.append(int(digits))

                    if prices:
                        min_price = min(prices)
                        # Find the original case name matching the normalized to save properly
                        original_name = next(h for h in hotel_competitors if normalize_string(h) == hotel_name)
                        hotel_prices[original_name.title()] = min_price
                        found_count += 1
                        
                except Exception as e:
                    logger.debug(f"Error fetching details for a property: {str(e)}")

            logger.info(f"Successfully scraped {found_count} target prices for {checkin_date}.")
            break # Break retry loop if successful

        except WebDriverException as e:
            logger.error(f"WebDriver exception on attempt {attempt + 1}: {e}")
            if attempt == retries:
                return hotel_prices
            time.sleep(2)
            
    return hotel_prices
