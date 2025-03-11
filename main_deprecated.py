# DEPRECATED - Booking.com uses JS and it doesn't work using the following libraries
# import requests
# import pandas as pd
# from datetime import datetime, timedelta
# from lxml import html
# from unidecode import unidecode
# from fake_useragent import UserAgent
#
#
# def fetch_hotel_prices(city, checkin_date, checkout_date, hotel_competitors):
#     """
#     Scrapes hotel names and prices from Booking.com using requests and lxml.
#
#     :param city: Name of the city
#     :param checkin_date: Check-in date (YYYY-MM-DD)
#     :param checkout_date: Check-out date (YYYY-MM-DD)
#     :param hotel_competitors: List of hotel names to track
#     :return: Dictionary with hotel names as keys and prices as values
#     """
#
#     print(f"📌 Fetching prices for {city} - Check-in: {checkin_date} to {checkout_date}...")
#
#     # Construct the search URL for Booking.com
#     search_url = f"https://www.booking.com/searchresults.html?ss={city}&checkin={checkin_date}&checkout={checkout_date}&group_adults=2&no_rooms=1&group_children=0"
#
#     # Make request to Booking.com
#     session = requests.Session()
#     # Generate random user-agent
#     ua = UserAgent()
#
#     session.headers.update({
#         "User-Agent": ua.random,  # Random user-agent
#     })
#
#     response = session.get(search_url)
#
#
#     if response.status_code != 200:
#         print(f"❌ Error: Unable to fetch data for {city}. Status Code: {response.status_code}")
#         return {"Check-in": checkin_date, "Error": "Page not loaded"}
#
#     # Parse the page with lxml
#     tree = html.fromstring(response.content)
#
#     # Extract hotel data
#     hotel_prices = {"Check-in": checkin_date}  # Store date as the first column
#
#     try:
#         # Extract hotel names using XPath
#         hotel_names = tree.xpath('//div[@data-testid="title"]/text()')
#
#         # Extract prices using XPath
#         price_elements = tree.xpath('//span[@data-testid="price-and-discounted-price"]/text()')
#
#         # Process extracted data
#         for name, price in zip(hotel_names, price_elements):
#             hotel_name = name.strip().title()
#
#             # Check if the hotel is in the competitor list (case-insensitive match)
#             if not any(unidecode(h).lower() == unidecode(hotel_name).lower() for h in hotel_competitors):
#                 continue
#
#             # Extract numeric price
#             numeric_price = "".join(filter(str.isdigit, price))
#
#             # Store the price in the dictionary
#             hotel_prices[hotel_name] = numeric_price if numeric_price else "N/A"
#
#     except Exception as e:
#         print(f"❌ Error extracting hotel details: {e}")
#
#     return hotel_prices
#
#
# if __name__ == "__main__":
#     # Generate a list of 30 days from today
#     date_list = [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]
#
#     city = "Taubate"
#
#     # Define the hotel list (case-insensitive matching)
#     hotel_competitors = [
#         "San Michel Palace Hotel",
#         "Carlton Plaza Baobá",
#         "Olavo Bilac Hotel",
#         "Ibis Taubate",
#         "Ibis Styles Taubate",
#         "Hotel São Nicolau",
#         "Samambaia Executive Hotel",
#         # "Hotel Bike Taubate",
#         # "Prisma Plaza Hotel"
#     ]
#
#     # Collect data
#     results = []
#     for in_, out_ in zip(range(len(date_list) - 1), range(1, len(date_list))):
#         results.append(fetch_hotel_prices(city, date_list[in_], date_list[out_], hotel_competitors))
#
#     # Convert results to DataFrame
#     df = pd.DataFrame(results)
#
#     # Reorder columns so "Check-in" is the first column
#     df = df[["Check-in"] + [col for col in df.columns if col != "Check-in"]]
#
#     # Save results to CSV
#     filename = f"{date_list[in_]}_booking_hotel_prices_{city}.csv"
#     df.to_csv(filename, index=False)
#
#     print(f"✅ Data saved to {filename}")