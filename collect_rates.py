import os
import random
import pandas as pd
from time import time
from unidecode import unidecode
from typing import List, Dict, Union
from datetime import datetime, timedelta, timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import knime.scripting.io as knio
import sys
from collections import defaultdict

# ─────────────────────────────────────────────────────────────
# Utility to print safely (removes non-ASCII chars like ❌)
# ─────────────────────────────────────────────────────────────
def safe_print(text: str):
    text = ''.join(c for c in text if ord(c) < 128)
    print(text)

# ─────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────
def normalize_string(s: str) -> str:
    return unidecode(s.strip().lower())

def create_webdriver() -> WebDriver:
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    chosen_user_agent = random.choice(user_agents)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(f"user-agent={chosen_user_agent}")

    driver_path = r"C:\Drivers\chrome-win64\chromedriver.exe"
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def wait_for_page_load(driver: WebDriver, timeout: int = 10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-testid="property-card"]'))
        )
        safe_print("Page loaded successfully.")
    except Exception as e:
        safe_print(f"Page load timeout: {e}")

# ─────────────────────────────────────────────────────────────
# Scraping Function
# ─────────────────────────────────────────────────────────────
def collect_hotel_prices(driver: WebDriver, city: str, checkin_date: str, checkout_date: str, hotel_competitors: List[str], script_start: datetime) -> Dict[str, Union[int, float]]:
    safe_print(f"Scraping data for {city} - Check-in: {checkin_date} to {checkout_date}")
    
    search_url = (
        f"https://www.booking.com/searchresults.html?"
        f"ss={city}&checkin={checkin_date}&checkout={checkout_date}"
        f"&group_adults=2&no_rooms=1&group_children=0"
    )
    driver.get(search_url)
    wait_for_page_load(driver)

    hotel_prices = {
        "Check_in": checkin_date,
        "Timestamp": script_start.strftime("%Y-%m-%d"),
        "Timestamp_DB": script_start.isoformat()
    }

    found_hotels = set()

    try:
        hotel_elements = driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')
        for hotel in hotel_elements:
            try:
                name_element = hotel.find_element(By.XPATH, './/div[@data-testid="title"]')
                hotel_name = normalize_string(name_element.text)

                if hotel_name in hotel_competitors:
                    found_hotels.add(hotel_name)

                    price_elements = hotel.find_elements(By.XPATH, './/span[@data-testid="price-and-discounted-price"]')
                    prices = [
                        int("".join(filter(str.isdigit, normalize_string(price.text))))
                        for price in price_elements if price.text
                    ]

                    hotel_prices[hotel_name.title()] = min(prices) if prices else None

            except Exception as e:
                safe_print(f"Error fetching hotel details: {str(e)}")
    except Exception as e:
        safe_print(f"Error fetching hotels: {str(e)}")

    # Mostrar quais hotéis esperados não foram encontrados
    not_found = [h for h in hotel_competitors if h not in found_hotels]
    if not_found:
        safe_print(f"Hotels not found in {city} ({checkin_date}): {[h.title() for h in not_found]}")

    return hotel_prices

# ─────────────────────────────────────────────────────────────
# Save and Output Function (Wide Format)
# ─────────────────────────────────────────────────────────────
def save_hotel_price_date(results: List[Dict[str, Union[int, float]]]) -> None:
    df = pd.DataFrame(results)

    if "City" in df.columns:
        df.drop(columns=["City"], inplace=True)

    cols_to_convert = df.columns.difference(['Check_in', 'Timestamp', 'Timestamp_DB'])
    df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric, errors='coerce')
    df = df[['Check_in', 'Timestamp', 'Timestamp_DB'] + sorted(cols_to_convert)]

    os.makedirs("data", exist_ok=True)
    filename = f"data/{df['Check_in'].iloc[0]}_booking_all_cities.csv"
    df.to_csv(filename, index=False, encoding='utf-8')
    safe_print(f"Data saved to {filename}")

    knio.output_tables[0] = knio.Table.from_pandas(df)

# ─────────────────────────────────────────────────────────────
# Main Execution
# ─────────────────────────────────────────────────────────────
t1 = time()
script_start = datetime.now(timezone(timedelta(hours=-3)))

# Define cidades e hotéis
city_hotels = {
    "Taubate": ["Ibis Taubate", "Ibis Styles Taubate"],
    "São José dos Campos": ["Ibis Sao Jose dos Campos Dutra", "Ibis Sao Jose dos Campos Colinas"],
    "Jacareí": ["Ibis Jacareí"],
    "Pindamonhangaba": ["Ibis Budget Pindamonhangaba"],
    "Guaratinguetá": ["Ibis Guaratingueta Aparecida - Circuito da Fé"],
    "Lorena": ["Ibis Budget Lorena - Circuito da Fé", "Ibis Lorena - Circuito da Fé"]
}

# Define período
date_list = [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]

driver = create_webdriver()
merged_results = defaultdict(dict)

for city, hotels in city_hotels.items():
    hotel_competitors_normalized = [normalize_string(h) for h in hotels]
    for i in range(len(date_list) - 1):
        checkin = date_list[i]
        checkout = date_list[i + 1]
        result = collect_hotel_prices(driver, city, checkin, checkout, hotel_competitors_normalized, script_start)
        key = result["Check_in"]
        merged_results[key].update(result)
        merged_results[key]["Check_in"] = result["Check_in"]
        merged_results[key]["Timestamp"] = result["Timestamp"]
        merged_results[key]["Timestamp_DB"] = result["Timestamp_DB"]

driver.quit()

all_results = list(merged_results.values())
save_hotel_price_date(all_results)
safe_print(f"\nTime taken: {round(time() - t1, 2)}s")
