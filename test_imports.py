#!/usr/bin/env python3
"""
Test script to verify dynamic themes dependencies
"""

import sys
import os

print("🧪 Testing Dynamic Themes Dependencies")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")
print()

# Test basic imports
try:
    import numpy as np
    print("✅ numpy imported successfully")
    print(f"   Version: {np.__version__}")
except ImportError as e:
    print(f"❌ numpy import failed: {e}")

try:
    import sklearn
    print("✅ scikit-learn imported successfully")
    print(f"   Version: {sklearn.__version__}")
except ImportError as e:
    print(f"❌ scikit-learn import failed: {e}")

print()

# Test dynamic themes module
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from pyper.dynamic_themes import DynamicThemeEngine, ThemedPlaylistsTab
    print("✅ Dynamic themes modules imported successfully")
except ImportError as e:
    print(f"❌ Dynamic themes import failed: {e}")

print()

# Test creating instances
try:
    # Mock data for testing
    mock_library = {'artists': []}
    mock_client = None
    
    engine = DynamicThemeEngine(mock_library, mock_client)
    print("✅ DynamicThemeEngine created successfully")
except Exception as e:
    print(f"❌ DynamicThemeEngine creation failed: {e}")

print()
print("�� Test complete!") 