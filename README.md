# 🏨 Hotel Price Tracker - Taubaté, SP

This project **captures hotel prices** from a given list of hotels in **Taubaté, São Paulo** at a specific time of the day.

## 📌 Features
✅ **Tracks multiple hotels** in Taubaté, SP dynamically via `.env` files  
✅ **Automated data collection** using Headless Chromium and Selenium 4  
✅ **Structured SQL Storage** directly into an robust `sqlite3` database replacing multiple `.csv` dumps  
✅ **Automated Notifier** emailing the consolidated `data/prices.db` with your SMTP configs  
✅ **Docker Support** easy environment bootstrapping and containerization   
✅ **Robust testing** via `pytest`   

---

## 🔧 Installation & Setup

### **1️⃣ Configuration Setup**
1. Copy `.env` to `.env.local` or edit the existing `.env` file directly:
```bash
cp .env .env.local
```
2. Populate the `EMAIL_SEND_FROM`, `EMAIL_SEND_FROM_PASSWORD` and `EMAIL_SEND_TO` so notifications can be sent successfully.

### **2️⃣ Running via Docker (Recommended)**
Ensure you have Docker and Docker Compose installed.
```bash
docker-compose build
docker-compose up -d
```
*Note: This will execute the scraper, ingest to the SQLite DB, map logs to `/logs`, store data in `/data`, and automatically shut down the container upon completion. You can setup your Host machine cron to execute `docker-compose up` daily.*

### **3️⃣ Running via Python Virtual Environment**
If you prefer running it locally on your machine without Docker:
1. Create and activate a Virtual Environment
```shell
python3 -m venv .venv
source .venv/bin/activate
```
2. Install dependencies
```shell
pip install -r requirements.txt
```
3. Run the Orchestrator
```shell
python main.py
```

### **4️⃣ Testing**
We utilize `pytest` to execute unit and mocked E2E tests:
```shell
PYTHONPATH=. pytest tests/
```

### **5️⃣ Locate the Results**
- The database is dynamically created explicitly inside the **`data/` folder**.
- Open `data/prices.db` using any SQLite viewer (like DBeaver or standard CLI) to review ingested outputs efficiently without scrolling through thousands of ZIPs!
