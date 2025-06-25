"""
Dynamic Themed Playlists Feature for Pyper
Phase 2 Step 2: Advanced Audio Analysis & Metadata Enrichment

Enhanced theme discovery with librosa audio analysis and MusicBrainz metadata.
Backwards compatible with Phase 1 functionality.
"""

__version__ = "2.1.0-step2"
__author__ = "Pyper Development Team"

# Import main components
from .dynamic_theme_engine import DynamicThemeEngine
from .config_manager import DynamicThemesConfig

# Phase 2 Step 2: Advanced analysis modules (optional)
try:
    from .audio_analyzer import AudioAnalyzer
    from .metadata_enricher import MetadataEnricher
    _ADVANCED_AVAILABLE = True
except ImportError:
    AudioAnalyzer = None
    MetadataEnricher = None
    _ADVANCED_AVAILABLE = False

# Import UI components - using import from ui package
from .ui import ThemedPlaylistsTab

__all__ = [
    'DynamicThemeEngine',
    'DynamicThemesConfig', 
    'ThemedPlaylistsTab',
    'AudioAnalyzer',
    'MetadataEnricher'
] 