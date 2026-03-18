import os
from pathlib import Path
from dotenv import load_dotenv

# Absolute path to the project root (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if present (values already in the environment take priority)
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Search settings
# ---------------------------------------------------------------------------
CITY: str = os.environ.get("CITY", "Taubate")

_hotel_competitors_env = os.environ.get("HOTEL_COMPETITORS", "")
HOTEL_COMPETITORS: list = (
    [h.strip() for h in _hotel_competitors_env.split(",") if h.strip()]
    if _hotel_competitors_env
    else [
        "Faro Hotel Taubaté",
        "Carlton Plaza Baobá",
        "Olavo Bilac Hotel",
        "Ibis Taubate",
        "Ibis Styles Taubate",
        "Gran Continental Hotel Taubaté",
        "KEEP SUÍTES HOTEL",
    ]
)

DAYS_AHEAD: int = int(os.environ.get("DAYS_AHEAD", 31))

# ---------------------------------------------------------------------------
# Email settings (optional, not yet implemented)
# ---------------------------------------------------------------------------
EMAIL_SEND_FROM: str = os.environ.get("EMAIL_SEND_FROM", "")
EMAIL_SEND_FROM_PASSWORD: str = os.environ.get("EMAIL_SEND_FROM_PASSWORD", "")
EMAIL_SEND_TO: str = os.environ.get("EMAIL_SEND_TO", "")

# ---------------------------------------------------------------------------
# Scraper settings
# ---------------------------------------------------------------------------
# Headless mode: auto-detected (True inside Docker, False locally).
# Can be overridden in .env with HEADLESS=true/false.
IS_DOCKER: bool = os.path.exists("/.dockerenv")
_headless_env = os.environ.get("HEADLESS")
HEADLESS: bool = (
    _headless_env.lower() in ("true", "1", "yes")
    if _headless_env is not None
    else IS_DOCKER
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR: str = str(BASE_DIR / "data")
LOGS_DIR: str = str(BASE_DIR / "logs")
LOG_FILE: str = str(BASE_DIR / "logs" / "app.log")

# Ensure required directories exist on startup
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Leave DATABASE_URL blank (or unset) to use SQLite locally.
# Set it to a PostgreSQL URL to use a shared/live database.
#
# SQLite  (default): DATABASE_URL=  ← blank or not set
# PostgreSQL:        DATABASE_URL=postgresql://user:pass@host:5432/hotels_db
DATABASE_URL: str = os.environ.get("DATABASE_URL", "").strip()

# SQLite file path — only used when DATABASE_URL is not set
DB_PATH: str = str(BASE_DIR / "data" / "prices.db")
