#!/bin/bash

# Set up paths — resolve relative to this script's location
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Activate virtual environment if available
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
fi

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Run the Python main orchestrator
python main.py

# Deactivate venv if active
if command -v deactivate &> /dev/null; then
    deactivate
fi