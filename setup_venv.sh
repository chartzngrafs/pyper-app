#!/bin/bash

# Pyper Virtual Environment Setup Script
# This script creates a virtual environment and installs all dependencies
# including the optional dynamic themes feature dependencies.

echo "🎵 Setting up Pyper virtual environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv pyper_venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source pyper_venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install core dependencies
echo "📚 Installing core Pyper dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "🚀 To run Pyper with dynamic themes support:"
echo "   source pyper_venv/bin/activate"
echo "   python pyper.py"
echo ""
echo "📝 To deactivate the virtual environment later:"
echo "   deactivate"
echo ""
echo "🎭 The 'Your Library Themes' tab will now be available in Pyper!" 