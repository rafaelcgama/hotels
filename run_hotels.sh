#!/bin/bash

# Set up paths
PROJECT_DIR="/Users/rafaelcgama/Projects/hotels" # Change to the path where the hotels project is stored
ARCHIVE_FILE="$PROJECT_DIR/data/rates.zip"  # This will store the compressed file

# Activate your virtual environment
source "$PROJECT_DIR/.venv/bin/activate"
python collect_rates.py

# Combine the current output with previous results and create a compressed archive
cd "$PROJECT_DIR/data"

# Append the new output to the previous one and create the zip archive
zip -r "$ARCHIVE_FILE" *.csv  # Compress all CSVs into a zip archive

#python send_email.py

# Deactivate the virtual environment (optional)
deactivate