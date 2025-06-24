"""
Theme Discovery Background Thread
Handles theme discovery processing without blocking the UI
"""

import logging
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, Any, List

logger = logging.getLogger('ThemeDiscoveryThread')


class ThemeDiscoveryThread(QThread):
    """Background thread for library analysis and theme discovery"""
    
    analysis_progress = pyqtSignal(str, int)     # status message, percentage
    theme_discovered = pyqtSignal(dict)          # individual theme discovered
    discovery_complete = pyqtSignal(list)        # all themes discovered
    discovery_error = pyqtSignal(str)           # error message
    
    def __init__(self, theme_engine):
        super().__init__()
        self.theme_engine = theme_engine
        self.should_stop = False
        
    def run(self):
        """Execute theme discovery pipeline"""
        try:
            logger.info("Starting theme discovery in background thread")
            
            # Check for cached themes first
            cached_themes = self.theme_engine.get_cached_themes()
            if cached_themes:
                logger.info(f"Using cached themes: {len(cached_themes)} themes")
                self.analysis_progress.emit("Loading cached themes...", 50)
                self.discovery_complete.emit(cached_themes)
                return
            
            # Run theme discovery with progress updates
            discovered_themes = self.theme_engine.discover_library_themes(
                progress_callback=self.emit_progress
            )
            
            if self.should_stop:
                logger.info("Theme discovery was cancelled")
                return
            
            self.discovery_complete.emit(discovered_themes)
            logger.info(f"Theme discovery completed: {len(discovered_themes)} themes")
            
        except Exception as e:
            logger.error(f"Theme discovery failed: {e}")
            self.discovery_error.emit(str(e))
    
    def emit_progress(self, message: str, percentage: int):
        """Emit progress signal with status and percentage"""
        if not self.should_stop:
            self.analysis_progress.emit(message, percentage)
    
    def stop(self):
        """Request thread to stop processing"""
        self.should_stop = True
        logger.info("Theme discovery thread stop requested") 