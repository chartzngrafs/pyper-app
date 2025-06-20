#!/usr/bin/env python3

import sys
import os
import threading
import time
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QSplitter,
    QMessageBox, QProgressBar, QFrame, QScrollArea, QMenu, QDialog,
    QTextEdit, QGridLayout, QLineEdit, QTabWidget, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

import libsonic
from qt_material import apply_stylesheet
import hashlib
import urllib.parse
import requests
import json
import xml.etree.ElementTree as ET
import random
import string

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

class CustomSubsonicClient:
    """Custom Subsonic API client that handles authentication correctly"""
    
    def __init__(self, server_url, username, password):
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        self.app_name = "Pyper"
        self.api_version = "1.16.1"
    
    def _generate_salt(self):
        """Generate a random salt for authentication"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    def _make_request(self, endpoint, params=None):
        """Make an authenticated request to the Subsonic API"""
        if params is None:
            params = {}
        
        salt = self._generate_salt()
        token = hashlib.md5((self.password + salt).encode()).hexdigest()
        
        base_params = {
            'u': self.username,
            't': token,
            's': salt,
            'v': self.api_version,
            'c': self.app_name,
            'f': 'json'
        }
        
        base_params.update(params)
        url = f"{self.server_url}/rest/{endpoint}"
        
        response = requests.get(url, params=base_params)
        response.raise_for_status()
        
        if response.headers.get('content-type', '').startswith('application/json'):
            return response.json()
        else:
            return response.content
    
    def ping(self):
        """Test connection to the server"""
        try:
            result = self._make_request('ping')
            return result.get('subsonic-response', {}).get('status') == 'ok'
        except Exception as e:
            print(f"Ping error: {e}")
            return False
    
    def getArtists(self):
        """Get all artists"""
        return self._make_request('getArtists')
    
    def getAlbumList2(self):
        """Get album list"""
        return self._make_request('getAlbumList2', {'type': 'alphabeticalByName', 'size': 500})
    
    def getPlaylists(self):
        """Get all playlists"""
        return self._make_request('getPlaylists')
    
    def getArtist(self, artist_id):
        """Get artist details with albums"""
        return self._make_request('getArtist', {'id': artist_id})
    
    def getAlbum(self, album_id):
        """Get album details with songs"""
        return self._make_request('getAlbum', {'id': album_id})
    
    def getPlaylist(self, playlist_id):
        """Get playlist details with songs"""
        return self._make_request('getPlaylist', {'id': playlist_id})
    
    def getCoverArt(self, cover_art_id, size=None):
        """Get cover art"""
        params = {'id': cover_art_id}
        if size:
            params['size'] = size
        return self._make_request('getCoverArt', params)
    
    def scrobble(self, song_id, submission=True):
        """Scrobble a track"""
        params = {'id': song_id}
        if submission:
            params['submission'] = 'true'
        return self._make_request('scrobble', params)
    
    def search3(self, query, artist_count=20, album_count=20, song_count=50):
        """Search for artists, albums, and songs"""
        params = {
            'query': query,
            'artistCount': artist_count,
            'albumCount': album_count,
            'songCount': song_count
        }
        return self._make_request('search3', params)

class NowPlayingDialog(QDialog):
    """Now playing flyout dialog with track information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Now Playing")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        
        # Album artwork
        self.artwork_label = QLabel()
        self.artwork_label.setFixedSize(200, 200)
        self.artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artwork_label.setStyleSheet("border: 1px solid gray; background-color: #333;")
        self.artwork_label.setText("No Cover Art")
        layout.addWidget(self.artwork_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Track info
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(80)
        layout.addWidget(self.info_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def update_track_info(self, song, artwork_pixmap=None):
        """Update the dialog with current track information"""
        if artwork_pixmap:
            self.artwork_label.setPixmap(artwork_pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.artwork_label.setText("")
        else:
            self.artwork_label.clear()
            self.artwork_label.setText("No Cover Art")
        
        info_html = f"""
        <b>Title:</b> {song.get('title', 'Unknown')}<br>
        <b>Artist:</b> {song.get('artist', 'Unknown')}<br>
        <b>Album:</b> {song.get('album', 'Unknown')}<br>
        <b>Year:</b> {song.get('year', 'Unknown')}<br>
        <b>Genre:</b> {song.get('genre', 'Unknown')}<br>
        <b>Duration:</b> {PyperMainWindow.format_duration(song.get('duration', 0))}
        """
        self.info_text.setHtml(info_html)

class LibraryRefreshThread(QThread):
    """Thread for refreshing library data from Navidrome server"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, sonic_client):
        super().__init__()
        self.sonic_client = sonic_client
        
    def run(self):
        try:
            self.progress.emit("Connecting to Navidrome server...")
            
            # Fetch all library data
            library_data = {}
            
            self.progress.emit("Fetching artists...")
            artists = self.sonic_client.getArtists()
            library_data['artists'] = artists.get('subsonic-response', {}).get('artists', {}).get('index', [])
            
            self.progress.emit("Fetching albums...")
            albums = self.sonic_client.getAlbumList2()
            library_data['albums'] = albums.get('subsonic-response', {}).get('albumList2', {}).get('album', [])
            
            self.progress.emit("Fetching playlists...")
            playlists = self.sonic_client.getPlaylists()
            library_data['playlists'] = playlists.get('subsonic-response', {}).get('playlists', {}).get('playlist', [])
            
            self.progress.emit("Library refresh complete!")
            self.finished.emit(library_data)
            
        except Exception as e:
            self.error.emit(f"Error refreshing library: {str(e)}")

class ImageDownloadThread(QThread):
    """Thread for downloading album/artist artwork"""
    image_ready = pyqtSignal(QPixmap)
    
    def __init__(self, sonic_client, cover_art_id):
        super().__init__()
        self.sonic_client = sonic_client
        self.cover_art_id = cover_art_id
        
    def run(self):
        try:
            cover_art = self.sonic_client.getCoverArt(self.cover_art_id, size=200)
            if cover_art:
                pixmap = QPixmap()
                pixmap.loadFromData(cover_art)
                if not pixmap.isNull():
                    self.image_ready.emit(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"Error downloading cover art: {e}")

class PyperMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pyper - Modern Navidrome Music Player")
        self.setMinimumSize(CONFIG['ui']['window_width'], CONFIG['ui']['window_height'])
        
        # Initialize Navidrome connection
        self.sonic_client = None
        self.library_data = {}
        self.current_queue = []
        self.current_playing_index = -1
        self.current_artwork_pixmap = None
        self.search_results = {}  # Store search results
        
        # Initialize now playing dialog (keep for backward compatibility)
        self.now_playing_dialog = NowPlayingDialog(self)
        
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
        
        # Connect to Navidrome
        self.connect_to_navidrome()
        
    def setup_ui(self):
        """Setup the main user interface"""
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
        player_widget.setMinimumHeight(100)
        player_widget.setMaximumHeight(120)
        player_layout = QHBoxLayout(player_widget)
        
        # Album artwork (properly sized)
        self.artwork_label = QLabel()
        self.artwork_label.setFixedSize(80, 80)
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
        self.category_list.addItems(["Artists", "Albums", "Playlists"])
        self.category_list.setMaximumWidth(120)
        self.category_list.itemClicked.connect(self.category_selected)
        
        # Items list
        self.items_list = QListWidget()
        self.items_list.itemClicked.connect(self.item_selected)
        self.items_list.itemDoubleClicked.connect(self.items_double_clicked)
        self.items_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.items_list.customContextMenuRequested.connect(self.show_items_context_menu)
        
        # Sub-items list
        self.subitems_list = QListWidget()
        self.subitems_list.itemClicked.connect(self.subitem_selected)
        self.subitems_list.itemDoubleClicked.connect(self.subitem_double_clicked)
        self.subitems_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.subitems_list.customContextMenuRequested.connect(self.show_subitems_context_menu)
        
        # Songs list
        self.songs_list = QListWidget()
        self.songs_list.itemDoubleClicked.connect(self.song_double_clicked)
        self.songs_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.songs_list.customContextMenuRequested.connect(self.show_songs_context_menu)
        
        browse_layout.addWidget(self.category_list)
        browse_layout.addWidget(self.items_list)
        browse_layout.addWidget(self.subitems_list)
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
        
        # Add tabs
        self.tab_widget.addTab(browse_tab, "Browse")
        self.tab_widget.addTab(search_tab, "Search")
        self.tab_widget.addTab(queue_tab, "Queue")
        
        browser_layout.addWidget(self.tab_widget)
        content_splitter.addWidget(browser_widget)
        
        # Set splitter proportions (player at top, browser at bottom)
        content_splitter.setSizes([150, 500])
        
    def setup_connections(self):
        """Setup signal connections"""
        pass
        
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
            print(f"Connection error details: {e}")
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
        self.songs_list.clear()
        self.clear_search_results()
    
    def refresh_error(self, error_message):
        """Handle library refresh error"""
        self.refresh_button.setEnabled(True)
        self.status_label.setText("Refresh failed")
        QMessageBox.warning(self, "Refresh Error", error_message)
    
    def category_selected(self, item):
        """Handle category selection (Artists, Albums, Playlists)"""
        category = item.text()
        self.items_list.clear()
        self.subitems_list.clear()
        self.songs_list.clear()
        
        if category == "Artists":
            for artist_group in self.library_data.get('artists', []):
                for artist in artist_group.get('artist', []):
                    list_item = QListWidgetItem(artist['name'])
                    list_item.setData(Qt.ItemDataRole.UserRole, artist)
                    self.items_list.addItem(list_item)
        elif category == "Albums":
            for album in self.library_data.get('albums', []):
                album_title = f"{album['name']} - {album.get('artist', 'Unknown Artist')}"
                list_item = QListWidgetItem(album_title)
                list_item.setData(Qt.ItemDataRole.UserRole, album)
                self.items_list.addItem(list_item)
        elif category == "Playlists":
            for playlist in self.library_data.get('playlists', []):
                list_item = QListWidgetItem(playlist['name'])
                list_item.setData(Qt.ItemDataRole.UserRole, playlist)
                self.items_list.addItem(list_item)
    
    def item_selected(self, item):
        """Handle item selection in the second pane"""
        self.subitems_list.clear()
        self.songs_list.clear()
        data = item.data(Qt.ItemDataRole.UserRole)
        
        if not data:
            return
            
        # Determine what type of item was selected
        if 'albumCount' in data:  # It's an artist, show albums in pane 3
            try:
                artist_albums = self.sonic_client.getArtist(data['id'])
                albums = artist_albums.get('subsonic-response', {}).get('artist', {}).get('album', [])
                for album in albums:
                    album_title = f"{album['name']} ({album.get('year', 'Unknown Year')})"
                    list_item = QListWidgetItem(album_title)
                    list_item.setData(Qt.ItemDataRole.UserRole, album)
                    self.subitems_list.addItem(list_item)
            except Exception as e:
                print(f"Error fetching artist albums: {e}")
                
        elif 'artist' in data and 'name' in data and 'songCount' in data:  # It's an album, show songs directly in pane 4
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
            except Exception as e:
                print(f"Error fetching album songs: {e}")
                
        elif 'public' in data:  # It's a playlist, show songs directly in pane 4
            try:
                playlist_songs = self.sonic_client.getPlaylist(data['id'])
                for song in playlist_songs.get('subsonic-response', {}).get('playlist', {}).get('entry', []):
                    song_title = f"{song['title']} - {song.get('artist', 'Unknown Artist')}"
                    if 'duration' in song:
                        duration = self.format_duration(song['duration'])
                        song_title += f" ({duration})"
                    list_item = QListWidgetItem(song_title)
                    list_item.setData(Qt.ItemDataRole.UserRole, song)
                    self.songs_list.addItem(list_item)
            except Exception as e:
                print(f"Error fetching playlist songs: {e}")
    
    def artwork_clicked(self, event):
        """Handle clicks on album artwork"""
        # Could show a simple now playing dialog or do nothing
        self.show_now_playing()
    
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
            print(f"Search error: {e}")
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
        
        menu = QMenu(self)
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_search_artist_to_queue(item))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.search_artist_double_clicked(item))
        
        menu.exec(self.search_artists_list.mapToGlobal(position))
    
    def show_search_albums_context_menu(self, position):
        """Show context menu for search albums"""
        item = self.search_albums_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_search_album_to_queue(item))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.search_album_double_clicked(item))
        
        menu.exec(self.search_albums_list.mapToGlobal(position))
    
    def show_search_songs_context_menu(self, position):
        """Show context menu for search songs"""
        item = self.search_songs_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_search_song_to_queue(item))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.search_song_double_clicked(item))
        
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
            except Exception as e:
                print(f"Error fetching album songs: {e}")
    
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
            
        menu = QMenu(self)
        
        # Delete single item
        delete_action = menu.addAction("Remove from Queue")
        delete_action.triggered.connect(lambda: self.remove_queue_item(self.queue_list.row(item)))
        
        # Play this item
        play_action = menu.addAction("Play Now")
        play_action.triggered.connect(lambda: self.play_track(self.queue_list.row(item)))
        
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
                print(f"Error playing track: {e}")
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
            # Navidrome handles scrobbling automatically when we stream
            self.sonic_client.scrobble(song_id)
        except Exception as e:
            print(f"Scrobbling error: {e}")
    
    @staticmethod
    def format_duration(seconds):
        """Format duration in seconds to MM:SS"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

def main():
    app = QApplication(sys.argv)
    
    # Apply a modern, clean theme
    apply_stylesheet(app, theme=CONFIG['ui']['theme'])
    
    # Create and show the main window
    window = PyperMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 