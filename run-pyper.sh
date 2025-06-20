#!/bin/bash

# Pyper Music Player Launch Script
# For Manjaro/Arch Linux systems

echo "🎵 Starting Pyper Music Player..."

# Check if config exists
if [ ! -f "config/config.json" ]; then
    echo "❌ Configuration file not found!"
    echo "Please copy config/config.example.json to config/config.json and update with your settings."
    exit 1
fi

echo "✅ Configuration found"
echo ""

# Launch the application
python pyper.py 