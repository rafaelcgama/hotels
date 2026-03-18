FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files
# and to ensure stdout/stderr are unbuffered for Docker logs.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set Chrome binary path for the scraper
ENV CHROME_BINARY=/usr/bin/chromium

# Install Chromium and its webdriver
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY src/ src/

# Create directories for mounted volumes
RUN mkdir -p logs data

# Default command to execute the scraper orchestrator
CMD ["python", "main.py"]
