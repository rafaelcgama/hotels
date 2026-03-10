import os
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
# Provide the absolute path to .env file at the root of the project
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- Configuration Variables ---

# Email Configurations
EMAIL_SEND_FROM = os.getenv("EMAIL_SEND_FROM", "")
EMAIL_SEND_FROM_PASSWORD = os.getenv("EMAIL_SEND_FROM_PASSWORD", "")
EMAIL_SEND_TO = os.getenv("EMAIL_SEND_TO", "")

# Search Configurations
CITY = os.getenv("CITY", "Taubate")
# Read hotel list from environment variable as JSON string, fallback to default list
HOTEL_COMPETITORS_JSON = os.getenv("HOTEL_COMPETITORS", "[]")
try:
    HOTEL_COMPETITORS = json.loads(HOTEL_COMPETITORS_JSON)
except json.JSONDecodeError:
    print("Warning: Failed to parse HOTEL_COMPETITORS from .env. Using empty list.")
    HOTEL_COMPETITORS = []

# Default if not provided in .env
if not HOTEL_COMPETITORS:
    HOTEL_COMPETITORS = [
        "Faro Hotel Taubaté",
        "Carlton Plaza Baobá",
        "Olavo Bilac Hotel",
        "Ibis Taubate",
        "Ibis Styles Taubate",
        "Gran Continental Hotel Taubaté",
        "KEEP SUÍTES HOTEL"
    ]

# Days ahead to search
DAYS_AHEAD = int(os.getenv("DAYS_AHEAD", "31"))

# Paths
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "prices.db")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "app.log")

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
