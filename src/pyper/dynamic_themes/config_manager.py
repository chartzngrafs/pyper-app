"""
Dynamic Themes Configuration Manager
Handles Phase 2 advanced configuration options with validation and defaults
"""

import logging
import json
import os
from typing import Dict, Any, Optional

logger = logging.getLogger('DynamicThemes.Config')


class DynamicThemesConfig:
    """Configuration manager for dynamic themes advanced features"""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "advanced_analysis": {
            "enabled": False,  # Opt-in for Phase 2 features
            "audio_analysis": False,  # Disabled by default for performance
            "sample_duration": 30,  # Reduced from 45s for faster analysis
            "analysis_timeout": 180,  # 3 minutes max (reduced from 5)
            "parallel_workers": 1,   # Reduced from 2 to avoid rate limiting issues
            "smart_sampling": True   # Enable intelligent sampling for large libraries
        },
        "clustering": {
            "algorithm": "auto",  # "kmeans", "hierarchical", "dbscan", "auto"
            "user_choice": True,   # Allow user to select algorithm
            "min_clusters": 5,
            "max_clusters": 25
        },
        "cache": {
            "max_size_mb": 100,   # 50, 100, 500 options
            "clear_on_analysis": True,
            "feature_cache_days": 30,
            "audio_features_cache": True
        },
        "external_services": {
            "musicbrainz_enabled": True,
            "lastfm_fallback": True,
            "rate_limit_delay": 0.5,  # Reduced from 1.2s - MusicBrainz allows 1 req/sec
            "request_timeout": 8      # Reduced from 10s for faster failure detection
        },
        "audio_features": {
            "bpm_analysis": True,
            "energy_analysis": True,
            "quantization_detection": True,
            "mood_detection": True,
            "spectral_analysis": True
        },
        "external_apis": {
            "musicbrainz_enabled": True,
            "lastfm_enabled": False,  # Requires API key
            "lastfm_api_key": None,   # Set via config or environment variable
            "rate_limit_delay": 1.0
        }
    }
    
    # Available clustering algorithms
    CLUSTERING_ALGORITHMS = {
        "auto": "Automatic (Best Results)",
        "kmeans": "K-Means (Fast)",
        "hierarchical": "Hierarchical (Nested Themes)",
        "dbscan": "DBSCAN (Density-Based)"
    }
    
    # Cache size options
    CACHE_SIZE_OPTIONS = {
        50: "50 MB (Minimal)",
        100: "100 MB (Recommended)",
        500: "500 MB (Maximum Quality)"
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/config.json"
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file with defaults"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    full_config = json.load(f)
                    
                # Extract dynamic_themes section or use defaults
                themes_config = full_config.get('dynamic_themes', {})
                
                # Merge with defaults
                merged_config = self._merge_config(self.DEFAULT_CONFIG, themes_config)
                
                logger.info("Dynamic themes configuration loaded successfully")
                return merged_config
            else:
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                return self.DEFAULT_CONFIG.copy()
                
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_config(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            # Load full config file
            full_config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    full_config = json.load(f)
            
            # Update dynamic_themes section
            full_config['dynamic_themes'] = self.config
            
            # Save back to file
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(full_config, f, indent=4)
                
            logger.info("Dynamic themes configuration saved")
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def is_advanced_analysis_enabled(self) -> bool:
        """Check if advanced analysis is enabled"""
        return self.config.get('advanced_analysis', {}).get('enabled', False)
    
    def enable_advanced_analysis(self, enabled: bool = True):
        """Enable or disable advanced analysis"""
        if 'advanced_analysis' not in self.config:
            self.config['advanced_analysis'] = {}
        self.config['advanced_analysis']['enabled'] = enabled
        logger.info(f"Advanced analysis {'enabled' if enabled else 'disabled'}")
    
    def get_clustering_algorithm(self) -> str:
        """Get selected clustering algorithm"""
        return self.config.get('clustering', {}).get('algorithm', 'auto')
    
    def set_clustering_algorithm(self, algorithm: str):
        """Set clustering algorithm"""
        if algorithm not in self.CLUSTERING_ALGORITHMS:
            logger.warning(f"Unknown algorithm: {algorithm}, using auto")
            algorithm = 'auto'
            
        if 'clustering' not in self.config:
            self.config['clustering'] = {}
        self.config['clustering']['algorithm'] = algorithm
        logger.info(f"Clustering algorithm set to: {algorithm}")
    
    def get_cache_size_mb(self) -> int:
        """Get cache size in MB"""
        return self.config.get('cache', {}).get('max_size_mb', 100)
    
    def set_cache_size_mb(self, size_mb: int):
        """Set cache size in MB"""
        if size_mb not in self.CACHE_SIZE_OPTIONS:
            logger.warning(f"Invalid cache size: {size_mb}, using 100MB")
            size_mb = 100
            
        if 'cache' not in self.config:
            self.config['cache'] = {}
        self.config['cache']['max_size_mb'] = size_mb
        logger.info(f"Cache size set to: {size_mb}MB")
    
    def get_sample_duration(self) -> int:
        """Get audio sample duration in seconds"""
        return self.config.get('advanced_analysis', {}).get('sample_duration', 45)
    
    def get_analysis_timeout(self) -> int:
        """Get analysis timeout in seconds"""
        return self.config.get('advanced_analysis', {}).get('analysis_timeout', 300)
    
    def get_rate_limit_delay(self) -> float:
        """Get rate limit delay for external APIs"""
        return self.config.get('external_services', {}).get('rate_limit_delay', 1.2)
    
    def is_musicbrainz_enabled(self) -> bool:
        """Check if MusicBrainz integration is enabled"""
        return self.config.get('external_services', {}).get('musicbrainz_enabled', True)
    
    def is_lastfm_fallback_enabled(self) -> bool:
        """Check if Last.fm fallback is enabled"""
        return self.config.get('external_services', {}).get('lastfm_fallback', True)
    
    def get_enabled_audio_features(self) -> Dict[str, bool]:
        """Get which audio features are enabled for analysis"""
        return self.config.get('audio_features', {})
    
    def validate_config(self) -> bool:
        """Validate configuration values"""
        try:
            # Check sample duration
            duration = self.get_sample_duration()
            if not (10 <= duration <= 120):
                logger.warning(f"Sample duration {duration}s outside recommended range (10-120s)")
            
            # Check timeout
            timeout = self.get_analysis_timeout()
            if not (60 <= timeout <= 600):
                logger.warning(f"Analysis timeout {timeout}s outside recommended range (60-600s)")
            
            # Check cache size
            cache_size = self.get_cache_size_mb()
            if cache_size not in self.CACHE_SIZE_OPTIONS:
                logger.warning(f"Cache size {cache_size}MB not in recommended options")
            
            return True
            
        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return False 