"""
Themed Playlists Tab
Main UI component for displaying and interacting with discovered library themes
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QScrollArea, QGridLayout, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import List, Dict, Any

from .theme_discovery_thread import ThemeDiscoveryThread
from .advanced_settings_dialog import AdvancedSettingsDialog
from ..config_manager import DynamicThemesConfig

logger = logging.getLogger('ThemedPlaylistsTab')


class ThemedPlaylistsTab(QWidget):
    """Tab displaying discovered library themes"""
    
    # Signals for playlist operations
    play_theme_requested = pyqtSignal(list)      # list of tracks to play
    queue_theme_requested = pyqtSignal(list)     # list of tracks to queue
    save_theme_requested = pyqtSignal(dict)      # theme data to save as playlist
    
    def __init__(self, parent, theme_engine):
        super().__init__(parent)
        self.theme_engine = theme_engine
        self.discovered_themes = []
        self.discovery_thread = None
        self.theme_cards = []
        self.config = DynamicThemesConfig()
        
        self.setup_ui()
        self.setup_connections()
        
        logger.info("Themed Playlists Tab initialized")
    
    def setup_ui(self):
        """Create the UI layout and components"""
        layout = QVBoxLayout(self)
        
        # Discovery control section
        self.setup_discovery_controls(layout)
        
        # Themes display area
        self.setup_themes_display(layout)
        
        # Initially show welcome message
        self.show_welcome_state()
    
    def setup_discovery_controls(self, layout):
        """Setup the discovery control section"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        control_layout = QVBoxLayout(control_frame)
        
        # Title
        title = QLabel("Your Library Themes")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        control_layout.addWidget(title)
        
        # Status and control row
        status_layout = QHBoxLayout()
        
        # Discovery button
        self.discover_button = QPushButton("🔍 Discover My Themes")
        self.discover_button.setMinimumHeight(40)
        self.discover_button.clicked.connect(self.start_theme_discovery)
        status_layout.addWidget(self.discover_button)
        
        # Advanced settings button
        self.advanced_settings_button = QPushButton("⚙️ Advanced Settings")
        self.advanced_settings_button.setMinimumHeight(40)
        self.advanced_settings_button.clicked.connect(self.show_advanced_settings)
        status_layout.addWidget(self.advanced_settings_button)
        
        # Status display
        self.status_label = QLabel("Library analysis status: Never analyzed")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        control_layout.addLayout(status_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(20)
        control_layout.addWidget(self.progress_bar)
        
        # Progress status
        self.progress_status = QLabel("")
        self.progress_status.setVisible(False)
        self.progress_status.setStyleSheet("color: #007acc; font-weight: bold;")
        control_layout.addWidget(self.progress_status)
        
        layout.addWidget(control_frame)
    
    def setup_themes_display(self, layout):
        """Setup the themes display area"""
        # Scroll area for themes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Themes container
        self.themes_container = QWidget()
        self.themes_layout = QGridLayout(self.themes_container)
        self.themes_layout.setSpacing(15)
        self.themes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.themes_container)
        layout.addWidget(scroll_area)
    
    def setup_connections(self):
        """Setup signal connections"""
        pass
    
    def show_welcome_state(self):
        """Show the initial welcome message"""
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        
        welcome_label = QLabel("🎵 Discover Your Music Library's Hidden Themes")
        welcome_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        
        description = QLabel(
            "Click 'Discover My Themes' to analyze your music library and find unique "
            "playlist themes based on your collection's characteristics like genre, era, "
            "and listening patterns."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("color: #666; margin: 20px;")
        welcome_layout.addWidget(description)
        
        welcome_layout.addStretch()
        
        # Clear existing content and add welcome
        self.clear_themes_display()
        self.themes_layout.addWidget(welcome_widget, 0, 0)
    
    def start_theme_discovery(self):
        """Start the theme discovery process"""
        if self.discovery_thread and self.discovery_thread.isRunning():
            logger.warning("Theme discovery already in progress")
            return
        
        logger.info("Starting theme discovery")
        
        # Update UI state
        self.discover_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_status.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_status.setText("Initializing...")
        
        # Clear existing themes
        self.clear_themes_display()
        
        # Start discovery thread
        self.discovery_thread = ThemeDiscoveryThread(self.theme_engine)
        self.discovery_thread.analysis_progress.connect(self.update_progress)
        self.discovery_thread.discovery_complete.connect(self.discovery_completed)
        self.discovery_thread.discovery_error.connect(self.discovery_failed)
        self.discovery_thread.start()
    
    def update_progress(self, message: str, percentage: int):
        """Update progress display"""
        self.progress_status.setText(message)
        if percentage >= 0:
            self.progress_bar.setValue(percentage)
    
    def discovery_completed(self, themes: List[Dict[str, Any]]):
        """Handle completion of theme discovery"""
        logger.info(f"Theme discovery completed with {len(themes)} themes")
        
        # Update UI state
        self.discover_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_status.setVisible(False)
        
        # Store themes
        self.discovered_themes = themes
        
        # Update status
        if themes:
            self.status_label.setText(f"Last analysis: Found {len(themes)} unique themes")
            self.display_discovered_themes(themes)
        else:
            self.status_label.setText("Last analysis: No themes found")
            self.show_no_themes_message()
    
    def discovery_failed(self, error_message: str):
        """Handle theme discovery failure"""
        logger.error(f"Theme discovery failed: {error_message}")
        
        # Update UI state
        self.discover_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_status.setVisible(False)
        self.status_label.setText("Last analysis: Failed")
        
        # Show error message
        QMessageBox.warning(
            self, 
            "Theme Discovery Failed", 
            f"Failed to discover themes from your library:\n\n{error_message}\n\n"
            "Please check your library connection and try again."
        )
        
        self.show_welcome_state()
    
    def display_discovered_themes(self, themes: List[Dict[str, Any]]):
        """Display discovered themes in grid layout"""
        self.clear_themes_display()
        
        if not themes:
            self.show_no_themes_message()
            return
        
        # Create theme cards in grid layout
        columns = 3  # 3 columns for theme cards
        
        for i, theme in enumerate(themes):
            row = i // columns
            col = i % columns
            
            theme_card = self.create_theme_card(theme)
            self.themes_layout.addWidget(theme_card, row, col)
            self.theme_cards.append(theme_card)
        
        logger.info(f"Displayed {len(themes)} theme cards")
    
    def create_theme_card(self, theme: Dict[str, Any]) -> QWidget:
        """Create a single theme card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setMinimumSize(280, 120)
        card.setMaximumSize(320, 140)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        # Theme name
        name_label = QLabel(theme['name'])
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Track count
        count_label = QLabel(f"🎵 {theme['track_count']} tracks")
        count_label.setStyleSheet("color: #666;")
        layout.addWidget(count_label)
        
        # Description
        description = QLabel(theme.get('description', ''))
        description.setWordWrap(True)
        description.setStyleSheet("color: #888; font-size: 10px;")
        description.setMaximumHeight(40)
        layout.addWidget(description)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        play_btn = QPushButton("▶")
        play_btn.setToolTip("Play theme")
        play_btn.setMaximumWidth(30)
        play_btn.clicked.connect(lambda: self.play_theme(theme))
        button_layout.addWidget(play_btn)
        
        queue_btn = QPushButton("+")
        queue_btn.setToolTip("Add to queue")
        queue_btn.setMaximumWidth(30)
        queue_btn.clicked.connect(lambda: self.queue_theme(theme))
        button_layout.addWidget(queue_btn)
        
        save_btn = QPushButton("💾")
        save_btn.setToolTip("Save as playlist")
        save_btn.setMaximumWidth(30)
        save_btn.clicked.connect(lambda: self.save_theme(theme))
        button_layout.addWidget(save_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return card
    
    def clear_themes_display(self):
        """Clear all theme cards from display"""
        for i in reversed(range(self.themes_layout.count())):
            child = self.themes_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        self.theme_cards.clear()
    
    def show_no_themes_message(self):
        """Show message when no themes are found"""
        no_themes_widget = QWidget()
        no_themes_layout = QVBoxLayout(no_themes_widget)
        
        message_label = QLabel("🎭 No Themes Found")
        message_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_themes_layout.addWidget(message_label)
        
        help_text = QLabel(
            "Your library might be too small or lack sufficient metadata for theme discovery. "
            "Try adding more music or ensure your tracks have genre and year information."
        )
        help_text.setWordWrap(True)
        help_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_text.setStyleSheet("color: #666; margin: 20px;")
        no_themes_layout.addWidget(help_text)
        
        no_themes_layout.addStretch()
        
        self.themes_layout.addWidget(no_themes_widget, 0, 0)
    
    def play_theme(self, theme: Dict[str, Any]):
        """Request to play a theme's tracks"""
        tracks = theme.get('tracks', [])
        if tracks:
            logger.info(f"Playing theme: {theme['name']} ({len(tracks)} tracks)")
            self.play_theme_requested.emit(tracks)
        else:
            logger.warning(f"No tracks in theme: {theme['name']}")
    
    def queue_theme(self, theme: Dict[str, Any]):
        """Request to queue a theme's tracks"""
        tracks = theme.get('tracks', [])
        if tracks:
            logger.info(f"Queuing theme: {theme['name']} ({len(tracks)} tracks)")
            self.queue_theme_requested.emit(tracks)
        else:
            logger.warning(f"No tracks in theme: {theme['name']}")
    
    def save_theme(self, theme: Dict[str, Any]):
        """Request to save a theme as a playlist"""
        logger.info(f"Saving theme as playlist: {theme['name']}")
        self.save_theme_requested.emit(theme)
    
    def show_advanced_settings(self):
        """Show the advanced settings dialog"""
        try:
            dialog = AdvancedSettingsDialog(self, self.config)
            
            # Connect settings applied signal
            dialog.settings_applied.connect(self.on_settings_applied)
            
            # Show dialog
            result = dialog.exec()
            
            if result == AdvancedSettingsDialog.DialogCode.Accepted:
                logger.info("Advanced settings dialog accepted")
            else:
                logger.info("Advanced settings dialog cancelled")
                
        except Exception as e:
            logger.error(f"Failed to show advanced settings: {e}")
    
    def on_settings_applied(self):
        """Handle when advanced settings are applied"""
        logger.info("Advanced settings applied, updating status")
        
        # Update status based on advanced analysis setting
        if self.config.is_advanced_analysis_enabled():
            self.status_label.setText("Advanced analysis enabled - enhanced theme discovery available")
        else:
            self.status_label.setText("Basic analysis mode - enable advanced features in settings")
        
        # If we have themes and advanced analysis was just enabled, suggest re-analysis
        if self.discovered_themes and self.config.is_advanced_analysis_enabled():
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, 
                "Advanced Analysis Enabled",
                "Advanced analysis has been enabled. Would you like to re-analyze your library "
                "with the new advanced features (audio analysis, external APIs)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.start_theme_discovery() 