#!/usr/bin/env python3
"""
Pyper - A Modern Navidrome Music Player
Main application module
"""

import sys
import os
import json
import hashlib
import random
import string
import sqlite3
import subprocess
import tempfile
import shutil
import logging
import urllib.request
import urllib.parse
import re
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QSplitter,
    QMessageBox, QScrollArea, QMenu, QDialog, QTextEdit, QLineEdit, 
    QTabWidget, QProgressBar, QMenuBar, QGridLayout
)
from PyQt6.QtGui import QAction, QActionGroup, QIcon, QPainter
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

import requests
from qt_material import apply_stylesheet

# Import our extracted modules
try:
    # Try relative imports first (when run as module)
    from .theme_manager import ThemeManager
    from .database_helper import NavidromeDBHelper
    from .subsonic_client import CustomSubsonicClient
    from .background_tasks import LibraryRefreshThread, ImageDownloadThread, ICYMetadataParser
    from .ui_components import NowPlayingDialog, ContextualInfoPanel, AlbumGridWidget
except ImportError:
    # Fall back to absolute imports (when run directly)
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from theme_manager import ThemeManager
    from database_helper import NavidromeDBHelper
    from subsonic_client import CustomSubsonicClient
    from background_tasks import LibraryRefreshThread, ImageDownloadThread, ICYMetadataParser
    from ui_components import NowPlayingDialog, ContextualInfoPanel, AlbumGridWidget

# Setup logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'pyper.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Pyper')

# Log startup
logger.info("Pyper Music Player starting up...")

# --- Constants ---
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900
PLAYER_BAR_HEIGHT = 100
CONTEXTUAL_PANEL_HEIGHT = 180  # Much taller to prevent text cutoff
ARTWORK_SIZE = 80
THUMBNAIL_SIZE = 70
MAX_CONTEXTUAL_ALBUMS = 8
DEFAULT_SEARCH_LIMITS = {'artists': 20, 'albums': 20, 'songs': 50}

