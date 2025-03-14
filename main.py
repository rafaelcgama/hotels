import os
import random
import pandas as pd
from time import time
from selenium import webdriver
from unidecode import unidecode
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def normalize_string(s):
    return unidecode(s.strip().lower())


def create_webdriver():
    """Creates and returns a Selenium WebDriver instance with predefined options."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    chosen_user_agent = random.choice(user_agents)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--enable-webgl")
    options.add_argument("--use-gl=desktop")
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={chosen_user_agent}")

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver


def wait_for_page_load(driver, timeout=10):
    """
    Ensures that the Booking.com page is fully loaded by waiting for hotel listings to appear.

    :param driver: Selenium WebDriver instance
    :param timeout: Maximum wait time in seconds
    """
    try:
        # Wait for hotel elements (key indicator of page load)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-testid="property-card"]'))
        )
        print("✅ Page loaded successfully.")

    except Exception as e:
        print(f"❌ Page load timeout: {e}")


def collecting_hotel_prices(driver, city, checkin_date, checkout_date, hotel_competitors):
    """
    Scrapes hotel names and prices from Booking.com for a given city and date range.

    :param driver: Selenium WebDriver instance
    :param city: Name of the city
    :param checkin_date: Check-in date (YYYY-MM-DD)
    :param checkout_date: Check-out date (YYYY-MM-DD)
    :param hotel_competitors: List of hotel names to track
    :return: Dictionary with hotel names as keys and prices as values
    """

    print(f"Scraping data for {city} - Check-in: {checkin_date} to {checkout_date}")

    # Construct Booking.com search URL
    search_url = f"https://www.booking.com/searchresults.html?ss={city}&checkin={checkin_date}&checkout={checkout_date}&group_adults=2&no_rooms=1&group_children=0"
    driver.get(search_url)

    # Wait for full page load
    wait_for_page_load(driver)

    # Dictionary to store prices
    hotel_prices = {"Check_in": checkin_date}  # First column is the date

    try:
        # Find all hotel elements
        hotel_elements = driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')

        for hotel in hotel_elements:
            try:
                # Extract hotel name
                name_element = hotel.find_element(By.XPATH, './/div[@data-testid="title"]')
                hotel_name = normalize_string(name_element.text)

                # Case-insensitive comparison
                if not any(normalize_string(h) == hotel_name for h in hotel_competitors):
                    continue

                # Extract hotel price
                price_elements = hotel.find_elements(By.XPATH, './/span[@data-testid="price-and-discounted-price"]')

                # TODO: check the logic to include numbers with decimals - check for brazil style decimals
                prices = [
                    int("".join(filter(str.isdigit, normalize_string(price.text))))  # Extract only digits from price
                    for price in price_elements if price.text
                ]

                # Store the minimum price found (if available)
                hotel_prices[hotel_name.title()] = min(prices) if prices else None
                hotel_prices["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            except Exception as e:
                print(f"Error fetching details for {hotel_name}: {str(e)}")

    except Exception as e:
        print(f"Error fetching hotels: {str(e)}")

    return hotel_prices  # Return data as a dictionary


if __name__ == "__main__":

    t1 = time()

    driver = create_webdriver()  # Start WebDriver

    # Generate a list of 30 days from today
    date_list = [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]

    city = "Taubate"

    # Define the hotel list (case-insensitive matching)
    hotel_competitors = [
        "San Michel Palace Hotel",
        "Carlton Plaza Baobá",
        "Olavo Bilac Hotel",
        "Ibis Taubate",
        "Ibis Styles Taubate",
        "Hotel São Nicolau",
        "Samambaia Executive Hotel",
        # "Hotel Bike Taubate",
        # "Prisma Plaza Hotel"
    ]

    hotel_competitors = [normalize_string(hotel) for hotel in hotel_competitors]

    # Collect data
    results = []
    for in_, out_ in zip(range(len(date_list) - 1), range(1, len(date_list))):
        results.append(collecting_hotel_prices(driver, city, date_list[in_], date_list[out_], hotel_competitors))

    # Close WebDriver after collecting data
    driver.quit()

    # Convert results to DataFrame
    df = pd.DataFrame(results)

    # Select columns to convert (excluding check_in and timestamp)
    cols_to_convert = df.columns.difference(['Check_in', 'Timestamp'])

    # Convert to nullable Int64 type (which allows NaN)
    df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric, errors='coerce').astype('Int64')

    # Ensure correct column order
    ordered_columns = ['Check_in', 'Timestamp'] + sorted(cols_to_convert)
    df = df[ordered_columns]

    # Save results to CSV
    # Create the "data" folder if it doesn't exist
    os.makedirs("data", exist_ok=True)

    filename = f"data/{date_list[0]}_booking_hotel_prices_{city.lower()}.csv"
    df.to_csv(filename, index=False)

    print("")
    print(f"Data saved to {filename}")
    print("")
    print(f"\n⏱ Time taken: {round(time() - t1, 2)}s")
