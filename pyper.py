#!/usr/bin/env python3
"""
Pyper - A Modern Navidrome Music Player
Entry point script
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyper.main import main

if __name__ == '__main__':
    main() 