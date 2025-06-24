"""
Dynamic Themed Playlists Feature for Pyper
Phase 1: Core Theme Discovery (MVP)

This module implements library-specific theme discovery through clustering analysis
rather than natural language processing, making it more feasible and reliable.
"""

__version__ = "1.0.0-mvp"
__author__ = "Pyper Development Team"

# Try to import main components - graceful degradation if ML libraries not available
try:
    from .dynamic_theme_engine import DynamicThemeEngine
    from .ui.themed_playlists_tab import ThemedPlaylistsTab
    
    __all__ = [
        'DynamicThemeEngine',
        'ThemedPlaylistsTab'
    ]
    
except ImportError as e:
    # ML dependencies not available - provide stub classes
    import logging
    logger = logging.getLogger('DynamicThemes')
    logger.warning(f"Dynamic themes dependencies not available: {e}")
    logger.info("To enable dynamic themes, install: pip install scikit-learn numpy")
    
    # Provide stub classes that won't crash the application
    class DynamicThemeEngine:
        def __init__(self, *args, **kwargs):
            raise ImportError("Dynamic themes feature requires: pip install scikit-learn numpy")
    
    class ThemedPlaylistsTab:
        def __init__(self, *args, **kwargs):
            raise ImportError("Dynamic themes feature requires: pip install scikit-learn numpy")
    
    __all__ = [
        'DynamicThemeEngine',
        'ThemedPlaylistsTab'
    ] 