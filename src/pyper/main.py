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
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QSplitter,
    QMessageBox, QScrollArea, QMenu, QDialog, QTextEdit, QLineEdit, 
    QTabWidget, QProgressBar, QMenuBar
)
from PyQt6.QtGui import QAction, QActionGroup, QIcon, QPainter
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

import requests
from qt_material import apply_stylesheet

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
CONTEXTUAL_PANEL_HEIGHT = 120
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

class ThemeManager:
    """Manages application themes and styling"""
    
    def __init__(self):
        self.themes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'themes')
        self.current_theme = None
        self.available_themes = self.load_available_themes()
        
    def load_available_themes(self):
        """Load all available theme definitions"""
        themes = {}
        
        # Add qt-material themes
        qt_themes = {
            'dark_teal': {'name': 'Dark Teal (qt-material)', 'qt_theme': 'dark_teal.xml'},
            'dark_purple': {'name': 'Dark Purple (qt-material)', 'qt_theme': 'dark_purple.xml'},
            'dark_amber': {'name': 'Dark Amber (qt-material)', 'qt_theme': 'dark_amber.xml'},
            'dark_blue': {'name': 'Dark Blue (qt-material)', 'qt_theme': 'dark_blue.xml'},
            'light_teal': {'name': 'Light Teal (qt-material)', 'qt_theme': 'light_teal.xml'},
            'light_blue': {'name': 'Light Blue (qt-material)', 'qt_theme': 'light_blue.xml'}
        }
        themes.update(qt_themes)
        
        # Load custom themes from JSON files
        if os.path.exists(self.themes_dir):
            for filename in os.listdir(self.themes_dir):
                if filename.endswith('.json'):
                    theme_id = filename[:-5]  # Remove .json extension
                    try:
                        with open(os.path.join(self.themes_dir, filename), 'r') as f:
                            theme_data = json.load(f)
                            themes[theme_id] = theme_data
                    except Exception as e:
                        logger.error(f"Failed to load theme {filename}: {e}")
        
        return themes
    
    def get_theme_list(self):
        """Get list of theme names for menu"""
        return [(theme_id, theme_data.get('name', theme_id)) for theme_id, theme_data in self.available_themes.items()]
    
    def apply_theme(self, app, theme_id):
        """Apply a theme to the application"""
        if theme_id not in self.available_themes:
            logger.error(f"Theme {theme_id} not found")
            return False
            
        theme_data = self.available_themes[theme_id]
        
        try:
            # Check if it's a qt-material theme
            if 'qt_theme' in theme_data:
                apply_stylesheet(app, theme=theme_data['qt_theme'])
                logger.info(f"Applied qt-material theme: {theme_data['name']}")
            else:
                # Apply custom theme
                self.apply_custom_theme(app, theme_data)
                logger.info(f"Applied custom theme: {theme_data['name']}")
            
            self.current_theme = theme_id
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply theme {theme_id}: {e}")
            return False
    
    def get_contrasting_text_color(self, background_color):
        """Get a contrasting text color (black or white) based on background color"""
        # Remove # if present
        bg_color = background_color.lstrip('#')
        
        # Convert to RGB
        try:
            r = int(bg_color[0:2], 16)
            g = int(bg_color[2:4], 16)
            b = int(bg_color[4:6], 16)
            
            # Calculate luminance using the relative luminance formula
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            
            # Return black text for light backgrounds, white text for dark backgrounds
            return '#000000' if luminance > 0.5 else '#FFFFFF'
        except:
            # Fallback to white if color parsing fails
            return '#FFFFFF'
    
    def apply_custom_theme(self, app, theme_data):
        """Apply a custom theme with CSS styling"""
        colors = theme_data.get('colors', {})
        
        # Create comprehensive stylesheet
        stylesheet = f"""
        QMainWindow {{
            background-color: {colors.get('background', '#212121')};
            color: {colors.get('text', '#FFFFFF')};
        }}
        
        QWidget {{
            background-color: {colors.get('background', '#212121')};
            color: {colors.get('text', '#FFFFFF')};
        }}
        
        QPushButton {{
            background-color: {colors.get('surface', '#424242')};
            color: {colors.get('text', '#FFFFFF')};
            border: 1px solid {colors.get('border', '#757575')};
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
            min-width: 60px;
            min-height: 30px;
        }}
        
        QPushButton:hover {{
            background-color: {colors.get('hover', '#616161')};
            border: 1px solid {colors.get('primary', '#009688')};
        }}
        
        QPushButton:pressed {{
            background-color: {colors.get('pressed', '#757575')};
        }}
        
        QListWidget {{
            background-color: {colors.get('surface', '#424242')};
            color: {colors.get('text', '#FFFFFF')};
            border: 1px solid {colors.get('border', '#757575')};
            selection-background-color: {colors.get('primary', '#009688')};
        }}
        
        QListWidget::item {{
            padding: 5px;
            border: none;
        }}
        
        QListWidget::item:selected {{
            background-color: {colors.get('primary', '#009688')};
            color: {self.get_contrasting_text_color(colors.get('primary', '#009688'))};
        }}
        
        QListWidget::item:hover {{
            background-color: {colors.get('hover', '#616161')};
        }}
        
        QTabWidget::pane {{
            border: 1px solid {colors.get('border', '#757575')};
            background-color: {colors.get('surface', '#424242')};
        }}
        
        QTabBar::tab {{
            background-color: {colors.get('surface_light', '#616161')};
            color: {colors.get('text_secondary', '#BDBDBD')};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors.get('primary', '#009688')};
            color: {self.get_contrasting_text_color(colors.get('primary', '#009688'))};
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors.get('hover', '#616161')};
        }}
        
        QLineEdit {{
            background-color: {colors.get('surface', '#424242')};
            color: {colors.get('text', '#FFFFFF')};
            border: 1px solid {colors.get('border', '#757575')};
            border-radius: 4px;
            padding: 5px;
        }}
        
        QLineEdit:focus {{
            border: 2px solid {colors.get('primary', '#009688')};
        }}
        
        QLabel {{
            color: {colors.get('text', '#FFFFFF')};
        }}
        
        QProgressBar {{
            background-color: {colors.get('surface', '#424242')};
            border: 1px solid {colors.get('border', '#757575')};
            border-radius: 5px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {colors.get('primary', '#009688')};
            border-radius: 4px;
        }}
        
        QScrollArea {{
            background-color: {colors.get('surface', '#424242')};
            border: 1px solid {colors.get('border', '#757575')};
        }}
        
        QMenu {{
            background-color: {colors.get('surface', '#424242')};
            color: {colors.get('text', '#FFFFFF')};
            border: 1px solid {colors.get('border', '#757575')};
        }}
        
        QMenu::item {{
            padding: 5px 20px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors.get('primary', '#009688')};
            color: {self.get_contrasting_text_color(colors.get('primary', '#009688'))};
        }}
        
        QMenuBar {{
            background-color: {colors.get('surface', '#424242')};
            color: {colors.get('text', '#FFFFFF')};
            border-bottom: 1px solid {colors.get('border', '#757575')};
        }}
        
        QMenuBar::item {{
            padding: 5px 10px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors.get('primary', '#009688')};
            color: {self.get_contrasting_text_color(colors.get('primary', '#009688'))};
        }}
        """
        
        app.setStyleSheet(stylesheet)
    
    def save_theme_preference(self, theme_id):
        """Save theme preference to config"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'config.json')
            
            # Read current config
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update theme
            if 'ui' not in config:
                config['ui'] = {}
            config['ui']['theme'] = theme_id
            
            # Write back to file
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            logger.info(f"Saved theme preference: {theme_id}")
            
        except Exception as e:
            logger.error(f"Failed to save theme preference: {e}")

class NavidromeDBHelper:
    """Helper class to access Navidrome's SQLite database for play counts and stats"""
    
    def __init__(self, db_path=None, ssh_config=None):
        self.db_path = db_path
        self.ssh_config = ssh_config
        self.temp_db_path = None
        
        if not db_path:
            # Try common Navidrome database locations
            self.db_path = self.find_navidrome_db()
    
    def find_navidrome_db(self):
        """Try to find the Navidrome database file"""
        common_paths = [
            "/var/lib/navidrome/navidrome.db",
            "/opt/navidrome/navidrome.db", 
            "/home/navidrome/navidrome.db",
            "~/navidrome/navidrome.db",
            "./navidrome.db"
        ]
        
        for path in common_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                return expanded_path
        return None
    
    def get_connection(self):
        """Get database connection if available"""
        db_to_use = self.db_path
        
        # If SSH config is provided, copy database from remote server
        if self.ssh_config and self.ssh_config.get('ssh_host'):
            db_to_use = self.get_remote_database()
            if not db_to_use:
                return None
        
        if not db_to_use or not os.path.exists(db_to_use):
            return None
        try:
            return sqlite3.connect(db_to_use, timeout=5.0)
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def get_remote_database(self):
        """Copy database from remote server via SSH"""
        if not self.ssh_config:
            return None
            
        try:
            # Create temporary file for the database copy
            if not self.temp_db_path:
                temp_dir = tempfile.mkdtemp()
                self.temp_db_path = os.path.join(temp_dir, 'navidrome_remote.db')
            
            ssh_host = self.ssh_config.get('ssh_host')
            ssh_user = self.ssh_config.get('ssh_user', 'root')
            ssh_key = self.ssh_config.get('ssh_key_path')
            remote_path = self.db_path
            
            # Build SCP command
            scp_cmd = ['scp']
            if ssh_key:
                expanded_key = os.path.expanduser(ssh_key)
                if os.path.exists(expanded_key):
                    scp_cmd.extend(['-i', expanded_key])
            
            # Add SSH options for non-interactive use
            scp_cmd.extend([
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=10',
                '-o', 'BatchMode=yes'
            ])
            
            remote_source = f"{ssh_user}@{ssh_host}:{remote_path}"
            scp_cmd.extend([remote_source, self.temp_db_path])
            
            logger.info(f"Copying database from {remote_source}...")
            
            # Execute SCP command
            result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"Database copied successfully to {self.temp_db_path}")
                return self.temp_db_path
            else:
                logger.error(f"SCP failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Database copy timed out")
            return None
        except Exception as e:
            logger.error(f"Error copying remote database: {e}")
            return None
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_db_path and os.path.exists(self.temp_db_path):
            try:
                temp_dir = os.path.dirname(self.temp_db_path)
                shutil.rmtree(temp_dir)
                logger.info("Cleaned up temporary database files")
            except Exception as e:
                logger.error(f"Error cleaning up temp files: {e}")
    
    def get_album_play_counts(self):
        """Get play counts for albums"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            # Get play counts by album from annotation table
            cursor.execute("""
                SELECT 
                    a.id,
                    a.name,
                    a.album_artist,
                    COALESCE(an.play_count, 0) as play_count,
                    an.play_date as last_played
                FROM album a
                LEFT JOIN annotation an ON a.id = an.item_id AND an.item_type = 'album'
                WHERE an.play_count > 0 OR an.play_count IS NULL
                ORDER BY play_count DESC
            """)
            
            results = {}
            for row in cursor.fetchall():
                album_id, name, artist, play_count, last_played = row
                if play_count is None:
                    play_count = 0
                results[album_id] = {
                    'name': name,
                    'artist': artist,
                    'play_count': play_count,
                    'last_played': last_played
                }
            
            conn.close()
            return results
        except Exception as e:
            print(f"Database query error: {e}")
            conn.close()
            return {}
    
    def get_most_played_albums(self, limit=50):
        """Get most played albums"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    a.id,
                    a.name,
                    a.album_artist,
                    a.id as cover_art_id,
                    a.max_year,
                    an.play_count
                FROM album a
                JOIN annotation an ON a.id = an.item_id AND an.item_type = 'album'
                WHERE an.play_count > 0
                ORDER BY an.play_count DESC, an.play_date DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                album_id, name, artist, cover_art_id, year, play_count = row
                results.append({
                    'id': album_id,
                    'name': name,
                    'artist': artist,
                    'coverArt': cover_art_id,
                    'year': year,
                    'playCount': play_count,
                    'songCount': 0  # Will be filled when needed
                })
            
            conn.close()
            return results
        except Exception as e:
            print(f"Database query error: {e}")
            conn.close()
            return []
    
    def get_recently_played_albums(self, limit=50):
        """Get recently played albums"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    a.id,
                    a.name,
                    a.album_artist,
                    a.id as cover_art_id,
                    a.max_year,
                    an.play_date as last_played,
                    an.play_count
                FROM album a
                JOIN annotation an ON a.id = an.item_id AND an.item_type = 'album'
                WHERE an.play_date IS NOT NULL
                ORDER BY an.play_date DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                album_id, name, artist, cover_art_id, year, last_played, play_count = row
                results.append({
                    'id': album_id,
                    'name': name,
                    'artist': artist,
                    'coverArt': cover_art_id,
                    'year': year,
                    'lastPlayed': last_played,
                    'playCount': play_count,
                    'songCount': 0  # Will be filled when needed
                })
            
            conn.close()
            return results
        except Exception as e:
            print(f"Database query error: {e}")
            conn.close()
            return []

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
    
    def search3(self, query, artist_count=None, album_count=None, song_count=None):
        """Search for artists, albums, and songs"""
        # Use default limits if not specified
        artist_count = artist_count or DEFAULT_SEARCH_LIMITS['artists']
        album_count = album_count or DEFAULT_SEARCH_LIMITS['albums']
        song_count = song_count or DEFAULT_SEARCH_LIMITS['songs']
        
        params = {
            'query': query,
            'artistCount': artist_count,
            'albumCount': album_count,
            'songCount': song_count
        }
        return self._make_request('search3', params)
    
    def getTopSongs(self, artist=None, count=50):
        """Get top songs (if supported by server)"""
        params = {'count': count}
        if artist:
            params['artist'] = artist
        try:
            return self._make_request('getTopSongs', params)
        except:
            return None
    
    def getAlbumList2_byFrequent(self, size=50):
        """Get albums ordered by play frequency"""
        params = {
            'type': 'frequent',
            'size': size
        }
        try:
            return self._make_request('getAlbumList2', params)
        except:
            return None
    
    def getAlbumList2_byRecent(self, size=50):
        """Get recently played albums"""
        params = {
            'type': 'recent',
            'size': size
        }
        try:
            return self._make_request('getAlbumList2', params)
        except:
            return None
    
    def getGenres(self):
        """Get all genres"""
        try:
            return self._make_request('getGenres')
        except:
            return None
    
    def getAlbumList2_byGenre(self, genre, size=500):
        """Get albums by genre"""
        params = {
            'type': 'byGenre',
            'genre': genre,
            'size': size
        }
        try:
            return self._make_request('getAlbumList2', params)
        except:
            return None
    
    def getAlbumList2_byYear(self, from_year, to_year, size=500):
        """Get albums by year range"""
        params = {
            'type': 'byYear',
            'fromYear': from_year,
            'toYear': to_year,
            'size': size
        }
        try:
            return self._make_request('getAlbumList2', params)
        except:
            return None

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
            logger.error(f"Error downloading cover art: {e}")

class ContextualInfoPanel(QWidget):
    """Bottom panel showing contextual information about selected items"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Main content area with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMaximumHeight(CONTEXTUAL_PANEL_HEIGHT)
        self.scroll_area.setMinimumHeight(CONTEXTUAL_PANEL_HEIGHT)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Default message
        self.show_default_message()
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
        
        # Style the panel
        self.setStyleSheet("""
            ContextualInfoPanel {
                background-color: #2b2b2b;
                border-top: 1px solid #555;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
    
    def clear_content(self):
        """Clear all content from the panel"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def show_default_message(self):
        """Show default message when nothing is selected"""
        self.clear_content()
        label = QLabel("Select an artist, album, or other item to see contextual information here")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888; font-style: italic;")
        self.content_layout.addWidget(label)
    
    def show_artist_info(self, artist_data, albums_data=None, sonic_client=None):
        """Show artist information with albums"""
        self.clear_content()
        
        # Artist info section
        artist_section = QWidget()
        artist_layout = QVBoxLayout(artist_section)
        artist_layout.setContentsMargins(5, 5, 5, 5)
        
        # Artist name
        artist_name = QLabel(f"<b>{artist_data.get('name', 'Unknown Artist')}</b>")
        artist_name.setStyleSheet("font-size: 14px; color: white;")
        artist_layout.addWidget(artist_name)
        
        # Artist stats
        album_count = len(albums_data) if albums_data else artist_data.get('albumCount', 0)
        stats = QLabel(f"{album_count} albums")
        stats.setStyleSheet("color: #ccc; font-size: 12px;")
        artist_layout.addWidget(stats)
        
        artist_section.setStyleSheet("background-color: #333; border-radius: 5px; margin-right: 10px;")
        artist_section.setFixedWidth(200)
        self.content_layout.addWidget(artist_section)
        
        # Albums section
        if albums_data:
            for album in albums_data[:MAX_CONTEXTUAL_ALBUMS]:  # Show max albums
                album_widget = self.create_album_widget(album, sonic_client)
                self.content_layout.addWidget(album_widget)
        
        self.content_layout.addStretch()
    
    def show_album_info(self, album_data, sonic_client=None):
        """Show album information"""
        self.clear_content()
        
        # Create a horizontal layout for artwork and info side by side
        album_container = QWidget()
        album_container_layout = QHBoxLayout(album_container)
        album_container_layout.setContentsMargins(0, 0, 0, 0)
        album_container_layout.setSpacing(10)
        
        # Album artwork (if available)
        artwork_section = QWidget()
        artwork_section.setFixedSize(100, 100)
        artwork_section.setStyleSheet("background-color: #333; border: 1px solid #555; border-radius: 5px;")
        
        artwork_layout = QVBoxLayout(artwork_section)
        artwork_layout.setContentsMargins(0, 0, 0, 0)
        artwork_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        artwork_label = QLabel()
        artwork_label.setText("♪")
        artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        artwork_label.setStyleSheet("border: none; background: transparent; color: #888; font-size: 24px;")
        artwork_layout.addWidget(artwork_label)
        
        if album_data.get('coverArt') and sonic_client:
            artwork_label.setText("Loading...")
            artwork_label.setStyleSheet("border: none; background: transparent; color: #888; font-size: 12px;")
            
            # Load artwork in thread
            def load_artwork():
                try:
                    image_data = sonic_client.getCoverArt(album_data['coverArt'], size=100)
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                    
                    # Scale maintaining aspect ratio, with padding for the container
                    scaled_pixmap = pixmap.scaled(98, 98, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    artwork_label.setPixmap(scaled_pixmap)
                    artwork_label.setText("")
                except:
                    artwork_label.setText("No Art")
                    artwork_label.setStyleSheet("border: none; background: transparent; color: #888; font-size: 12px;")
            
            QTimer.singleShot(100, load_artwork)
        
        album_container_layout.addWidget(artwork_section)
        
        # Album info section - same height as artwork
        album_info_section = QWidget()
        album_info_section.setFixedHeight(100)
        album_info_section.setStyleSheet("background-color: #333; border-radius: 5px; padding: 5px;")
        
        album_layout = QVBoxLayout(album_info_section)
        album_layout.setContentsMargins(10, 10, 10, 10)
        album_layout.setSpacing(5)
        
        # Album title
        title = QLabel(f"<b>{album_data.get('name', 'Unknown Album')}</b>")
        title.setStyleSheet("font-size: 16px; color: white;")
        title.setWordWrap(True)
        album_layout.addWidget(title)
        
        # Artist
        artist = QLabel(f"by {album_data.get('artist', 'Unknown Artist')}")
        artist.setStyleSheet("color: #ccc; font-size: 14px;")
        artist.setWordWrap(True)
        album_layout.addWidget(artist)
        
        # Year and track count
        year = album_data.get('year', '')
        song_count = album_data.get('songCount', 0)
        details = []
        if year:
            details.append(str(year))
        if song_count:
            details.append(f"{song_count} tracks")
        
        if details:
            details_label = QLabel(" • ".join(details))
            details_label.setStyleSheet("color: #aaa; font-size: 12px;")
            album_layout.addWidget(details_label)
        
        # Add stretch to push content to top
        album_layout.addStretch()
        
        album_container_layout.addWidget(album_info_section)
        album_container_layout.addStretch()  # Push everything to the left
        
        self.content_layout.addWidget(album_container)
        self.content_layout.addStretch()
    
    def create_album_widget(self, album_data, sonic_client=None):
        """Create a small album widget for the contextual panel"""
        widget = QWidget()
        widget.setFixedSize(80, 100)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Album artwork
        artwork_label = QLabel()
        artwork_label.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        artwork_label.setStyleSheet("border: 1px solid #555; background-color: #444;")
        artwork_label.setText("♪")
        artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        
        # Load artwork if available
        if album_data.get('coverArt') and sonic_client:
            def load_artwork():
                try:
                    image_data = sonic_client.getCoverArt(album_data['coverArt'], size=THUMBNAIL_SIZE)
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                    
                    # Scale maintaining aspect ratio, but leave some padding for border
                    scaled_pixmap = pixmap.scaled(THUMBNAIL_SIZE-2, THUMBNAIL_SIZE-2, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    artwork_label.setPixmap(scaled_pixmap)
                    artwork_label.setText("")
                except:
                    pass
            
            QTimer.singleShot(100, load_artwork)
        
        layout.addWidget(artwork_label)
        
        # Album name (truncated)
        name = album_data.get('name', 'Unknown')
        if len(name) > 12:
            name = name[:12] + "..."
        name_label = QLabel(name)
        name_label.setStyleSheet("color: white; font-size: 10px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        widget.setStyleSheet("background-color: #333; border-radius: 3px; margin: 2px;")
        return widget
    
    def show_genre_info(self, genre_name, albums_data=None):
        """Show genre information with albums"""
        self.clear_content()
        
        # Genre info section
        genre_section = QWidget()
        genre_layout = QVBoxLayout(genre_section)
        genre_layout.setContentsMargins(5, 5, 5, 5)
        
        # Genre name
        genre_title = QLabel(f"<b>Genre: {genre_name}</b>")
        genre_title.setStyleSheet("font-size: 14px; color: white;")
        genre_layout.addWidget(genre_title)
        
        # Genre stats
        album_count = len(albums_data) if albums_data else 0
        stats = QLabel(f"{album_count} albums")
        stats.setStyleSheet("color: #ccc; font-size: 12px;")
        genre_layout.addWidget(stats)
        
        genre_section.setStyleSheet("background-color: #333; border-radius: 5px; margin-right: 10px;")
        genre_section.setFixedWidth(200)
        self.content_layout.addWidget(genre_section)
        
        # Albums section
        if albums_data:
            for album in albums_data[:MAX_CONTEXTUAL_ALBUMS]:  # Show max albums
                album_widget = self.create_album_widget(album, None)  # No sonic_client for genre view
                self.content_layout.addWidget(album_widget)
        
        self.content_layout.addStretch()
    
    def show_decade_info(self, decade_name, albums_data=None):
        """Show decade information with albums"""
        self.clear_content()
        
        # Decade info section
        decade_section = QWidget()
        decade_layout = QVBoxLayout(decade_section)
        decade_layout.setContentsMargins(5, 5, 5, 5)
        
        # Decade name
        decade_title = QLabel(f"<b>{decade_name}</b>")
        decade_title.setStyleSheet("font-size: 14px; color: white;")
        decade_layout.addWidget(decade_title)
        
        # Decade stats
        album_count = len(albums_data) if albums_data else 0
        stats = QLabel(f"{album_count} albums")
        stats.setStyleSheet("color: #ccc; font-size: 12px;")
        decade_layout.addWidget(stats)
        
        decade_section.setStyleSheet("background-color: #333; border-radius: 5px; margin-right: 10px;")
        decade_section.setFixedWidth(200)
        self.content_layout.addWidget(decade_section)
        
        # Albums section
        if albums_data:
            for album in albums_data[:MAX_CONTEXTUAL_ALBUMS]:  # Show max albums
                album_widget = self.create_album_widget(album, None)  # No sonic_client for decade view
                self.content_layout.addWidget(album_widget)
        
        self.content_layout.addStretch()

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
        
        # Add tabs
        self.tab_widget.addTab(browse_tab, "Browse")
        self.tab_widget.addTab(search_tab, "Search")
        self.tab_widget.addTab(queue_tab, "Queue")
        self.tab_widget.addTab(most_played_tab, "Most Played")
        self.tab_widget.addTab(recently_played_tab, "Recently Played")
        
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
        self.songs_list.clear()
        self.clear_search_results()
        
        # Auto-expand artists on startup
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)  # Select "Artists"
            self.category_selected(self.category_list.item(0))
        
        # Load play count data and populate new tabs
        self.load_play_count_data()
    
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
        self.songs_list.clear()
        
        # Clear contextual panel when changing categories
        if self.contextual_panel:
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
                    # Add play count if available
                    if album['id'] in self.play_counts:
                        play_count = self.play_counts[album['id']]['play_count']
                        if play_count > 0:
                            album_title += f" • {play_count} plays"
                    list_item = QListWidgetItem(album_title)
                    list_item.setData(Qt.ItemDataRole.UserRole, album)
                    self.subitems_list.addItem(list_item)
                
                # Show artist info in contextual panel
                if self.contextual_panel:
                    self.contextual_panel.show_artist_info(data, albums, self.sonic_client)
                    
            except Exception as e:
                logger.error(f"Error fetching artist albums: {e}")
                
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
                
                # Show album info in contextual panel
                if self.contextual_panel:
                    self.contextual_panel.show_album_info(data, self.sonic_client)
                    
            except Exception as e:
                logger.error(f"Error fetching album songs: {e}")
                
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
                logger.error(f"Error fetching playlist songs: {e}")
                
        elif data.get('type') == 'genre':  # It's a genre, show albums in that genre
            try:
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
                    self.contextual_panel.show_genre_info(data['name'], albums)
                    
                self.status_label.setText(f"Loaded {len(albums)} albums for {data['name']}")
            except Exception as e:
                logger.error(f"Error fetching genre albums: {e}")
                self.status_label.setText("Error loading genre albums")
                
        elif data.get('type') == 'decade':  # It's a decade, show albums from that decade
            try:
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
                    self.contextual_panel.show_decade_info(data['name'], albums)
                    
                self.status_label.setText(f"Loaded {len(albums)} albums from {data['name']}")
            except Exception as e:
                logger.error(f"Error fetching decade albums: {e}")
                self.status_label.setText("Error loading decade albums")
    
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
        
        menu = QMenu(self)
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_album_songs_to_queue(item.data(Qt.ItemDataRole.UserRole)))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.most_played_double_clicked(item))
        
        menu.exec(self.most_played_list.mapToGlobal(position))
    
    def show_recently_played_context_menu(self, position):
        """Show context menu for recently played albums"""
        item = self.recently_played_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_album_songs_to_queue(item.data(Qt.ItemDataRole.UserRole)))
        
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.recently_played_double_clicked(item))
        
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
            logger.error(f"Scrobbling error: {e}")
    
    @staticmethod
    def format_duration(seconds):
        """Format duration in seconds to MM:SS"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

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
    except Exception as e:
        logger.error(f"Failed to apply initial theme: {e}")
        logger.info("Continuing with default theme")
    
    window.show()
    
    logger.info("Pyper application started successfully")
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 