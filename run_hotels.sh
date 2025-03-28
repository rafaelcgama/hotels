#!/bin/bash

# Set up paths
PROJECT_DIR="" # Change to the path where the hotels project is stored
ARCHIVE_FILE="$PROJECT_DIR/data/data.zip"  # This will store the compressed file

# Activate your virtual environment
source "$PROJECT_DIR/.venv/bin/activate"
python main.py

# Combine the current output with previous results and create a compressed archive
cd "$PROJECT_DIR/data"

# Append the new output to the previous one and create the zip archive
zip -r "$ARCHIVE_FILE" *.csv  # Compress all CSVs into a zip archive

# Deactivate the virtual environment (optional)
deactivate