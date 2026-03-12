# 🏨 Hotel Price Tracker — Taubaté, SP

Automated daily scraper that **captures hotel prices** from Booking.com for a list of competitor hotels in **Taubaté, São Paulo** and stores them locally (SQLite) or in a shared database (PostgreSQL).

## 📌 Features

✅ **Tracks multiple hotels** dynamically from a configurable list  
✅ **Automated data collection** using Selenium with Chrome/Chromium  
✅ **Configurable headless/visible mode** — visible locally for debugging, headless in Docker  
✅ **Structured SQL storage** with UPSERT support (re-running the scraper is always safe)  
✅ **SQLite by default** — zero setup, works out of the box  
✅ **PostgreSQL ready** — switch with one environment variable when you need a shared database  
✅ **Docker support** for easy deployment and containerized scheduling  
✅ **Robust testing** with `pytest`  

---

## 📁 Project Structure

```
hotels/
├── main.py                     # Orchestrator entry point
├── send_email.py               # Email notification (optional)
├── run_hotels.sh               # Shell script for cron scheduling
├── setup.cfg                   # Pytest & coverage configuration

├── requirements.txt            # All dependencies (runtime + testing)
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Container orchestration
├── src/
│   ├── config.py               # Centralized configuration
│   ├── database.py             # Database layer (SQLite or PostgreSQL)
│   ├── scraper/
│   │   └── booking_scraper.py  # Selenium scraper for Booking.com
│   └── utils/
│       └── logger.py           # Dual logger (console + file)
├── tests/
│   ├── unit/                   # Unit tests
│   └── e2e/                    # End-to-end orchestration tests
├── data/                       # SQLite database (auto-created, gitignored)
└── logs/                       # Application logs (auto-created, gitignored)
```

---

## ⚙️ Configuration

Configuration is resolved with the following **priority order**:
1. **Environment variables** (`.env` file or system env) — highest priority
2. **Hardcoded defaults** — fallback

### Environment Variables (`.env`)

Copy `.env.example` to `.env` and customize:

| Variable | Description | Default |
|---|---|---|
| `CHROME_BINARY` | Path to Chrome/Chromium binary | Auto-detected |
| `HEADLESS` | Run browser in headless mode | `True` in Docker, `False` locally |
| `CITY` | Target city for hotel search | `Taubate` |
| `DAYS_AHEAD` | Number of nights to scrape ahead | `31` |
| `HOTEL_COMPETITORS` | Comma-separated list of hotels | Uses `config.py` default list |
| `EMAIL_SEND_FROM` | Sender email address | *(empty)* |
| `EMAIL_SEND_FROM_PASSWORD` | Sender email password/app password | *(empty)* |
| `EMAIL_SEND_TO` | Recipient email address | *(empty)* |
| `DATABASE_URL` | PostgreSQL connection string | *(empty → SQLite)* |

---

## 🔧 Installation & Setup

### 1️⃣ Running locally (Python venv)

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Copy and edit your config
cp .env.example .env

# Run the scraper
python main.py
```

### 2️⃣ Running via Docker (full stack)

Ensure you have Docker and Docker Compose installed.

```bash
docker-compose build
docker-compose up
```

> The container runs the scraper once and exits. Schedule daily runs with your host machine's cron:
> ```bash
> 0 8 * * * cd /path/to/hotels && docker-compose up
> ```

### 3️⃣ Automated Scheduling (Cron)

Use the included `run_hotels.sh` script with `crontab`:

```bash
# Edit crontab
crontab -e

# Add a daily run at 8am
0 8 * * * /path/to/hotels/run_hotels.sh >> /path/to/hotels/cron.log 2>&1
```

---

## 🧪 Testing

```bash
# Run all tests with coverage
pytest --cov

# Run just unit tests
pytest tests/unit/

# Run just E2E tests
pytest tests/e2e/
```

---

## 📊 Viewing Results

The database is automatically created at `data/prices.db` (SQLite).
Open it with any SQLite viewer (e.g., [DB Browser for SQLite](https://sqlitebrowser.org), DBeaver):

```bash
sqlite3 data/prices.db "SELECT * FROM hotel_prices ORDER BY checkin_date LIMIT 10;"
```

---

## 🐘 Migrating to PostgreSQL (when ready)

When you're ready to use a **shared, live database** (e.g., Supabase, Neon, Railway, or your own server), migration is a single environment variable change — no code changes needed.

### Steps

**1. Install the PostgreSQL driver:**
```bash
# In requirements.txt, uncomment:
# psycopg2-binary>=2.9.9

pip install psycopg2-binary
```

**2. Set `DATABASE_URL` in your `.env`:**
```bash
# Local development (Postgres.app)
DATABASE_URL=postgresql://localhost/hotels_db

# Cloud database (Supabase, Neon, Railway, etc.)
DATABASE_URL=postgresql://user:password@host:5432/hotels_db
```

**3. Run the scraper — that's it.** The app detects `DATABASE_URL` automatically and switches to PostgreSQL.

### Recommended free cloud PostgreSQL options

| Provider | Free tier | Notes |
|:---|:---|:---|
| [Supabase](https://supabase.com) | ✅ Generous | Has a web UI dashboard |
| [Neon](https://neon.tech) | ✅ Generous | Serverless Postgres |
| [Railway](https://railway.app) | ✅ Small | Easy to set up |
