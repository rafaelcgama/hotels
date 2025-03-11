import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from unidecode import unidecode
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import time, sleep
import os


def wait_for_page_load(driver, timeout=10):
    """
    Ensures that the Booking.com page is fully loaded by waiting for hotel listings to appear.

    :param driver: Selenium WebDriver instance
    :param timeout: Maximum wait time in seconds
    """
    try:
        # sleep(2)
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
    # sleep(5)

    # Dictionary to store prices
    hotel_prices = {"Check-in": checkin_date}  # First column is the date

    try:
        # Find all hotel elements
        hotel_elements = driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')

        for hotel in hotel_elements:
            try:
                # Extract hotel name
                name_element = hotel.find_element(By.XPATH, './/div[@data-testid="title"]')
                hotel_name = unidecode(name_element.text.strip().lower())

                # # Normalize hotel name for case-insensitive comparison
                # normalized_name = hotel_name.lower()
                #
                # # Check if the hotel is in the competitor list (case-insensitive match)
                # if not any(h.lower() == normalized_name for h in hotel_competitors):
                #     continue
                if hotel_name not in hotel_competitors:
                    continue

                # Extract hotel price
                price_elements = hotel.find_elements(By.XPATH, './/span[@data-testid="price-and-discounted-price"]')
                prices = [
                    int("".join(filter(str.isdigit, price.text)))  # Extract only digits from price
                    for price in price_elements if price.text
                ]

                # Store the minimum price found (if available)
                hotel_prices[hotel_name.title()] = min(prices) if prices else None

            except Exception as e:
                print(f"Error fetching details for {hotel_name}: {str(e)}")

    except Exception as e:
        print(f"Error fetching hotels: {str(e)}")

    return hotel_prices  # Return data as a dictionary


if __name__ == "__main__":

    t1 = time()

    # Start WebDriver (single instance for efficiency)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Newer headless mode
    options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    options.add_argument("--disable-gpu")  # Enable rendering
    options.add_argument("--enable-webgl")
    options.add_argument("--use-gl=desktop")
    options.add_argument("--start-maximized")  # Maximize window
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    # Generate a list of 30 days from today
    date_list = [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(31)]

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

    hotel_competitors = [unidecode(hotel).lower() for hotel in hotel_competitors]

    # Collect data
    results = []
    for in_, out_ in zip(range(len(date_list) - 1), range(1, len(date_list))):
        results.append(collecting_hotel_prices(driver, city, date_list[in_], date_list[out_], hotel_competitors))

    # Close WebDriver after collecting data
    driver.quit()

    # Convert results to DataFrame
    df = pd.DataFrame(results)

    # Reorder columns so "Check-in" is the first column
    df = df[["Check-in"] + [col for col in df.columns if col != "Check-in"]]

    # Save results to CSV
    # Create the "data" folder if it doesn't exist
    os.makedirs("data", exist_ok=True)

    filename = f"data/{date_list[in_]}_booking_hotel_prices_{city.lower()}.csv"
    df.to_csv(filename, index=False)

    print("")
    print(f"Data saved to {filename}")
    print("")
    print(f"Time taken: {time() - t1}s")
