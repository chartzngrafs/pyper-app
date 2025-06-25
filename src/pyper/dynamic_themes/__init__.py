"""
Dynamic Themed Playlists Feature for Pyper
Phase 1: Core Theme Discovery (MVP)

This module implements library-specific theme discovery through clustering analysis
rather than natural language processing, making it more feasible and reliable.
"""

__version__ = "1.0.0-mvp"
__author__ = "Pyper Development Team"

# Import main components
from .dynamic_theme_engine import DynamicThemeEngine
from .config_manager import DynamicThemesConfig

# Import UI components - using import from ui package
from .ui import ThemedPlaylistsTab

__all__ = [
    'DynamicThemeEngine',
    'DynamicThemesConfig', 
    'ThemedPlaylistsTab'
] 