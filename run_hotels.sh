#!/bin/bash

# Set up paths
PROJECT_DIR="/Users/rafaelcgama/Projects/hotels" # Change to the path where the hotels project is stored
ARCHIVE_FILE="$PROJECT_DIR/data/rates.zip"  # This will store the compressed file

# Activate your virtual environment
source "$PROJECT_DIR/.venv/bin/activate"

# Change to project directory to ensure relative paths work
cd "$PROJECT_DIR"

# Run the Python script from inside the correct folder
python collect_rates.py

# Zip all CSVs into archive
cd data
zip -r "$ARCHIVE_FILE" *.csv

# Deactivate venv
deactivate

#python send_email.py