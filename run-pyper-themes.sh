#!/bin/bash

# Pyper with Dynamic Themes Launcher
# This script properly sets up the virtual environment and runs Pyper
# with the dynamic themed playlists feature enabled.

echo "🎵 Starting Pyper with Dynamic Themed Playlists..."

# Check if virtual environment exists
if [ ! -d "pyper_venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup_venv.sh first."
    exit 1
fi

# Set up environment
export PYTHONPATH="$(pwd)/pyper_venv/lib/python3.13/site-packages:$PYTHONPATH"

# Run Pyper with virtual environment Python
echo "🚀 Launching Pyper..."
pyper_venv/bin/python pyper.py

echo "👋 Pyper closed." 