"""
Advanced Settings Dialog for Dynamic Themes
UI for configuring Phase 2 advanced analysis options
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QCheckBox, QComboBox, QSpinBox, QSlider, QTabWidget,
    QWidget, QFormLayout, QDialogButtonBox, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from ..config_manager import DynamicThemesConfig

logger = logging.getLogger('AdvancedSettingsDialog')


class AdvancedSettingsDialog(QDialog):
    """Dialog for configuring advanced dynamic themes options"""
    
    # Signal emitted when settings are applied
    settings_applied = pyqtSignal()
    
    def __init__(self, parent=None, config: Optional[DynamicThemesConfig] = None):
        super().__init__(parent)
        self.config = config or DynamicThemesConfig()
        self.original_config = self.config.config.copy()  # Backup for cancel
        
        self.setup_ui()
        self.load_current_settings()
        self.setup_connections()
        
        logger.info("Advanced settings dialog initialized")
    
    def setup_ui(self):
        """Create the UI layout"""
        self.setWindowTitle("Advanced Theme Discovery Settings")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🎯 Advanced Theme Discovery Configuration")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tabs for different settings categories
        self.tabs = QTabWidget()
        
        # Analysis Tab
        self.analysis_tab = self.create_analysis_tab()
        self.tabs.addTab(self.analysis_tab, "🎵 Analysis")
        
        # Clustering Tab
        self.clustering_tab = self.create_clustering_tab()
        self.tabs.addTab(self.clustering_tab, "🔗 Clustering")
        
        # Cache Tab
        self.cache_tab = self.create_cache_tab()
        self.tabs.addTab(self.cache_tab, "💾 Cache")
        
        # External Services Tab
        self.services_tab = self.create_services_tab()
        self.tabs.addTab(self.services_tab, "🌐 Services")
        
        layout.addWidget(self.tabs)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        
        # Add reset button
        self.reset_button = QPushButton("Reset to Defaults")
        button_box.addButton(self.reset_button, QDialogButtonBox.ButtonRole.ResetRole)
        
        layout.addWidget(button_box)
        
        # Store button references
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        self.apply_button = button_box.button(QDialogButtonBox.StandardButton.Apply)
    
    def create_analysis_tab(self) -> QWidget:
        """Create the analysis settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Advanced Analysis Group
        analysis_group = QGroupBox("Advanced Analysis")
        analysis_layout = QFormLayout(analysis_group)
        
        # Enable advanced analysis
        self.enable_advanced_checkbox = QCheckBox("Enable Advanced Analysis")
        self.enable_advanced_checkbox.setToolTip(
            "Enable Phase 2 features including audio analysis and external API integration"
        )
        analysis_layout.addRow("", self.enable_advanced_checkbox)
        
        # Sample duration
        self.sample_duration_spin = QSpinBox()
        self.sample_duration_spin.setRange(10, 120)
        self.sample_duration_spin.setSuffix(" seconds")
        self.sample_duration_spin.setToolTip(
            "Duration of audio sample to analyze per track (10-120 seconds)"
        )
        analysis_layout.addRow("Sample Duration:", self.sample_duration_spin)
        
        # Analysis timeout
        self.analysis_timeout_spin = QSpinBox()
        self.analysis_timeout_spin.setRange(60, 600)
        self.analysis_timeout_spin.setSuffix(" seconds")
        self.analysis_timeout_spin.setToolTip(
            "Maximum time to spend on analysis before timing out"
        )
        analysis_layout.addRow("Analysis Timeout:", self.analysis_timeout_spin)
        
        # Parallel workers
        self.parallel_workers_spin = QSpinBox()
        self.parallel_workers_spin.setRange(1, 8)
        self.parallel_workers_spin.setToolTip(
            "Number of parallel workers for audio analysis"
        )
        analysis_layout.addRow("Parallel Workers:", self.parallel_workers_spin)
        
        layout.addWidget(analysis_group)
        
        # Audio Features Group
        features_group = QGroupBox("Audio Features to Analyze")
        features_layout = QVBoxLayout(features_group)
        
        self.bpm_checkbox = QCheckBox("BPM Detection")
        self.bpm_checkbox.setToolTip("Analyze beats per minute for tempo-based clustering")
        features_layout.addWidget(self.bpm_checkbox)
        
        self.energy_checkbox = QCheckBox("Energy Analysis")
        self.energy_checkbox.setToolTip("Analyze amplitude and energy levels")
        features_layout.addWidget(self.energy_checkbox)
        
        self.quantization_checkbox = QCheckBox("Quantization Detection")
        self.quantization_checkbox.setToolTip("Detect electronic music through quantization patterns")
        features_layout.addWidget(self.quantization_checkbox)
        
        self.mood_checkbox = QCheckBox("Mood Detection")
        self.mood_checkbox.setToolTip("Detect mood categories (chill, upbeat, energetic, etc.)")
        features_layout.addWidget(self.mood_checkbox)
        
        self.spectral_checkbox = QCheckBox("Spectral Analysis")
        self.spectral_checkbox.setToolTip("Advanced spectral feature analysis")
        features_layout.addWidget(self.spectral_checkbox)
        
        layout.addWidget(features_group)
        layout.addStretch()
        
        return tab
    
    def create_clustering_tab(self) -> QWidget:
        """Create the clustering settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Algorithm Selection Group
        algorithm_group = QGroupBox("Clustering Algorithm")
        algorithm_layout = QFormLayout(algorithm_group)
        
        self.algorithm_combo = QComboBox()
        for key, desc in self.config.CLUSTERING_ALGORITHMS.items():
            self.algorithm_combo.addItem(desc, key)
        self.algorithm_combo.setToolTip(
            "Choose clustering algorithm or let system auto-select best results"
        )
        algorithm_layout.addRow("Algorithm:", self.algorithm_combo)
        
        # User choice option
        self.user_choice_checkbox = QCheckBox("Allow User Algorithm Selection")
        self.user_choice_checkbox.setToolTip(
            "Show algorithm selection in the main interface"
        )
        algorithm_layout.addRow("", self.user_choice_checkbox)
        
        layout.addWidget(algorithm_group)
        
        # Cluster Range Group
        range_group = QGroupBox("Cluster Range")
        range_layout = QFormLayout(range_group)
        
        self.min_clusters_spin = QSpinBox()
        self.min_clusters_spin.setRange(2, 50)
        self.min_clusters_spin.setToolTip("Minimum number of themes to generate")
        range_layout.addRow("Minimum Clusters:", self.min_clusters_spin)
        
        self.max_clusters_spin = QSpinBox()
        self.max_clusters_spin.setRange(5, 50)
        self.max_clusters_spin.setToolTip("Maximum number of themes to generate")
        range_layout.addRow("Maximum Clusters:", self.max_clusters_spin)
        
        layout.addWidget(range_group)
        layout.addStretch()
        
        return tab
    
    def create_cache_tab(self) -> QWidget:
        """Create the cache settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Cache Size Group
        size_group = QGroupBox("Cache Configuration")
        size_layout = QFormLayout(size_group)
        
        self.cache_size_combo = QComboBox()
        for size, desc in self.config.CACHE_SIZE_OPTIONS.items():
            self.cache_size_combo.addItem(desc, size)
        self.cache_size_combo.setToolTip(
            "Maximum disk space for caching analysis results"
        )
        size_layout.addRow("Cache Size:", self.cache_size_combo)
        
        # Cache options
        self.clear_on_analysis_checkbox = QCheckBox("Clear Cache on New Analysis")
        self.clear_on_analysis_checkbox.setToolTip(
            "Clear old analysis data when running new theme discovery"
        )
        size_layout.addRow("", self.clear_on_analysis_checkbox)
        
        self.audio_features_cache_checkbox = QCheckBox("Cache Audio Features")
        self.audio_features_cache_checkbox.setToolTip(
            "Cache extracted audio features to speed up subsequent analyses"
        )
        size_layout.addRow("", self.audio_features_cache_checkbox)
        
        # Cache retention
        self.cache_retention_spin = QSpinBox()
        self.cache_retention_spin.setRange(1, 365)
        self.cache_retention_spin.setSuffix(" days")
        self.cache_retention_spin.setToolTip(
            "How long to keep cached audio features"
        )
        size_layout.addRow("Feature Cache Retention:", self.cache_retention_spin)
        
        layout.addWidget(size_group)
        layout.addStretch()
        
        return tab
    
    def create_services_tab(self) -> QWidget:
        """Create the external services tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # External Services Group
        services_group = QGroupBox("External Services")
        services_layout = QVBoxLayout(services_group)
        
        self.musicbrainz_checkbox = QCheckBox("Enable MusicBrainz Integration")
        self.musicbrainz_checkbox.setToolTip(
            "Use MusicBrainz API for enhanced metadata and genre information"
        )
        services_layout.addWidget(self.musicbrainz_checkbox)
        
        self.lastfm_checkbox = QCheckBox("Enable Last.fm Fallback")
        self.lastfm_checkbox.setToolTip(
            "Use Last.fm as fallback when MusicBrainz is unavailable"
        )
        services_layout.addWidget(self.lastfm_checkbox)
        
        # Rate limiting
        rate_limit_layout = QFormLayout()
        
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(1, 10)
        self.rate_limit_spin.setSuffix(" seconds")
        self.rate_limit_spin.setToolTip(
            "Delay between API requests to respect rate limits"
        )
        rate_limit_layout.addRow("Rate Limit Delay:", self.rate_limit_spin)
        
        self.request_timeout_spin = QSpinBox()
        self.request_timeout_spin.setRange(5, 60)
        self.request_timeout_spin.setSuffix(" seconds")
        self.request_timeout_spin.setToolTip(
            "Timeout for individual API requests"
        )
        rate_limit_layout.addRow("Request Timeout:", self.request_timeout_spin)
        
        services_layout.addLayout(rate_limit_layout)
        layout.addWidget(services_group)
        layout.addStretch()
        
        return tab
    
    def setup_connections(self):
        """Setup signal connections"""
        self.ok_button.clicked.connect(self.accept_settings)
        self.cancel_button.clicked.connect(self.cancel_settings)
        self.apply_button.clicked.connect(self.apply_settings)
        self.reset_button.clicked.connect(self.reset_to_defaults)
        
        # Enable/disable controls based on advanced analysis checkbox
        self.enable_advanced_checkbox.toggled.connect(self.toggle_advanced_controls)
    
    def load_current_settings(self):
        """Load current configuration into UI controls"""
        # Analysis settings
        self.enable_advanced_checkbox.setChecked(self.config.is_advanced_analysis_enabled())
        self.sample_duration_spin.setValue(self.config.get_sample_duration())
        self.analysis_timeout_spin.setValue(self.config.get_analysis_timeout())
        self.parallel_workers_spin.setValue(
            self.config.config.get('advanced_analysis', {}).get('parallel_workers', 2)
        )
        
        # Audio features
        features = self.config.get_enabled_audio_features()
        self.bpm_checkbox.setChecked(features.get('bpm_analysis', True))
        self.energy_checkbox.setChecked(features.get('energy_analysis', True))
        self.quantization_checkbox.setChecked(features.get('quantization_detection', True))
        self.mood_checkbox.setChecked(features.get('mood_detection', True))
        self.spectral_checkbox.setChecked(features.get('spectral_analysis', True))
        
        # Clustering settings
        algorithm = self.config.get_clustering_algorithm()
        for i in range(self.algorithm_combo.count()):
            if self.algorithm_combo.itemData(i) == algorithm:
                self.algorithm_combo.setCurrentIndex(i)
                break
        
        self.user_choice_checkbox.setChecked(
            self.config.config.get('clustering', {}).get('user_choice', True)
        )
        self.min_clusters_spin.setValue(
            self.config.config.get('clustering', {}).get('min_clusters', 5)
        )
        self.max_clusters_spin.setValue(
            self.config.config.get('clustering', {}).get('max_clusters', 25)
        )
        
        # Cache settings
        cache_size = self.config.get_cache_size_mb()
        for i in range(self.cache_size_combo.count()):
            if self.cache_size_combo.itemData(i) == cache_size:
                self.cache_size_combo.setCurrentIndex(i)
                break
        
        self.clear_on_analysis_checkbox.setChecked(
            self.config.config.get('cache', {}).get('clear_on_analysis', True)
        )
        self.audio_features_cache_checkbox.setChecked(
            self.config.config.get('cache', {}).get('audio_features_cache', True)
        )
        self.cache_retention_spin.setValue(
            self.config.config.get('cache', {}).get('feature_cache_days', 30)
        )
        
        # External services
        self.musicbrainz_checkbox.setChecked(self.config.is_musicbrainz_enabled())
        self.lastfm_checkbox.setChecked(self.config.is_lastfm_fallback_enabled())
        self.rate_limit_spin.setValue(int(self.config.get_rate_limit_delay()))
        self.request_timeout_spin.setValue(
            self.config.config.get('external_services', {}).get('request_timeout', 10)
        )
        
        # Update control states
        self.toggle_advanced_controls(self.enable_advanced_checkbox.isChecked())
    
    def toggle_advanced_controls(self, enabled: bool):
        """Enable/disable advanced controls based on checkbox"""
        # Disable all advanced controls if not enabled
        controls = [
            self.sample_duration_spin, self.analysis_timeout_spin, self.parallel_workers_spin,
            self.bpm_checkbox, self.energy_checkbox, self.quantization_checkbox,
            self.mood_checkbox, self.spectral_checkbox
        ]
        
        for control in controls:
            control.setEnabled(enabled)
    
    def apply_settings(self):
        """Apply current settings to configuration"""
        try:
            # Analysis settings
            self.config.enable_advanced_analysis(self.enable_advanced_checkbox.isChecked())
            
            if 'advanced_analysis' not in self.config.config:
                self.config.config['advanced_analysis'] = {}
            self.config.config['advanced_analysis']['sample_duration'] = self.sample_duration_spin.value()
            self.config.config['advanced_analysis']['analysis_timeout'] = self.analysis_timeout_spin.value()
            self.config.config['advanced_analysis']['parallel_workers'] = self.parallel_workers_spin.value()
            
            # Audio features
            if 'audio_features' not in self.config.config:
                self.config.config['audio_features'] = {}
            self.config.config['audio_features']['bpm_analysis'] = self.bpm_checkbox.isChecked()
            self.config.config['audio_features']['energy_analysis'] = self.energy_checkbox.isChecked()
            self.config.config['audio_features']['quantization_detection'] = self.quantization_checkbox.isChecked()
            self.config.config['audio_features']['mood_detection'] = self.mood_checkbox.isChecked()
            self.config.config['audio_features']['spectral_analysis'] = self.spectral_checkbox.isChecked()
            
            # Clustering settings
            self.config.set_clustering_algorithm(self.algorithm_combo.currentData())
            if 'clustering' not in self.config.config:
                self.config.config['clustering'] = {}
            self.config.config['clustering']['user_choice'] = self.user_choice_checkbox.isChecked()
            self.config.config['clustering']['min_clusters'] = self.min_clusters_spin.value()
            self.config.config['clustering']['max_clusters'] = self.max_clusters_spin.value()
            
            # Cache settings
            self.config.set_cache_size_mb(self.cache_size_combo.currentData())
            if 'cache' not in self.config.config:
                self.config.config['cache'] = {}
            self.config.config['cache']['clear_on_analysis'] = self.clear_on_analysis_checkbox.isChecked()
            self.config.config['cache']['audio_features_cache'] = self.audio_features_cache_checkbox.isChecked()
            self.config.config['cache']['feature_cache_days'] = self.cache_retention_spin.value()
            
            # External services
            if 'external_services' not in self.config.config:
                self.config.config['external_services'] = {}
            self.config.config['external_services']['musicbrainz_enabled'] = self.musicbrainz_checkbox.isChecked()
            self.config.config['external_services']['lastfm_fallback'] = self.lastfm_checkbox.isChecked()
            self.config.config['external_services']['rate_limit_delay'] = float(self.rate_limit_spin.value())
            self.config.config['external_services']['request_timeout'] = self.request_timeout_spin.value()
            
            # Save configuration
            self.config.save_config()
            
            # Emit signal
            self.settings_applied.emit()
            
            logger.info("Advanced settings applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
    
    def accept_settings(self):
        """Apply settings and close dialog"""
        self.apply_settings()
        self.accept()
    
    def cancel_settings(self):
        """Cancel changes and close dialog"""
        # Restore original config
        self.config.config = self.original_config
        self.reject()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.config.config = self.config.DEFAULT_CONFIG.copy()
        self.load_current_settings()
        logger.info("Settings reset to defaults") 