# --- Configuration ---
def load_config():
    """Load configuration from config file"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        QMessageBox.critical(None, "Configuration Error", 
                           f"Configuration file not found at {config_path}\n"
                           "Please copy config.example.json to config.json and update with your settings.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        QMessageBox.critical(None, "Configuration Error", 
                           f"Invalid JSON in configuration file: {e}")
        sys.exit(1)

# Load configuration
CONFIG = load_config()
NAVIDROME_URL = CONFIG['navidrome']['server_url']
NAVIDROME_USER = CONFIG['navidrome']['username']
NAVIDROME_PASS = CONFIG['navidrome']['password']

# Update constants from config if available
if 'ui' in CONFIG:
    ui_config = CONFIG['ui']
    DEFAULT_WINDOW_WIDTH = ui_config.get('window_width', DEFAULT_WINDOW_WIDTH)
    DEFAULT_WINDOW_HEIGHT = ui_config.get('window_height', DEFAULT_WINDOW_HEIGHT)


class PyperMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pyper - Modern Navidrome Music Player")
        self.setMinimumSize(CONFIG['ui']['window_width'], CONFIG['ui']['window_height'])
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self.app = QApplication.instance()
        
        # Initialize Navidrome connection
        self.sonic_client = None
        self.library_data = {}
        self.current_queue = []
        self.current_playing_index = -1
        self.current_artwork_pixmap = None
        self.search_results = {}  # Store search results
        self.radio_stations = []  # Store radio stations
        
        # Radio metadata
        self.icy_parser = None
        self.current_radio_track = {}
        self.is_playing_radio = False
        
        # Initialize database helper for play counts
        db_path = CONFIG.get('navidrome', {}).get('database_path')
        ssh_config = {
            'ssh_host': CONFIG.get('navidrome', {}).get('ssh_host'),
            'ssh_user': CONFIG.get('navidrome', {}).get('ssh_user'),
            'ssh_key_path': CONFIG.get('navidrome', {}).get('ssh_key_path')
        }
        self.db_helper = NavidromeDBHelper(db_path, ssh_config)
        self.play_counts = {}
        self.most_played_albums = []
        self.recently_played_albums = []
        self.recently_added_albums = []  # New: Recently added albums
        
        # Initialize now playing dialog (keep for backward compatibility)
        self.now_playing_dialog = NowPlayingDialog(self)
        
        # Initialize contextual info panel
        self.contextual_panel = None
        
        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.mediaStatusChanged.connect(self.media_status_changed)
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        
        # Set window properties
        self.setWindowTitle("Pyper - Modern Navidrome Player")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        # Set application icon
        self.set_application_icon()
        
        # Connect to Navidrome
        self.connect_to_navidrome()
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Stop radio metadata parsing
        if hasattr(self, 'icy_parser') and self.icy_parser:
            self.icy_parser.stop()
            self.icy_parser.wait()
        
        # Clean up album grid threads
        if hasattr(self, 'album_grid') and self.album_grid:
            self.album_grid.cleanup_threads()
            
        # Clean up temporary database files
        if hasattr(self, 'db_helper'):
            self.db_helper.cleanup()
        event.accept()
        
    def setup_ui(self):
        """Setup the main user interface"""
        # Create menu bar
        self.create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create top toolbar
        toolbar_layout = QHBoxLayout()
        
        # Search section
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search artists, albums, songs...")
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        self.search_button.setMinimumWidth(70)
        self.search_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                padding: 5px 10px;
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #444;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #555;
                border: 1px solid #888;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        
        # Controls
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_library)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                padding: 5px 10px;
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #444;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #555;
                border: 1px solid #888;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        
        self.status_label = QLabel("Ready")
        
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.search_input)
        toolbar_layout.addWidget(self.search_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.refresh_button)
        toolbar_layout.addWidget(self.status_label)
        
        main_layout.addLayout(toolbar_layout)
        
        # Create main content area with splitter
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(content_splitter)
        
        # Player bar at top (with proper height)
        player_widget = QWidget()
        player_widget.setMinimumHeight(PLAYER_BAR_HEIGHT)
        player_widget.setMaximumHeight(PLAYER_BAR_HEIGHT + 20)
        player_layout = QHBoxLayout(player_widget)
        
        # Album artwork (properly sized)
        self.artwork_label = QLabel()
        self.artwork_label.setFixedSize(ARTWORK_SIZE, ARTWORK_SIZE)
        self.artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artwork_label.setScaledContents(True)  # Enable proper scaling
        self.artwork_label.setStyleSheet("""
            QLabel {
                border: 1px solid #666;
                background-color: #333;
                color: #fff;
                font-size: 24px;
                font-weight: bold;
            }
            QLabel:hover {
                border: 1px solid #888;
                background-color: #444;
            }
        """)
        self.artwork_label.setText("♪")
        self.artwork_label.mousePressEvent = self.artwork_clicked
        player_layout.addWidget(self.artwork_label)
        
        # Now playing info and controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        controls_layout.setSpacing(5)
        
        # Now playing info
        self.now_playing_label = QLabel("Not playing")
        self.now_playing_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        controls_layout.addWidget(self.now_playing_label)
        
        # Controls row
        controls_row = QHBoxLayout()
        controls_row.setSpacing(10)
        
        # Playback buttons
        self.prev_button = QPushButton("Prev")
        self.play_pause_button = QPushButton("Play")
        self.stop_button = QPushButton("Stop")
        self.next_button = QPushButton("Next")
        
        # Style the buttons consistently
        button_style = """
            QPushButton {
                font-weight: bold;
                min-width: 60px;
                min-height: 35px;
                max-height: 35px;
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #444;
                color: #fff;
                padding: 3px;
            }
            QPushButton:hover {
                background-color: #555;
                border: 1px solid #888;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """
        
        for btn in [self.prev_button, self.play_pause_button, self.stop_button, self.next_button]:
            btn.setStyleSheet(button_style)
        
        self.prev_button.clicked.connect(self.previous_track)
        self.play_pause_button.clicked.connect(self.play_pause)
        self.stop_button.clicked.connect(self.stop)
        self.next_button.clicked.connect(self.next_track)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMaximumHeight(15)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #666;
                border-radius: 2px;
                text-align: center;
                background-color: #444;
                color: #fff;
            }
            QProgressBar::chunk {
                background-color: #8b5cf6;
                border-radius: 2px;
            }
        """)
        # Enable progress bar clicking for time scrubbing
        self.progress_bar.mousePressEvent = self.progress_bar_clicked
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(80)
        
        controls_row.addWidget(self.prev_button)
        controls_row.addWidget(self.play_pause_button)
        controls_row.addWidget(self.stop_button)
        controls_row.addWidget(self.next_button)
        controls_row.addWidget(self.progress_bar)
        controls_row.addWidget(self.time_label)
        
        controls_layout.addLayout(controls_row)
        player_layout.addWidget(controls_widget)
        
        # Spacer for better layout
        player_layout.addStretch()
        
        content_splitter.addWidget(player_widget)
        
        # Main browser area (full width)
        browser_widget = QWidget()
        browser_layout = QVBoxLayout(browser_widget)
        browser_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        
        # Browse tab
        browse_tab = QWidget()
        browse_layout = QHBoxLayout(browse_tab)
        
        # Category list
        self.category_list = QListWidget()
        self.category_list.addItems(["Artists", "Albums", "Playlists", "Genres", "Years"])
        self.category_list.setMaximumWidth(120)
        self.category_list.itemClicked.connect(self.category_selected)
        
        # Items list
        self.items_list = QListWidget()
        self.items_list.itemClicked.connect(self.item_selected)
        self.items_list.itemDoubleClicked.connect(self.items_double_clicked)
        self.items_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.items_list.customContextMenuRequested.connect(self.show_items_context_menu)
        
        # Sub-items list (albums/playlists/etc)
        self.subitems_list = QListWidget()
        self.subitems_list.itemClicked.connect(self.subitem_selected)
        self.subitems_list.itemDoubleClicked.connect(self.subitem_double_clicked)
        self.subitems_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.subitems_list.customContextMenuRequested.connect(self.show_subitems_context_menu)
        
        # Album grid widget (for artist albums)
        self.album_grid = AlbumGridWidget(self)
        self.album_grid.album_selected.connect(self.album_grid_selected)
        self.album_grid.album_double_clicked.connect(self.album_grid_double_clicked)
        self.album_grid.hide()  # Initially hidden
        
        # Songs list
        self.songs_list = QListWidget()
        self.songs_list.itemDoubleClicked.connect(self.song_double_clicked)
        self.songs_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.songs_list.customContextMenuRequested.connect(self.show_songs_context_menu)
        
        browse_layout.addWidget(self.category_list)
        browse_layout.addWidget(self.items_list)
        
        # Create a stacked widget to hold either subitems_list or album_grid
        self.subitems_container = QWidget()
        subitems_container_layout = QVBoxLayout(self.subitems_container)
        subitems_container_layout.setContentsMargins(0, 0, 0, 0)
        subitems_container_layout.setSpacing(0)
        subitems_container_layout.addWidget(self.subitems_list)
        subitems_container_layout.addWidget(self.album_grid)
        
        # Set initial styling for the container - will be updated by theme
        self.subitems_container.setStyleSheet("""
            QWidget {
                border: 1px solid #666;
                background-color: transparent;
            }
        """)
        
        browse_layout.addWidget(self.subitems_container)
        browse_layout.addWidget(self.songs_list)
        
        # Search tab
        search_tab = QWidget()
        search_layout = QVBoxLayout(search_tab)
        
        search_results_layout = QHBoxLayout()
        
        # Search results lists
        search_artists_widget = QWidget()
        search_artists_layout = QVBoxLayout(search_artists_widget)
        search_artists_layout.addWidget(QLabel("Artists"))
        self.search_artists_list = QListWidget()
        self.search_artists_list.itemDoubleClicked.connect(self.search_artist_double_clicked)
        self.search_artists_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_artists_list.customContextMenuRequested.connect(self.show_search_artists_context_menu)
        search_artists_layout.addWidget(self.search_artists_list)
        
        search_albums_widget = QWidget()
        search_albums_layout = QVBoxLayout(search_albums_widget)
        search_albums_layout.addWidget(QLabel("Albums"))
        self.search_albums_list = QListWidget()
        self.search_albums_list.itemDoubleClicked.connect(self.search_album_double_clicked)
        self.search_albums_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_albums_list.customContextMenuRequested.connect(self.show_search_albums_context_menu)
        search_albums_layout.addWidget(self.search_albums_list)
        
        search_songs_widget = QWidget()
        search_songs_layout = QVBoxLayout(search_songs_widget)
        search_songs_layout.addWidget(QLabel("Songs"))
        self.search_songs_list = QListWidget()
        self.search_songs_list.itemDoubleClicked.connect(self.search_song_double_clicked)
        self.search_songs_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_songs_list.customContextMenuRequested.connect(self.show_search_songs_context_menu)
        search_songs_layout.addWidget(self.search_songs_list)
        
        search_results_layout.addWidget(search_artists_widget)
        search_results_layout.addWidget(search_albums_widget)
        search_results_layout.addWidget(search_songs_widget)
        search_layout.addLayout(search_results_layout)
        
        # Queue tab
        queue_tab = QWidget()
        queue_layout = QVBoxLayout(queue_tab)
        
        # Queue header with clear button
        queue_header_layout = QHBoxLayout()
        queue_label = QLabel("Playback Queue")
        queue_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.clear_queue_button = QPushButton("Clear Queue")
        self.clear_queue_button.clicked.connect(self.clear_queue)
        self.clear_queue_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                padding: 5px 10px;
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #444;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #555;
                border: 1px solid #888;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        
        queue_header_layout.addWidget(queue_label)
        queue_header_layout.addStretch()
        queue_header_layout.addWidget(self.clear_queue_button)
        queue_layout.addLayout(queue_header_layout)
        
        self.queue_list = QListWidget()
        self.queue_list.itemDoubleClicked.connect(self.queue_item_double_clicked)
        self.queue_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self.show_queue_context_menu)
        queue_layout.addWidget(self.queue_list)
        
        # Recently Added tab
        recently_added_tab = QWidget()
        recently_added_layout = QVBoxLayout(recently_added_tab)
        
        recently_added_header = QLabel("Recently Added Albums")
        recently_added_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        recently_added_layout.addWidget(recently_added_header)
        
        self.recently_added_list = QListWidget()
        self.recently_added_list.itemDoubleClicked.connect(self.recently_added_double_clicked)
        self.recently_added_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recently_added_list.customContextMenuRequested.connect(self.show_recently_added_context_menu)
        recently_added_layout.addWidget(self.recently_added_list)
        
        # Most Played tab
        most_played_tab = QWidget()
        most_played_layout = QVBoxLayout(most_played_tab)
        
        most_played_header = QLabel("Most Played Albums")
        most_played_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        most_played_layout.addWidget(most_played_header)
        
        self.most_played_list = QListWidget()
        self.most_played_list.itemDoubleClicked.connect(self.most_played_double_clicked)
        self.most_played_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.most_played_list.customContextMenuRequested.connect(self.show_most_played_context_menu)
        most_played_layout.addWidget(self.most_played_list)
        
        # Recently Played tab
        recently_played_tab = QWidget()
        recently_played_layout = QVBoxLayout(recently_played_tab)
        
        recently_played_header = QLabel("Recently Played Albums")
        recently_played_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        recently_played_layout.addWidget(recently_played_header)
        
        self.recently_played_list = QListWidget()
        self.recently_played_list.itemDoubleClicked.connect(self.recently_played_double_clicked)
        self.recently_played_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recently_played_list.customContextMenuRequested.connect(self.show_recently_played_context_menu)
        recently_played_layout.addWidget(self.recently_played_list)
        
        # Radio tab
        radio_tab = QWidget()
        radio_layout = QVBoxLayout(radio_tab)
        
        radio_header = QLabel("Internet Radio Stations")
        radio_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        radio_layout.addWidget(radio_header)
        
        self.radio_list = QListWidget()
        self.radio_list.itemDoubleClicked.connect(self.radio_double_clicked)
        self.radio_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.radio_list.customContextMenuRequested.connect(self.show_radio_context_menu)
        radio_layout.addWidget(self.radio_list)
        
        # Add tabs
        self.tab_widget.addTab(browse_tab, "Browse")
        self.tab_widget.addTab(search_tab, "Search")
        self.tab_widget.addTab(queue_tab, "Queue")
        self.tab_widget.addTab(recently_added_tab, "Recently Added")
        self.tab_widget.addTab(most_played_tab, "Most Played")
        self.tab_widget.addTab(recently_played_tab, "Recently Played")
        self.tab_widget.addTab(radio_tab, "Radio")
        
        browser_layout.addWidget(self.tab_widget)
        content_splitter.addWidget(browser_widget)
        
        # Contextual info panel at the bottom
        self.contextual_panel = ContextualInfoPanel(self)
        content_splitter.addWidget(self.contextual_panel)
        
        # Set splitter proportions (player at top, browser in middle, contextual panel at bottom)
        content_splitter.setSizes([150, 500, 120])
        
    def create_menu_bar(self):
        """Create the application menu bar with theme selection"""
        menubar = self.menuBar()
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # Theme submenu
        theme_menu = view_menu.addMenu('Themes')
        
        # Create action group for theme selection
        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)
        
        # Get current theme from config
        current_theme = CONFIG.get('ui', {}).get('theme', 'dark_teal')
        
        # Add theme actions
        for theme_id, theme_name in self.theme_manager.get_theme_list():
            action = QAction(theme_name, self)
            action.setCheckable(True)
            action.setData(theme_id)
            
            # Check current theme
            if theme_id == current_theme or (current_theme.endswith('.xml') and theme_id == current_theme[:-4]):
                action.setChecked(True)
            
            action.triggered.connect(lambda checked, t_id=theme_id: self.change_theme(t_id))
            
            self.theme_action_group.addAction(action)
            theme_menu.addAction(action)
        
        # Add separator and theme info
        theme_menu.addSeparator()
        info_action = QAction('About Themes...', self)
        info_action.triggered.connect(self.show_theme_info)
        theme_menu.addAction(info_action)
        
    def setup_connections(self):
        """Setup signal connections"""
        pass
    
    def create_context_menu(self, item, add_callback, play_callback):
        """Create a standard context menu for items"""
        menu = QMenu(self)
        
        add_action = menu.addAction("Add to Queue")
        add_action.triggered.connect(lambda: add_callback(item))
        
        play_action = menu.addAction("Play Now")
        play_action.triggered.connect(lambda: play_callback(item))
        
        return menu
    
    def change_theme(self, theme_id):
        """Change the application theme"""
        logger.info(f"Changing theme to: {theme_id}")
        
        # Apply the theme
        if self.theme_manager.apply_theme(self.app, theme_id):
            # Apply element-specific styling (e.g., now playing color)
            self.theme_manager.apply_element_specific_styling(self)
            # Save preference
            self.theme_manager.save_theme_preference(theme_id)
            self.status_label.setText(f"Theme changed to: {self.theme_manager.available_themes[theme_id].get('name', theme_id)}")
        else:
            self.status_label.setText("Failed to apply theme")
            QMessageBox.warning(self, "Theme Error", f"Failed to apply theme: {theme_id}")
    
    def show_theme_info(self):
        """Show information about available themes"""
        info_text = "Available Themes:\n\n"
        
        for theme_id, theme_data in self.theme_manager.available_themes.items():
            name = theme_data.get('name', theme_id)
            description = theme_data.get('description', 'No description available')
            info_text += f"• {name}\n  {description}\n\n"
        
        info_text += "\nCustom themes are loaded from the 'themes' directory.\n"
        info_text += "You can create your own themes by adding JSON files to that directory."
        
        QMessageBox.information(self, "Theme Information", info_text)
    
    def set_application_icon(self):
        """Set the application icon"""
        try:
            # Try to use the custom icon from assets directory
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'pyper-icon.png')
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
                # Also set for the application
                QApplication.instance().setWindowIcon(icon)
                logger.info(f"Application icon set from: {icon_path}")
            else:
                logger.warning(f"Icon file not found at: {icon_path}")
        except Exception as e:
            logger.error(f"Failed to set application icon: {e}")
        
    def connect_to_navidrome(self):
        """Connect to the Navidrome server"""
        try:
            self.sonic_client = CustomSubsonicClient(
                NAVIDROME_URL,
                NAVIDROME_USER,
                NAVIDROME_PASS
            )
            
            # Test connection
            ping_response = self.sonic_client.ping()
            
            if ping_response:
                self.status_label.setText("Connected to Navidrome")
                self.refresh_library()
            else:
                raise Exception("Ping failed - unable to authenticate")
                
        except Exception as e:
            logger.error(f"Connection error details: {e}")
            QMessageBox.critical(self, "Connection Error", 
                               f"Failed to connect to Navidrome server:\n{str(e)}\n\nPlease check your configuration.")
            self.status_label.setText("Connection failed")
    
    def refresh_library(self):
        """Refresh the music library from Navidrome"""
        if not self.sonic_client:
            return
            
        self.refresh_button.setEnabled(False)
        self.status_label.setText("Refreshing library...")
        
        self.refresh_thread = LibraryRefreshThread(self.sonic_client)
        self.refresh_thread.progress.connect(self.status_label.setText)
        self.refresh_thread.finished.connect(self.library_refreshed)
        self.refresh_thread.error.connect(self.refresh_error)
        self.refresh_thread.start()
    
    def library_refreshed(self, library_data):
        """Handle completed library refresh"""
        self.library_data = library_data
        self.refresh_button.setEnabled(True)
        self.status_label.setText("Library refreshed successfully")
        
        # Clear current selections
        self.items_list.clear()
        self.subitems_list.clear()
        self.album_grid.clear()
        self.songs_list.clear()
        self.clear_search_results()
        
        # Auto-expand artists on startup
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)  # Select "Artists"
            self.category_selected(self.category_list.item(0))
        
        # Load play count data and populate new tabs
        self.load_play_count_data()
        
        # Load recently added albums
        self.load_recently_added_albums()
        
        # Load radio stations
        self.load_radio_stations()
    
    def refresh_error(self, error_message):
        """Handle library refresh error"""
        self.refresh_button.setEnabled(True)
        self.status_label.setText("Refresh failed")
        QMessageBox.warning(self, "Refresh Error", error_message)
    
    def category_selected(self, item):
        """Handle category selection (Artists, Albums, Playlists, Genres, Years)"""
        category = item.text()
        self.items_list.clear()
        self.subitems_list.clear()
        self.album_grid.clear()
        self.songs_list.clear()
        
        # Show list and hide grid for all categories
        self.album_grid.hide()
        self.subitems_list.show()
        
        # Clear contextual panel when changing categories
        if self.contextual_panel:
            self.contextual_panel.show()
            self.contextual_panel.show_default_message()
        
        if category == "Artists":
            for artist_group in self.library_data.get('artists', []):
                for artist in artist_group.get('artist', []):
                    list_item = QListWidgetItem(artist['name'])
                    list_item.setData(Qt.ItemDataRole.UserRole, artist)
                    self.items_list.addItem(list_item)
        elif category == "Albums":
            for album in self.library_data.get('albums', []):
                album_title = f"{album['name']} - {album.get('artist', 'Unknown Artist')}"
                # Add play count if available
                if album['id'] in self.play_counts:
                    play_count = self.play_counts[album['id']]['play_count']
                    if play_count > 0:
                        album_title += f" ({play_count} plays)"
                list_item = QListWidgetItem(album_title)
                list_item.setData(Qt.ItemDataRole.UserRole, album)
                self.items_list.addItem(list_item)
        elif category == "Playlists":
            for playlist in self.library_data.get('playlists', []):
                list_item = QListWidgetItem(playlist['name'])
                list_item.setData(Qt.ItemDataRole.UserRole, playlist)
                self.items_list.addItem(list_item)
        elif category == "Genres":
            try:
                self.status_label.setText("Loading genres...")
                logger.info("Loading genres from server")
                genres_response = self.sonic_client.getGenres()
                genres = genres_response.get('subsonic-response', {}).get('genres', {}).get('genre', [])
                for genre in genres:
                    genre_name = genre.get('value', genre.get('name', 'Unknown Genre'))
                    list_item = QListWidgetItem(genre_name)
                    list_item.setData(Qt.ItemDataRole.UserRole, {'name': genre_name, 'type': 'genre'})
                    self.items_list.addItem(list_item)
                self.status_label.setText(f"Loaded {len(genres)} genres")
            except Exception as e:
                logger.error(f"Error loading genres: {e}")
                self.status_label.setText("Error loading genres")
        elif category == "Years":
            # Generate year ranges based on available albums
            years = set()
            for album in self.library_data.get('albums', []):
                year = album.get('year')
                if year and year > 0:
                    years.add(year)
            
            # Create decade ranges
            decades = {}
            for year in sorted(years):
                decade = (year // 10) * 10
                decade_label = f"{decade}s"
                if decade_label not in decades:
                    decades[decade_label] = {'start': decade, 'end': decade + 9, 'count': 0}
                decades[decade_label]['count'] += 1
            
            # Add decade items
            for decade_label, decade_info in sorted(decades.items(), key=lambda x: x[1]['start'], reverse=True):
                display_text = f"{decade_label} ({decade_info['count']} albums)"
                list_item = QListWidgetItem(display_text)
                list_item.setData(Qt.ItemDataRole.UserRole, {'name': decade_label, 'type': 'decade', 'start': decade_info['start'], 'end': decade_info['end']})
                self.items_list.addItem(list_item)
    
    def item_selected(self, item):
        """Handle item selection in the second pane"""
        self.subitems_list.clear()
        self.album_grid.clear()
        self.songs_list.clear()
        data = item.data(Qt.ItemDataRole.UserRole)
        
        if not data:
            return
            
        # Determine what type of item was selected
        if 'albumCount' in data:  # It's an artist, show albums in grid
            try:
                artist_albums = self.sonic_client.getArtist(data['id'])
                albums = artist_albums.get('subsonic-response', {}).get('artist', {}).get('album', [])
                
                # Show album grid and hide list
                self.subitems_list.hide()
                self.album_grid.show()
                
                # Setup album grid
                self.album_grid.set_sonic_client(self.sonic_client)
                self.album_grid.set_play_counts(self.play_counts)
                
                # Apply current theme colors
                if hasattr(self.theme_manager, 'current_theme') and self.theme_manager.current_theme:
                    current_theme_data = self.theme_manager.available_themes.get(self.theme_manager.current_theme, {})
                    if 'colors' in current_theme_data:
                        self.album_grid.apply_theme_colors(current_theme_data['colors'])
                
                self.album_grid.populate_albums(albums)
                
                # Hide contextual panel for artist album browsing (as requested)
                if self.contextual_panel:
                    self.contextual_panel.hide()
                    
            except Exception as e:
                logger.error(f"Error fetching artist albums: {e}")
                
        elif 'artist' in data and 'name' in data and 'songCount' in data:  # It's an album, show songs directly in pane 4
            try:
                # Show list and hide grid
                self.album_grid.hide()
                self.subitems_list.show()
                
                album_songs = self.sonic_client.getAlbum(data['id'])
                for song in album_songs.get('subsonic-response', {}).get('album', {}).get('song', []):
                    track_num = str(song.get('track', '0'))
                    song_title = f"{track_num.zfill(2)}. {song['title']}"
                    if 'duration' in song:
                        duration = self.format_duration(song['duration'])
                        song_title += f" ({duration})"
                    list_item = QListWidgetItem(song_title)
                    list_item.setData(Qt.ItemDataRole.UserRole, song)
                    self.songs_list.addItem(list_item)
                    
                # Load album artwork
                if 'coverArt' in data:
                    self.load_artwork(data['coverArt'])
                
                # Show album info in contextual panel
                if self.contextual_panel:
                    self.contextual_panel.show()
                    self.contextual_panel.show_album_info(data, self.sonic_client)
                    
            except Exception as e:
                logger.error(f"Error fetching album songs: {e}")
                
        elif 'public' in data:  # It's a playlist, show songs directly in pane 4
            try:
                # Show list and hide grid
                self.album_grid.hide()
                self.subitems_list.show()
                
                playlist_songs = self.sonic_client.getPlaylist(data['id'])
                for song in playlist_songs.get('subsonic-response', {}).get('playlist', {}).get('entry', []):
                    song_title = f"{song['title']} - {song.get('artist', 'Unknown Artist')}"
                    if 'duration' in song:
                        duration = self.format_duration(song['duration'])
                        song_title += f" ({duration})"
                    list_item = QListWidgetItem(song_title)
                    list_item.setData(Qt.ItemDataRole.UserRole, song)
                    self.songs_list.addItem(list_item)
                    
                # Show contextual panel
                if self.contextual_panel:
                    self.contextual_panel.show()
                    
            except Exception as e:
                logger.error(f"Error fetching playlist songs: {e}")
                
        elif data.get('type') == 'genre':  # It's a genre, show albums in that genre
            try:
                # Show list and hide grid
                self.album_grid.hide()
                self.subitems_list.show()
                
                self.status_label.setText(f"Loading albums for genre: {data['name']}")
                genre_albums = self.sonic_client.getAlbumList2_byGenre(data['name'])
                albums = genre_albums.get('subsonic-response', {}).get('albumList2', {}).get('album', [])
                for album in albums:
                    album_title = f"{album['name']} - {album.get('artist', 'Unknown Artist')}"
                    if album.get('year'):
                        album_title += f" ({album['year']})"
                    list_item = QListWidgetItem(album_title)
                    list_item.setData(Qt.ItemDataRole.UserRole, album)
                    self.subitems_list.addItem(list_item)
                
                # Show genre info in contextual panel
                if self.contextual_panel:
                    self.contextual_panel.show()
                    self.contextual_panel.show_genre_info(data['name'], albums)
                    
                self.status_label.setText(f"Loaded {len(albums)} albums for {data['name']}")
            except Exception as e:
                logger.error(f"Error fetching genre albums: {e}")
                self.status_label.setText("Error loading genre albums")
                
        elif data.get('type') == 'decade':  # It's a decade, show albums from that decade
            try:
                # Show list and hide grid
                self.album_grid.hide()
                self.subitems_list.show()
                
                self.status_label.setText(f"Loading albums from {data['name']}")
                decade_albums = self.sonic_client.getAlbumList2_byYear(data['start'], data['end'])
                albums = decade_albums.get('subsonic-response', {}).get('albumList2', {}).get('album', [])
                for album in albums:
                    album_title = f"{album['name']} - {album.get('artist', 'Unknown Artist')}"
                    if album.get('year'):
                        album_title += f" ({album['year']})"
                    list_item = QListWidgetItem(album_title)
                    list_item.setData(Qt.ItemDataRole.UserRole, album)
                    self.subitems_list.addItem(list_item)
                
                # Show decade info in contextual panel
                if self.contextual_panel:
                    self.contextual_panel.show()
                    self.contextual_panel.show_decade_info(data['name'], albums)
                    
                self.status_label.setText(f"Loaded {len(albums)} albums from {data['name']}")
            except Exception as e:
                logger.error(f"Error fetching decade albums: {e}")
                self.status_label.setText("Error loading decade albums")
    
    def artwork_clicked(self, event):
        """Handle clicks on album artwork"""
        # Could show a simple now playing dialog or do nothing
        self.show_now_playing()
    
    def progress_bar_clicked(self, event):
        """Handle clicks on progress bar for time scrubbing"""
        if self.media_player.duration() > 0 and not self.is_playing_radio:
            # Calculate the position based on click location
            click_x = event.pos().x()
            bar_width = self.progress_bar.width()
            position_ratio = click_x / bar_width
            
            # Clamp between 0 and 1
            position_ratio = max(0, min(1, position_ratio))
            
            # Calculate new position in milliseconds
            new_position = int(self.media_player.duration() * position_ratio)
            
            # Seek to new position
            self.media_player.setPosition(new_position)
            logger.info(f"Scrubbed to position: {self.format_duration(new_position // 1000)}")
    
    def perform_search(self):
        """Perform search and display results"""
        query = self.search_input.text().strip()
        if not query:
            return
            
        try:
            self.status_label.setText("Searching...")
            results = self.sonic_client.search3(query)
            self.search_results = results.get('subsonic-response', {}).get('searchResult3', {})
            
            self.populate_search_results()
            self.tab_widget.setCurrentIndex(1)  # Switch to search tab
            self.status_label.setText(f"Search complete: '{query}'")
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            self.status_label.setText("Search failed")
    
    def populate_search_results(self):
        """Populate search result lists"""
        self.clear_search_results()
        
        # Artists
        artists = self.search_results.get('artist', [])
        for artist in artists:
            list_item = QListWidgetItem(artist['name'])
            list_item.setData(Qt.ItemDataRole.UserRole, artist)
            self.search_artists_list.addItem(list_item)
        
        # Albums
        albums = self.search_results.get('album', [])
        for album in albums:
            album_title = f"{album['name']} - {album.get('artist', 'Unknown Artist')}"
            list_item = QListWidgetItem(album_title)
            list_item.setData(Qt.ItemDataRole.UserRole, album)
            self.search_albums_list.addItem(list_item)
        
        # Songs
        songs = self.search_results.get('song', [])
        for song in songs:
            song_title = f"{song['title']} - {song.get('artist', 'Unknown Artist')}"
            if 'duration' in song:
                duration = self.format_duration(song['duration'])
                song_title += f" ({duration})"
            list_item = QListWidgetItem(song_title)
            list_item.setData(Qt.ItemDataRole.UserRole, song)
            self.search_songs_list.addItem(list_item)
    
    def clear_search_results(self):
        """Clear all search result lists"""
        self.search_artists_list.clear()
        self.search_albums_list.clear()
        self.search_songs_list.clear()
    
    def load_play_count_data(self):
        """Load play count data from Navidrome database or API"""
        try:
            self.status_label.setText("Loading play count data...")
            
            # Try database first
            self.play_counts = self.db_helper.get_album_play_counts()
            self.most_played_albums = self.db_helper.get_most_played_albums()
            self.recently_played_albums = self.db_helper.get_recently_played_albums()
            
            # If database approach failed, try API fallback
            if not self.play_counts and not self.most_played_albums:
                self.status_label.setText("Database unavailable, trying API fallback...")
                self.load_api_play_data()
            
            self.populate_most_played_list()
            self.populate_recently_played_list()
            
            if self.play_counts or self.most_played_albums:
                source = "database" if self.play_counts else "API"
                self.status_label.setText(f"Loaded play data from {source}")
            else:
                self.status_label.setText("Library refreshed (no play count data available)")
                
        except Exception as e:
            print(f"Error loading play count data: {e}")
            self.status_label.setText("Library refreshed (play count data unavailable)")
    
    def load_api_play_data(self):
        """Load play data using Navidrome API as fallback"""
        try:
            # Try to get frequently played albums
            frequent_response = self.sonic_client.getAlbumList2_byFrequent(50)
            if frequent_response:
                albums = frequent_response.get('subsonic-response', {}).get('albumList2', {}).get('album', [])
                self.most_played_albums = []
                for i, album in enumerate(albums):
                    album_data = album.copy()
                    album_data['playCount'] = 50 - i  # Estimate based on order
                    self.most_played_albums.append(album_data)
            
            # Try to get recently played albums
            recent_response = self.sonic_client.getAlbumList2_byRecent(50)
            if recent_response:
                albums = recent_response.get('subsonic-response', {}).get('albumList2', {}).get('album', [])
                self.recently_played_albums = []
                for album in albums:
                    album_data = album.copy()
                    album_data['playCount'] = 1  # Default count
                    self.recently_played_albums.append(album_data)
                    
        except Exception as e:
            print(f"API fallback failed: {e}")
    
    def populate_most_played_list(self):
        """Populate the most played albums list"""
        self.most_played_list.clear()
        for album in self.most_played_albums:
            album_title = f"{album['name']} - {album['artist']}"
            if album.get('year'):
                album_title += f" ({album['year']})"
            album_title += f" • {album['playCount']} plays"
            
            list_item = QListWidgetItem(album_title)
            list_item.setData(Qt.ItemDataRole.UserRole, album)
            self.most_played_list.addItem(list_item)
    
    def populate_recently_played_list(self):
        """Populate the recently played albums list"""
        self.recently_played_list.clear()
        for album in self.recently_played_albums:
            album_title = f"{album['name']} - {album['artist']}"
            if album.get('year'):
                album_title += f" ({album['year']})"
            
            # Format last played date
            if album.get('lastPlayed'):
                from datetime import datetime
                try:
                    # Assuming ISO format timestamp
                    dt = datetime.fromisoformat(album['lastPlayed'].replace('Z', '+00:00'))
                    album_title += f" • Last played: {dt.strftime('%Y-%m-%d')}"
                except:
                    album_title += f" • {album['playCount']} plays"
            
            list_item = QListWidgetItem(album_title)
            list_item.setData(Qt.ItemDataRole.UserRole, album)
            self.recently_played_list.addItem(list_item)
    
    def most_played_double_clicked(self, item):
        """Handle double-click on most played album"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            queue_start_index = len(self.current_queue)
            self.add_album_songs_to_queue(data)
            if self.current_queue:
                self.play_track(queue_start_index)
    
    def recently_played_double_clicked(self, item):
        """Handle double-click on recently played album"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            queue_start_index = len(self.current_queue)
            self.add_album_songs_to_queue(data)
            if self.current_queue:
                self.play_track(queue_start_index)
    
    def show_most_played_context_menu(self, position):
        """Show context menu for most played albums"""
        item = self.most_played_list.itemAt(position)
        if not item:
            return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_album_songs_to_queue(data))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.most_played_double_clicked(item))
        
        menu.addSeparator()
        
        # Add "Go to Album" option
        go_to_album_action = menu.addAction("Go to Album")
        go_to_album_action.triggered.connect(lambda: self.go_to_browse_item(data, 'album'))
        
        # Add "Go to Artist" option if artist info is available
        if data and data.get('artist'):
            go_to_artist_action = menu.addAction("Go to Artist")
            go_to_artist_action.triggered.connect(lambda: self.go_to_browse_item(data, 'artist'))
        
        menu.exec(self.most_played_list.mapToGlobal(position))
    
    def show_recently_played_context_menu(self, position):
        """Show context menu for recently played albums"""
        item = self.recently_played_list.itemAt(position)
        if not item:
            return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_album_songs_to_queue(data))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.recently_played_double_clicked(item))
        
        menu.addSeparator()
        
        # Add "Go to Album" option
        go_to_album_action = menu.addAction("Go to Album")
        go_to_album_action.triggered.connect(lambda: self.go_to_browse_item(data, 'album'))
        
        # Add "Go to Artist" option if artist info is available
        if data and data.get('artist'):
            go_to_artist_action = menu.addAction("Go to Artist")
            go_to_artist_action.triggered.connect(lambda: self.go_to_browse_item(data, 'artist'))
        
        menu.exec(self.recently_played_list.mapToGlobal(position))
    

    
    # Search result handlers
    def search_artist_double_clicked(self, item):
        """Handle double-click on search artist result"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            queue_start_index = len(self.current_queue)
            self.add_artist_songs_to_queue(data)
            if self.current_queue:
                self.play_track(queue_start_index)
    
    def search_album_double_clicked(self, item):
        """Handle double-click on search album result"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            queue_start_index = len(self.current_queue)
            self.add_album_songs_to_queue(data)
            if self.current_queue:
                self.play_track(queue_start_index)
    
    def search_song_double_clicked(self, item):
        """Handle double-click on search song result"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and 'title' in data:
            queue_start_index = len(self.current_queue)
            self.add_songs_to_queue([data])
            self.play_track(queue_start_index)
    
    # Context menus for search results
    def show_search_artists_context_menu(self, position):
        """Show context menu for search artists"""
        item = self.search_artists_list.itemAt(position)
        if not item:
            return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_search_artist_to_queue(item))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.search_artist_double_clicked(item))
        
        menu.addSeparator()
        
        # Add "Go to Artist" option
        go_to_artist_action = menu.addAction("Go to Artist")
        go_to_artist_action.triggered.connect(lambda: self.go_to_browse_item(data, 'artist'))
        
        menu.exec(self.search_artists_list.mapToGlobal(position))
    
    def show_search_albums_context_menu(self, position):
        """Show context menu for search albums"""
        item = self.search_albums_list.itemAt(position)
        if not item:
            return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_search_album_to_queue(item))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.search_album_double_clicked(item))
        
        menu.addSeparator()
        
        # Add "Go to Album" option
        go_to_album_action = menu.addAction("Go to Album")
        go_to_album_action.triggered.connect(lambda: self.go_to_browse_item(data, 'album'))
        
        # Add "Go to Artist" option if artist info is available
        if data and data.get('artist'):
            go_to_artist_action = menu.addAction("Go to Artist")
            go_to_artist_action.triggered.connect(lambda: self.go_to_browse_item(data, 'artist'))
        
        menu.exec(self.search_albums_list.mapToGlobal(position))
    
    def show_search_songs_context_menu(self, position):
        """Show context menu for search songs"""
        item = self.search_songs_list.itemAt(position)
        if not item:
            return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_search_song_to_queue(item))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.search_song_double_clicked(item))
        
        menu.addSeparator()
        
        # Add "Go to Song" option (navigates to album and selects song)
        go_to_song_action = menu.addAction("Go to Song")
        go_to_song_action.triggered.connect(lambda: self.go_to_browse_item(data, 'song'))
        
        # Add "Go to Album" option if album info is available
        if data and data.get('album'):
            go_to_album_action = menu.addAction("Go to Album")
            go_to_album_action.triggered.connect(lambda: self.go_to_browse_item(data, 'album'))
        
        # Add "Go to Artist" option if artist info is available
        if data and data.get('artist'):
            go_to_artist_action = menu.addAction("Go to Artist")
            go_to_artist_action.triggered.connect(lambda: self.go_to_browse_item(data, 'artist'))
        
        menu.exec(self.search_songs_list.mapToGlobal(position))
    
    def add_search_artist_to_queue(self, item):
        """Add search artist to queue"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.add_artist_songs_to_queue(data)
    
    def add_search_album_to_queue(self, item):
        """Add search album to queue"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.add_album_songs_to_queue(data)
    
    def add_search_song_to_queue(self, item):
        """Add search song to queue"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and 'title' in data:
            self.add_songs_to_queue([data])
    
    def add_artist_songs_to_queue(self, artist_data):
        """Add all songs from an artist to queue"""
        try:
            artist_albums = self.sonic_client.getArtist(artist_data['id'])
            albums = artist_albums.get('subsonic-response', {}).get('artist', {}).get('album', [])
            songs_to_add = []
            for album in albums:
                album_songs = self.sonic_client.getAlbum(album['id'])
                songs = album_songs.get('subsonic-response', {}).get('album', {}).get('song', [])
                songs_to_add.extend(songs)
            
            if songs_to_add:
                self.add_songs_to_queue(songs_to_add)
        except Exception as e:
            print(f"Error adding artist songs to queue: {e}")
    
    def add_album_songs_to_queue(self, album_data):
        """Add all songs from an album to queue"""
        try:
            album_songs = self.sonic_client.getAlbum(album_data['id'])
            songs = album_songs.get('subsonic-response', {}).get('album', {}).get('song', [])
            if songs:
                self.add_songs_to_queue(songs)
        except Exception as e:
            print(f"Error adding album songs to queue: {e}")
    
    def items_double_clicked(self, item):
        """Handle double-click on items in the second pane - add to queue and play"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        songs_to_add = []
        
        if 'albumCount' in data:  # It's an artist, add all their songs
            try:
                artist_albums = self.sonic_client.getArtist(data['id'])
                albums = artist_albums.get('subsonic-response', {}).get('artist', {}).get('album', [])
                for album in albums:
                    album_songs = self.sonic_client.getAlbum(album['id'])
                    songs = album_songs.get('subsonic-response', {}).get('album', {}).get('song', [])
                    songs_to_add.extend(songs)
            except Exception as e:
                print(f"Error fetching artist songs: {e}")
                
        elif 'artist' in data and 'name' in data and 'songCount' in data:  # It's an album
            try:
                album_songs = self.sonic_client.getAlbum(data['id'])
                songs = album_songs.get('subsonic-response', {}).get('album', {}).get('song', [])
                songs_to_add.extend(songs)
            except Exception as e:
                print(f"Error fetching album songs: {e}")
                
        elif 'public' in data:  # It's a playlist
            try:
                playlist_songs = self.sonic_client.getPlaylist(data['id'])
                songs = playlist_songs.get('subsonic-response', {}).get('playlist', {}).get('entry', [])
                songs_to_add.extend(songs)
            except Exception as e:
                print(f"Error fetching playlist songs: {e}")
        
        if songs_to_add:
            queue_start_index = len(self.current_queue)
            self.add_songs_to_queue(songs_to_add)
            # Start playing the first song we just added
            self.play_track(queue_start_index)
    
    def show_items_context_menu(self, position):
        """Show context menu for items in the second pane"""
        item = self.items_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu(self)
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_item_to_queue(item))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.items_double_clicked(item))
        
        menu.exec(self.items_list.mapToGlobal(position))
    
    def add_item_to_queue(self, item):
        """Add an item (artist/album/playlist) to queue without playing"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        songs_to_add = []
        
        if 'albumCount' in data:  # It's an artist
            try:
                artist_albums = self.sonic_client.getArtist(data['id'])
                albums = artist_albums.get('subsonic-response', {}).get('artist', {}).get('album', [])
                for album in albums:
                    album_songs = self.sonic_client.getAlbum(album['id'])
                    songs = album_songs.get('subsonic-response', {}).get('album', {}).get('song', [])
                    songs_to_add.extend(songs)
            except Exception as e:
                print(f"Error fetching artist songs: {e}")
                
        elif 'artist' in data and 'name' in data and 'songCount' in data:  # It's an album
            try:
                album_songs = self.sonic_client.getAlbum(data['id'])
                songs = album_songs.get('subsonic-response', {}).get('album', {}).get('song', [])
                songs_to_add.extend(songs)
            except Exception as e:
                print(f"Error fetching album songs: {e}")
                
        elif 'public' in data:  # It's a playlist
            try:
                playlist_songs = self.sonic_client.getPlaylist(data['id'])
                songs = playlist_songs.get('subsonic-response', {}).get('playlist', {}).get('entry', [])
                songs_to_add.extend(songs)
            except Exception as e:
                print(f"Error fetching playlist songs: {e}")
        
        if songs_to_add:
            self.add_songs_to_queue(songs_to_add)
    
    def subitem_selected(self, item):
        """Handle selection in the third pane (albums from artists)"""
        self.songs_list.clear()
        data = item.data(Qt.ItemDataRole.UserRole)
        
        if not data:
            return
            
        # This should be an album, show its songs in pane 4
        if 'artist' in data and 'name' in data:
            try:
                album_songs = self.sonic_client.getAlbum(data['id'])
                for song in album_songs.get('subsonic-response', {}).get('album', {}).get('song', []):
                    track_num = str(song.get('track', '0'))
                    song_title = f"{track_num.zfill(2)}. {song['title']}"
                    if 'duration' in song:
                        duration = self.format_duration(song['duration'])
                        song_title += f" ({duration})"
                    list_item = QListWidgetItem(song_title)
                    list_item.setData(Qt.ItemDataRole.UserRole, song)
                    self.songs_list.addItem(list_item)
                    
                # Load album artwork
                if 'coverArt' in data:
                    self.load_artwork(data['coverArt'])
                
                # Show album info in contextual panel
                if self.contextual_panel:
                    self.contextual_panel.show_album_info(data, self.sonic_client)
                    
            except Exception as e:
                logger.error(f"Error fetching album songs: {e}")
    
    def song_double_clicked(self, item):
        """Handle double-click on songs in the fourth pane - add to queue and play"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and 'title' in data:
            queue_start_index = len(self.current_queue)
            self.add_songs_to_queue([data])
            self.play_track(queue_start_index)
    
    def show_songs_context_menu(self, position):
        """Show context menu for songs in the fourth pane"""
        item = self.songs_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu(self)
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_song_to_queue(item))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.song_double_clicked(item))
        
        menu.exec(self.songs_list.mapToGlobal(position))
    
    def add_song_to_queue(self, item):
        """Add a single song to queue without playing"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and 'title' in data:
            self.add_songs_to_queue([data])
    
    def subitem_double_clicked(self, item):
        """Handle double-click on subitem - add to queue and play"""
        data = item.data(Qt.ItemDataRole.UserRole)
        
        if not data:
            return
            
        songs_to_add = []
        
        # If it's an album, add all songs to queue
        if 'artist' in data and 'name' in data and 'song' not in data:
            try:
                album_songs = self.sonic_client.getAlbum(data['id'])
                songs = album_songs.get('subsonic-response', {}).get('album', {}).get('song', [])
                songs_to_add.extend(songs)
            except Exception as e:
                print(f"Error adding album to queue: {e}")
        # If it's a song, add just that song
        elif 'title' in data:
            songs_to_add.append(data)
            
        if songs_to_add:
            queue_start_index = len(self.current_queue)
            self.add_songs_to_queue(songs_to_add)
            self.play_track(queue_start_index)
    
    def show_subitems_context_menu(self, position):
        """Show context menu for subitems in the third pane"""
        item = self.subitems_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu(self)
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_subitem_to_queue(item))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.subitem_double_clicked(item))
        
        menu.exec(self.subitems_list.mapToGlobal(position))
    
    def add_subitem_to_queue(self, item):
        """Add a subitem (album/song) to queue without playing"""
        data = item.data(Qt.ItemDataRole.UserRole)
        
        if not data:
            return
            
        songs_to_add = []
        
        # If it's an album, add all songs to queue
        if 'artist' in data and 'name' in data and 'song' not in data:
            try:
                album_songs = self.sonic_client.getAlbum(data['id'])
                songs = album_songs.get('subsonic-response', {}).get('album', {}).get('song', [])
                songs_to_add.extend(songs)
            except Exception as e:
                print(f"Error adding album to queue: {e}")
        # If it's a song, add just that song
        elif 'title' in data:
            songs_to_add.append(data)
            
        if songs_to_add:
            self.add_songs_to_queue(songs_to_add)
    
    def album_grid_selected(self, album_data):
        """Handle album selection in the grid"""
        self.songs_list.clear()
        
        if not album_data:
            return
            
        # Show album songs in pane 4
        try:
            album_songs = self.sonic_client.getAlbum(album_data['id'])
            for song in album_songs.get('subsonic-response', {}).get('album', {}).get('song', []):
                track_num = str(song.get('track', '0'))
                song_title = f"{track_num.zfill(2)}. {song['title']}"
                if 'duration' in song:
                    duration = self.format_duration(song['duration'])
                    song_title += f" ({duration})"
                list_item = QListWidgetItem(song_title)
                list_item.setData(Qt.ItemDataRole.UserRole, song)
                self.songs_list.addItem(list_item)
                
            # Load album artwork
            if 'coverArt' in album_data:
                self.load_artwork(album_data['coverArt'])
                
        except Exception as e:
            logger.error(f"Error fetching album songs from grid: {e}")
    
    def album_grid_double_clicked(self, album_data):
        """Handle double-click on album in grid - add to queue and play"""
        if not album_data:
            return
            
        try:
            album_songs = self.sonic_client.getAlbum(album_data['id'])
            songs = album_songs.get('subsonic-response', {}).get('album', {}).get('song', [])
            if songs:
                queue_start_index = len(self.current_queue)
                self.add_songs_to_queue(songs)
                self.play_track(queue_start_index)
        except Exception as e:
            logger.error(f"Error playing album from grid: {e}")
    
    def add_album_to_queue_from_grid(self, album_data):
        """Add album to queue from grid context menu"""
        if not album_data:
            return
            
        try:
            album_songs = self.sonic_client.getAlbum(album_data['id'])
            songs = album_songs.get('subsonic-response', {}).get('album', {}).get('song', [])
            if songs:
                self.add_songs_to_queue(songs)
        except Exception as e:
            logger.error(f"Error adding album to queue from grid: {e}")

    def add_songs_to_queue(self, songs):
        """Add songs to the playback queue"""
        for song in songs:
            self.current_queue.append(song)
            song_title = f"{song['title']} - {song.get('artist', 'Unknown Artist')}"
            self.queue_list.addItem(song_title)
        
        self.status_label.setText(f"Added {len(songs)} song(s) to queue")
    
    def queue_item_double_clicked(self, item):
        """Handle double-click on queue item (start playback)"""
        row = self.queue_list.row(item)
        self.play_track(row)
    
    def clear_queue(self):
        """Clear the entire playback queue"""
        self.current_queue.clear()
        self.queue_list.clear()
        self.current_playing_index = -1
        self.status_label.setText("Queue cleared")
    
    def show_queue_context_menu(self, position):
        """Show context menu for queue items"""
        item = self.queue_list.itemAt(position)
        if not item:
            return
            
        data = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        
        # Delete single item
        delete_action = menu.addAction("Remove from Queue")
        delete_action.triggered.connect(lambda: self.remove_queue_item(self.queue_list.row(item)))
        
        # Play this item
        play_action = menu.addAction("Play Now")
        play_action.triggered.connect(lambda: self.play_track(self.queue_list.row(item)))
        
        menu.addSeparator()
        
        # Add "Go to Song" option (navigates to album and selects song)
        go_to_song_action = menu.addAction("Go to Song")
        go_to_song_action.triggered.connect(lambda: self.go_to_browse_item(data, 'song'))
        
        # Add "Go to Album" option if album info is available
        if data and data.get('album'):
            go_to_album_action = menu.addAction("Go to Album")
            go_to_album_action.triggered.connect(lambda: self.go_to_browse_item(data, 'album'))
        
        # Add "Go to Artist" option if artist info is available
        if data and data.get('artist'):
            go_to_artist_action = menu.addAction("Go to Artist")
            go_to_artist_action.triggered.connect(lambda: self.go_to_browse_item(data, 'artist'))
        
        menu.exec(self.queue_list.mapToGlobal(position))
    
    def remove_queue_item(self, index):
        """Remove a single item from the queue"""
        if 0 <= index < len(self.current_queue):
            # Remove from data
            self.current_queue.pop(index)
            
            # Remove from UI
            self.queue_list.takeItem(index)
            
            # Adjust current playing index if necessary
            if self.current_playing_index > index:
                self.current_playing_index -= 1
            elif self.current_playing_index == index:
                self.current_playing_index = -1  # Currently playing song was removed
                
            self.status_label.setText("Removed song from queue")
    
    
    def show_now_playing(self):
        """Show the now playing information"""
        if self.current_playing_index >= 0 and self.current_playing_index < len(self.current_queue):
            current_song = self.current_queue[self.current_playing_index]
            self.now_playing_dialog.update_track_info(current_song, self.current_artwork_pixmap)
            self.now_playing_dialog.show()
        else:
            QMessageBox.information(self, "Now Playing", "No track currently playing")
    
    def play_track(self, index):
        """Play a specific track from the queue"""
        if 0 <= index < len(self.current_queue):
            song = self.current_queue[index]
            self.current_playing_index = index
            
            # Stop radio metadata if playing radio
            if self.is_playing_radio:
                self.stop_radio_metadata()
            
            try:
                # Get stream URL with token authentication
                salt = self.sonic_client._generate_salt()
                token = hashlib.md5((NAVIDROME_PASS + salt).encode()).hexdigest()
                stream_url = f"{NAVIDROME_URL}/rest/stream?id={song['id']}&u={NAVIDROME_USER}&t={token}&s={salt}&v=1.16.1&c=Pyper"
                
                # Update UI
                self.now_playing_label.setText(f"♪ {song['title']} - {song.get('artist', 'Unknown Artist')}")
                
                # Start playback
                self.media_player.setSource(QUrl(stream_url))
                self.media_player.play()
                self.play_pause_button.setText("Pause")
                
                # Load artwork if available
                if 'coverArt' in song:
                    self.load_artwork(song['coverArt'])
                    
                # Update now playing dialog if it's open
                if self.now_playing_dialog.isVisible():
                    self.now_playing_dialog.update_track_info(song, self.current_artwork_pixmap)
                    
                # Scrobble to Navidrome
                self.scrobble_track(song['id'])
                
            except Exception as e:
                logger.error(f"Error playing track: {e}")
                QMessageBox.warning(self, "Playback Error", f"Failed to play track: {str(e)}")
    
    def play_pause(self):
        """Toggle play/pause"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_pause_button.setText("Play")
        else:
            if self.current_playing_index >= 0:
                self.media_player.play()
                self.play_pause_button.setText("Pause")
            elif self.current_queue:
                self.play_track(0)
    
    def stop(self):
        """Stop playback"""
        # Stop radio metadata if playing radio
        if self.is_playing_radio:
            self.stop_radio_metadata()
            
        self.media_player.stop()
        self.play_pause_button.setText("Play")
        self.now_playing_label.setText("Stopped")
    
    def previous_track(self):
        """Play previous track"""
        if self.current_playing_index > 0:
            self.play_track(self.current_playing_index - 1)
    
    def next_track(self):
        """Play next track"""
        if self.current_playing_index < len(self.current_queue) - 1:
            self.play_track(self.current_playing_index + 1)
    
    def position_changed(self, position):
        """Handle playback position changes"""
        if self.media_player.duration() > 0:
            progress = int((position / self.media_player.duration()) * 100)
            self.progress_bar.setValue(progress)
            
            current_time = self.format_duration(position // 1000)
            total_time = self.format_duration(self.media_player.duration() // 1000)
            self.time_label.setText(f"{current_time} / {total_time}")
    
    def duration_changed(self, duration):
        """Handle duration changes"""
        if duration > 0:
            total_time = self.format_duration(duration // 1000)
            self.time_label.setText(f"00:00 / {total_time}")
    
    def media_status_changed(self, status):
        """Handle media status changes"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Auto-advance to next track
            self.next_track()
    
    def load_artwork(self, cover_art_id):
        """Load album artwork"""
        if cover_art_id and self.sonic_client:
            self.image_thread = ImageDownloadThread(self.sonic_client, cover_art_id)
            self.image_thread.image_ready.connect(self.artwork_loaded)
            self.image_thread.start()
    
    def artwork_loaded(self, pixmap):
        """Handle loaded artwork"""
        # Scale pixmap to fit the artwork label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.artwork_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.artwork_label.setPixmap(scaled_pixmap)
        self.artwork_label.setText("")
        self.current_artwork_pixmap = pixmap  # Store original for other uses
    
    def scrobble_track(self, song_id):
        """Scrobble track to Navidrome"""
        try:
            logger.info(f"Attempting to scrobble track with ID: {song_id}")
            # Navidrome handles scrobbling automatically when we stream
            result = self.sonic_client.scrobble(song_id)
            logger.info(f"Scrobble request sent successfully for track {song_id}")
            logger.debug(f"Scrobble response: {result}")
        except Exception as e:
            logger.error(f"Scrobbling error for track {song_id}: {e}")
            import traceback
            logger.error(f"Scrobble traceback: {traceback.format_exc()}")
    
    def load_radio_stations(self):
        """Load radio stations from library data"""
        self.radio_stations = self.library_data.get('radio_stations', [])
        self.populate_radio_list()
    
    def populate_radio_list(self):
        """Populate the radio stations list"""
        self.radio_list.clear()
        for station in self.radio_stations:
            station_name = station.get('name', 'Unknown Station')
            list_item = QListWidgetItem(station_name)
            list_item.setData(Qt.ItemDataRole.UserRole, station)
            self.radio_list.addItem(list_item)
        
        if self.radio_stations:
            logger.info(f"Loaded {len(self.radio_stations)} radio stations")
        else:
            logger.info("No radio stations found")
    
    def radio_double_clicked(self, item):
        """Handle double-click on radio station - start playing directly"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and 'streamUrl' in data:
            self.play_radio_station(data)
    
    def show_radio_context_menu(self, position):
        """Show context menu for radio stations"""
        item = self.radio_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        play_action = menu.addAction("Play Radio Station")
        play_action.triggered.connect(lambda: self.radio_double_clicked(item))
        
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and data.get('homepageUrl'):
            menu.addSeparator()
            homepage_action = menu.addAction("Open Homepage")
            homepage_action.triggered.connect(lambda: self.open_radio_homepage(data))
        
        menu.exec(self.radio_list.mapToGlobal(position))
    
    def play_radio_station(self, station_data):
        """Play a radio station directly"""
        try:
            stream_url = station_data.get('streamUrl')
            station_name = station_data.get('name', 'Unknown Station')
            
            if not stream_url:
                QMessageBox.warning(self, "Radio Error", "No stream URL available for this station")
                return
            
            # Stop any existing ICY parser
            if self.icy_parser:
                self.icy_parser.stop()
                self.icy_parser.wait()
                self.icy_parser = None
            
            # Update state
            self.is_playing_radio = True
            self.current_radio_track = {'station': station_name}
            
            # Update UI
            self.now_playing_label.setText(f"📻 {station_name}")
            
            # Start radio playback - radio streams directly, no queue needed
            self.media_player.setSource(QUrl(stream_url))
            self.media_player.play()
            self.play_pause_button.setText("Pause")
            
            # Set initial radio artwork
            logger.info("Setting initial radio artwork...")
            self.artwork_label.clear()
            self.artwork_label.setText("📻")
            self.current_artwork_pixmap = None
            
            # Force a simple test artwork to see if the label works
            test_pixmap = QPixmap(80, 80)
            test_pixmap.fill(Qt.GlobalColor.red)
            self.artwork_label.setPixmap(test_pixmap)
            logger.info("Set test red artwork")
            
            # Then clear it back to radio icon
            QTimer.singleShot(2000, lambda: self.artwork_label.setText("📻"))
            
            logger.info("Initial radio artwork set")
            
            # Start ICY metadata parsing
            self.start_icy_metadata_parsing(stream_url, station_data)
            
            # Show in contextual panel if available
            if self.contextual_panel:
                self.show_radio_info_in_panel(station_data)
            
            self.status_label.setText(f"Playing radio: {station_name}")
            logger.info(f"Started playing radio station: {station_name}")
            
        except Exception as e:
            logger.error(f"Error playing radio station: {e}")
            QMessageBox.warning(self, "Radio Error", f"Failed to play radio station: {str(e)}")
    
    def show_radio_info_in_panel(self, station_data):
        """Show radio station info in contextual panel"""
        if not self.contextual_panel:
            return
            
        self.contextual_panel.clear_content()
        
        # Create radio info section
        radio_section = QWidget()
        radio_layout = QVBoxLayout(radio_section)
        radio_layout.setContentsMargins(5, 5, 5, 5)
        
        # Station name
        station_name = QLabel(f"<b>📻 {station_data.get('name', 'Unknown Station')}</b>")
        station_name.setStyleSheet("font-size: 14px; color: white;")
        radio_layout.addWidget(station_name)
        
        # Stream URL (abbreviated)
        stream_url = station_data.get('streamUrl', '')
        if len(stream_url) > 50:
            stream_url = stream_url[:47] + "..."
        url_label = QLabel(f"Stream: {stream_url}")
        url_label.setStyleSheet("color: #ccc; font-size: 12px;")
        radio_layout.addWidget(url_label)
        
        # Homepage URL if available
        if station_data.get('homepageUrl'):
            homepage_url = station_data.get('homepageUrl')
            if len(homepage_url) > 50:
                homepage_url = homepage_url[:47] + "..."
            homepage_label = QLabel(f"Homepage: {homepage_url}")
            homepage_label.setStyleSheet("color: #aaa; font-size: 12px;")
            radio_layout.addWidget(homepage_label)
        
        radio_section.setStyleSheet("background-color: #333; border-radius: 5px; margin-right: 10px;")
        radio_section.setFixedWidth(300)
        self.contextual_panel.content_layout.addWidget(radio_section)
        self.contextual_panel.content_layout.addStretch()
    
    def open_radio_homepage(self, station_data):
        """Open radio station homepage in browser"""
        homepage_url = station_data.get('homepageUrl')
        if homepage_url:
            try:
                import webbrowser
                webbrowser.open(homepage_url)
            except Exception as e:
                logger.error(f"Error opening homepage: {e}")
                QMessageBox.warning(self, "Browser Error", f"Failed to open homepage: {str(e)}")
    
    def start_icy_metadata_parsing(self, stream_url, station_data):
        """Start ICY metadata parsing for radio station"""
        try:
            self.icy_parser = ICYMetadataParser(stream_url)
            self.icy_parser.metadata_updated.connect(self.on_radio_metadata_updated)
            self.icy_parser.artwork_ready.connect(self.on_radio_artwork_ready)
            self.icy_parser.start()
            logger.info(f"Started ICY metadata parsing for {station_data.get('name')}")
        except Exception as e:
            logger.error(f"Failed to start ICY metadata parsing: {e}")
    
    def on_radio_metadata_updated(self, track_info):
        """Handle updated radio metadata"""
        if not self.is_playing_radio:
            return
            
        self.current_radio_track.update(track_info)
        
        # Update UI with track info
        station_name = self.current_radio_track.get('station', 'Radio')
        artist = track_info.get('artist', 'Unknown Artist')
        title = track_info.get('title', 'Unknown Title')
        
        # Update now playing label
        if artist != 'Unknown Artist':
            self.now_playing_label.setText(f"📻 {station_name}: {artist} - {title}")
        else:
            self.now_playing_label.setText(f"📻 {station_name}: {title}")
        
        # Update contextual panel with track info
        if self.contextual_panel:
            self.update_radio_contextual_panel()
        
        # Update status
        self.status_label.setText(f"Radio: {artist} - {title}")
        
        logger.info(f"Radio track updated: {artist} - {title}")
    
    def on_radio_artwork_ready(self, pixmap):
        """Handle radio artwork ready"""
        logger.info(f"Received radio artwork: {pixmap.width()}x{pixmap.height()}")
        
        if not self.is_playing_radio:
            logger.info("Not playing radio - ignoring artwork")
            return
            
        # Update artwork in player
        logger.info("Updating artwork label...")
        self.artwork_label.setPixmap(pixmap)
        self.artwork_label.setText("")
        self.current_artwork_pixmap = pixmap
        
        # Force update
        self.artwork_label.update()
        self.artwork_label.repaint()
        
        logger.info("Radio artwork updated successfully")
    
    def update_radio_contextual_panel(self):
        """Update contextual panel with current radio track info"""
        if not self.contextual_panel or not self.is_playing_radio:
            return
            
        self.contextual_panel.clear_content()
        
        # Create radio track info section
        radio_section = QWidget()
        radio_layout = QVBoxLayout(radio_section)
        radio_layout.setContentsMargins(5, 5, 5, 5)
        
        # Station name
        station_name = self.current_radio_track.get('station', 'Unknown Station')
        station_label = QLabel(f"<b>📻 {station_name}</b>")
        station_label.setStyleSheet("font-size: 14px; color: white;")
        radio_layout.addWidget(station_label)
        
        # Current track info
        artist = self.current_radio_track.get('artist', 'Unknown Artist')
        title = self.current_radio_track.get('title', 'Unknown Title')
        
        if artist != 'Unknown Artist':
            artist_label = QLabel(f"Artist: {artist}")
            artist_label.setStyleSheet("color: #ccc; font-size: 12px;")
            radio_layout.addWidget(artist_label)
        
        title_label = QLabel(f"Track: {title}")
        title_label.setStyleSheet("color: #ccc; font-size: 12px;")
        radio_layout.addWidget(title_label)
        
        # Raw metadata for debugging
        raw_title = self.current_radio_track.get('raw_title', '')
        if raw_title and raw_title != title:
            raw_label = QLabel(f"Stream Title: {raw_title}")
            raw_label.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
            radio_layout.addWidget(raw_label)
        
        radio_section.setStyleSheet("background-color: #333; border-radius: 5px; margin-right: 10px;")
        radio_section.setFixedWidth(350)
        self.contextual_panel.content_layout.addWidget(radio_section)
        self.contextual_panel.content_layout.addStretch()
    
    def stop_radio_metadata(self):
        """Stop radio metadata parsing"""
        if self.icy_parser:
            self.icy_parser.stop()
            self.icy_parser.wait()
            self.icy_parser = None
        self.is_playing_radio = False
        self.current_radio_track = {}
    
    @staticmethod
    def format_duration(seconds):
        """Format duration in seconds to MM:SS"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def load_recently_added_albums(self):
        """Load recently added albums from API"""
        try:
            recent_response = self.sonic_client.getAlbumList2_byNewest(50)
            if recent_response:
                albums = recent_response.get('subsonic-response', {}).get('albumList2', {}).get('album', [])
                self.recently_added_albums = albums
                self.populate_recently_added_list()
        except Exception as e:
            logger.error(f"Error loading recently added albums: {e}")
    
    def populate_recently_added_list(self):
        """Populate the recently added albums list"""
        self.recently_added_list.clear()
        for album in self.recently_added_albums:
            album_title = f"{album['name']} - {album['artist']}"
            if album.get('year'):
                album_title += f" ({album['year']})"
            
            # Add created date if available
            if album.get('created'):
                from datetime import datetime
                try:
                    # Assuming ISO format timestamp  
                    dt = datetime.fromisoformat(album['created'].replace('Z', '+00:00'))
                    album_title += f" • Added: {dt.strftime('%Y-%m-%d')}"
                except:
                    pass  # Skip date formatting if it fails
            
            list_item = QListWidgetItem(album_title)
            list_item.setData(Qt.ItemDataRole.UserRole, album)
            self.recently_added_list.addItem(list_item)
    
    def recently_added_double_clicked(self, item):
        """Handle double-click on recently added album"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            queue_start_index = len(self.current_queue)
            self.add_album_songs_to_queue(data)
            if self.current_queue:
                self.play_track(queue_start_index)
    
    def show_recently_added_context_menu(self, position):
        """Show context menu for recently added albums"""
        item = self.recently_added_list.itemAt(position)
        if not item:
            return
            
        data = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_recently_added_to_queue(item))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.recently_added_double_clicked(item))
        
        menu.addSeparator()
        
        # Add "Go to Album" option
        go_to_album_action = menu.addAction("Go to Album")
        go_to_album_action.triggered.connect(lambda: self.go_to_browse_item(data, 'album'))
        
        # Add "Go to Artist" option if artist info is available
        if data and data.get('artist'):
            go_to_artist_action = menu.addAction("Go to Artist")
            go_to_artist_action.triggered.connect(lambda: self.go_to_browse_item(data, 'artist'))
        
        menu.exec(self.recently_added_list.mapToGlobal(position))
    
    def add_recently_added_to_queue(self, item):
        """Add recently added album to queue without playing"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.add_album_songs_to_queue(data)
    
    def go_to_browse_item(self, item_data, item_type):
        """Navigate to the Browse tab and select the specified item"""
        try:
            # Switch to Browse tab (index 0)
            self.tab_widget.setCurrentIndex(0)
            
            if item_type == 'album':
                # Navigate to Albums category
                self.category_list.setCurrentRow(1)  # Albums is index 1
                self.category_selected(self.category_list.item(1))
                
                # Find and select the album in the items list
                for i in range(self.items_list.count()):
                    list_item = self.items_list.item(i)
                    list_data = list_item.data(Qt.ItemDataRole.UserRole)
                    if list_data and list_data.get('id') == item_data.get('id'):
                        self.items_list.setCurrentRow(i)
                        self.item_selected(list_item)
                        break
                        
            elif item_type == 'artist':
                # Navigate to Artists category
                self.category_list.setCurrentRow(0)  # Artists is index 0
                self.category_selected(self.category_list.item(0))
                
                # Find and select the artist in the items list
                artist_name = item_data.get('artist', item_data.get('name', ''))
                for i in range(self.items_list.count()):
                    list_item = self.items_list.item(i)
                    list_data = list_item.data(Qt.ItemDataRole.UserRole)
                    if list_data and list_data.get('name') == artist_name:
                        self.items_list.setCurrentRow(i)
                        self.item_selected(list_item)
                        break
                        
            elif item_type == 'song':
                # For songs, navigate to the album first
                album_id = item_data.get('albumId')
                if album_id:
                    # Find the album in our library data
                    target_album = None
                    for album in self.library_data.get('albums', []):
                        if album.get('id') == album_id:
                            target_album = album
                            break
                    
                    if target_album:
                        # Navigate to Albums category
                        self.category_list.setCurrentRow(1)  # Albums is index 1
                        self.category_selected(self.category_list.item(1))
                        
                        # Find and select the album
                        for i in range(self.items_list.count()):
                            list_item = self.items_list.item(i)
                            list_data = list_item.data(Qt.ItemDataRole.UserRole)
                            if list_data and list_data.get('id') == album_id:
                                self.items_list.setCurrentRow(i)
                                self.item_selected(list_item)
                                
                                # Now find and select the song in the songs list
                                for j in range(self.songs_list.count()):
                                    song_item = self.songs_list.item(j)
                                    song_data = song_item.data(Qt.ItemDataRole.UserRole)
                                    if song_data and song_data.get('id') == item_data.get('id'):
                                        self.songs_list.setCurrentRow(j)
                                        break
                                break
            
            self.status_label.setText(f"Navigated to {item_type}: {item_data.get('name', item_data.get('title', 'Unknown'))}")
            logger.info(f"Navigated to {item_type} in Browse tab: {item_data.get('name', item_data.get('title', 'Unknown'))}")
            
        except Exception as e:
            logger.error(f"Error navigating to browse item: {e}")
            self.status_label.setText("Failed to navigate to item")

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = PyperMainWindow()
    
    # Apply initial theme
    try:
        theme_id = CONFIG.get('ui', {}).get('theme', 'dark_teal')
        # Handle legacy .xml theme names
        if theme_id.endswith('.xml'):
            theme_id = theme_id[:-4]
        
        logger.info(f"Applying initial theme: {theme_id}")
        window.theme_manager.apply_theme(app, theme_id)
        window.theme_manager.apply_element_specific_styling(window)
    except Exception as e:
        logger.error(f"Failed to apply initial theme: {e}")
        logger.info("Continuing with default theme")
    
    window.show()
    
    logger.info("Pyper application started successfully")
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 