"""
UI Components Module for Pyper Music Player
Contains custom UI widgets and dialogs
"""

import logging
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QScrollArea, QGridLayout, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QFont

# Get logger
logger = logging.getLogger('Pyper')

# Constants (these will be imported from main module)
CONTEXTUAL_PANEL_HEIGHT = 180
MAX_CONTEXTUAL_ALBUMS = 8


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
        
        # Import format_duration from main window class when needed
        try:
            from .main import PyperMainWindow
            duration_str = PyperMainWindow.format_duration(song.get('duration', 0))
        except ImportError:
            duration_str = str(song.get('duration', 0))
        
        info_html = f"""
        <b>Title:</b> {song.get('title', 'Unknown')}<br>
        <b>Artist:</b> {song.get('artist', 'Unknown')}<br>
        <b>Album:</b> {song.get('album', 'Unknown')}<br>
        <b>Year:</b> {song.get('year', 'Unknown')}<br>
        <b>Genre:</b> {song.get('genre', 'Unknown')}<br>
        <b>Duration:</b> {duration_str}
        """
        self.info_text.setHtml(info_html)


class MiniPlayerDialog(QDialog):
    """Compact mini player window for multitasking"""
    
    # Signals for communication with main window
    play_pause_clicked = pyqtSignal()
    previous_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    expand_clicked = pyqtSignal()
    progress_clicked = pyqtSignal(int)  # Position percentage
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_ui()
        self.apply_default_theme()
        
        # Removed always-on-top functionality - replaced with system tray icon
        
    def setup_ui(self):
        """Setup the mini player UI"""
        self.setWindowTitle("Pyper - Mini Player")
        self.setMinimumSize(350, 120)
        self.resize(350, 120)
        
        # Make window resizable and draggable
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)
        
        # Album artwork (compact size)
        self.artwork_label = QLabel()
        self.artwork_label.setFixedSize(80, 80)
        self.artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artwork_label.setScaledContents(True)
        self.artwork_label.setText("♪")
        self.artwork_label.setStyleSheet("""
            QLabel {
                border: 1px solid #666;
                background-color: #333;
                color: #fff;
                font-size: 18px;
                font-weight: bold;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.artwork_label)
        
        # Controls and info section
        controls_section = QWidget()
        controls_layout = QVBoxLayout(controls_section)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(4)
        
        # Track info
        self.track_info_label = QLabel("Not playing")
        self.track_info_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #fff;")
        self.track_info_label.setWordWrap(True)
        controls_layout.addWidget(self.track_info_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #666;
                border-radius: 3px;
                background-color: #444;
            }
            QProgressBar::chunk {
                background-color: #8b5cf6;
                border-radius: 3px;
            }
        """)
        # Enable progress bar clicking for time scrubbing
        self.progress_bar.mousePressEvent = self.progress_bar_clicked
        controls_layout.addWidget(self.progress_bar)
        
        # Control buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)
        
        # Playback buttons (compact)
        self.prev_button = QPushButton("⏮")
        self.play_pause_button = QPushButton("▶")
        self.stop_button = QPushButton("⏹")
        self.next_button = QPushButton("⏭")
        
        # Style buttons
        button_style = """
            QPushButton {
                font-size: 12px;
                min-width: 25px;
                max-width: 25px;
                min-height: 25px;
                max-height: 25px;
                border: 1px solid #666;
                border-radius: 3px;
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
        """
        
        for btn in [self.prev_button, self.play_pause_button, self.stop_button, self.next_button]:
            btn.setStyleSheet(button_style)
        
        # Connect button signals
        self.prev_button.clicked.connect(self.previous_clicked.emit)
        self.play_pause_button.clicked.connect(self.play_pause_clicked.emit)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        self.next_button.clicked.connect(self.next_clicked.emit)
        
        buttons_layout.addWidget(self.prev_button)
        buttons_layout.addWidget(self.play_pause_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.next_button)
        buttons_layout.addStretch()
        
        controls_layout.addLayout(buttons_layout)
        main_layout.addWidget(controls_section)
        
        # Right side buttons
        right_buttons_layout = QVBoxLayout()
        right_buttons_layout.setSpacing(4)
        
        # Expand to full window button (removed always-on-top in favor of tray icon)
        self.expand_button = QPushButton("⤢")
        self.expand_button.setToolTip("Expand to Full Player")
        self.expand_button.clicked.connect(self.expand_clicked.emit)
        self.expand_button.setStyleSheet(button_style)
        
        right_buttons_layout.addWidget(self.expand_button)
        right_buttons_layout.addStretch()
        
        main_layout.addLayout(right_buttons_layout)
        
    def apply_default_theme(self):
        """Apply default dark theme to mini player"""
        self.setStyleSheet("""
            MiniPlayerDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)
        
    def apply_theme_colors(self, theme_colors):
        """Apply theme colors to the mini player"""
        background = theme_colors.get('background', '#2b2b2b')
        text = theme_colors.get('text', '#ffffff')
        surface = theme_colors.get('surface', '#424242')
        border = theme_colors.get('border', '#666666')
        primary = theme_colors.get('primary', '#8b5cf6')
        hover = theme_colors.get('hover', '#555555')
        
        self.setStyleSheet(f"""
            MiniPlayerDialog {{
                background-color: {background};
                color: {text};
            }}
            QWidget {{
                background-color: {background};
                color: {text};
            }}
        """)
        
        # Update artwork label
        self.artwork_label.setStyleSheet(f"""
            QLabel {{
                border: 1px solid {border};
                background-color: {surface};
                color: {text};
                font-size: 18px;
                font-weight: bold;
                border-radius: 4px;
            }}
        """)
        
        # Update track info
        self.track_info_label.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {text};")
        
        # Update progress bar
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {border};
                border-radius: 3px;
                background-color: {surface};
            }}
            QProgressBar::chunk {{
                background-color: {primary};
                border-radius: 3px;
            }}
        """)
        
        # Update buttons
        button_style = f"""
            QPushButton {{
                font-size: 12px;
                min-width: 25px;
                max-width: 25px;
                min-height: 25px;
                max-height: 25px;
                border: 1px solid {border};
                border-radius: 3px;
                background-color: {surface};
                color: {text};
            }}
            QPushButton:hover {{
                background-color: {hover};
                border: 1px solid {primary};
            }}
            QPushButton:pressed {{
                background-color: {border};
            }}
        """
        
        for btn in [self.prev_button, self.play_pause_button, self.stop_button, self.next_button, self.expand_button]:
            btn.setStyleSheet(button_style)
        
    # Always-on-top functionality removed - replaced with system tray icon
        
    def progress_bar_clicked(self, event):
        """Handle progress bar click for time scrubbing"""
        if self.progress_bar.maximum() > 0:
            # Calculate percentage based on click position
            click_x = event.position().x()
            width = self.progress_bar.width()
            percentage = int((click_x / width) * 100)
            percentage = max(0, min(100, percentage))  # Clamp between 0-100
            self.progress_clicked.emit(percentage)
            
    def update_track_info(self, song_data):
        """Update the mini player with current track information"""
        if song_data:
            title = song_data.get('title', 'Unknown')
            artist = song_data.get('artist', 'Unknown Artist')
            self.track_info_label.setText(f"{title}\n{artist}")
        else:
            self.track_info_label.setText("Not playing")
            
    def update_artwork(self, pixmap):
        """Update the artwork display"""
        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.artwork_label.setPixmap(scaled_pixmap)
            self.artwork_label.setText("")
        else:
            self.artwork_label.clear()
            self.artwork_label.setText("♪")
            
    def update_play_button(self, is_playing):
        """Update play/pause button state"""
        if is_playing:
            self.play_pause_button.setText("⏸")
        else:
            self.play_pause_button.setText("▶")
            
    def update_progress(self, position, duration):
        """Update progress bar"""
        if duration > 0:
            percentage = int((position / duration) * 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setValue(0)
            
    def closeEvent(self, event):
        """Handle mini player close event"""
        # Check if main window is closing to avoid interference
        if (self.parent_window and 
            hasattr(self.parent_window, '_is_closing') and 
            self.parent_window._is_closing):
            event.accept()
            return
            
        # Check if application is quitting to avoid interference
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        
        # If application is quitting, don't interfere
        if app and app.closingDown():
            event.accept()
            return
            
        # Otherwise, show main window if it's hidden
        if (self.parent_window and 
            hasattr(self.parent_window, 'isVisible') and 
            not self.parent_window.isVisible()):
            try:
                self.parent_window.show()
                self.parent_window.raise_()
                self.parent_window.activateWindow()
            except:
                pass  # Ignore errors during close
        
        event.accept()


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
        artist_layout.setContentsMargins(15, 15, 15, 15)
        artist_layout.setSpacing(8)
        
        # Artist name - no height restrictions
        artist_name_text = artist_data.get('name', 'Unknown Artist')
        artist_name = QLabel(f"<b>{artist_name_text}</b>")
        artist_name.setStyleSheet("font-size: 18px; color: white; font-weight: bold; line-height: 1.3;")
        artist_name.setWordWrap(True)
        # No maximum height - let it expand as needed
        artist_layout.addWidget(artist_name)
        
        # Artist stats
        album_count = len(albums_data) if albums_data else artist_data.get('albumCount', 0)
        stats = QLabel(f"{album_count} albums")
        stats.setStyleSheet("color: #ccc; font-size: 14px;")
        artist_layout.addWidget(stats)
        
        # Add stretch to push content to top
        artist_layout.addStretch()
        
        artist_section.setStyleSheet("background-color: #333; border-radius: 5px; margin-right: 20px;")
        artist_section.setMinimumWidth(280)  # Wider to prevent text cutting
        artist_section.setMinimumHeight(160)  # Match the increased contextual panel height
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
        album_container_layout.setSpacing(20)
        
        # Album artwork (if available)
        artwork_section = QWidget()
        artwork_section.setFixedSize(150, 150)  # Larger artwork
        artwork_section.setStyleSheet("background-color: #333; border: 1px solid #555; border-radius: 5px;")
        
        artwork_layout = QVBoxLayout(artwork_section)
        artwork_layout.setContentsMargins(0, 0, 0, 0)
        artwork_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        artwork_label = QLabel()
        artwork_label.setText("♪")
        artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        artwork_label.setStyleSheet("border: none; background: transparent; color: #888; font-size: 32px;")
        artwork_layout.addWidget(artwork_label)
        
        if album_data.get('coverArt') and sonic_client:
            artwork_label.setText("Loading...")
            artwork_label.setStyleSheet("border: none; background: transparent; color: #888; font-size: 12px;")
            
            # Load artwork in thread
            def load_artwork():
                try:
                    image_data = sonic_client.getCoverArt(album_data['coverArt'], size=150)
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                    
                    # Scale maintaining aspect ratio, with padding for the container
                    scaled_pixmap = pixmap.scaled(148, 148, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    artwork_label.setPixmap(scaled_pixmap)
                    artwork_label.setText("")
                except:
                    artwork_label.setText("No Art")
                    artwork_label.setStyleSheet("border: none; background: transparent; color: #888; font-size: 12px;")
            
            QTimer.singleShot(100, load_artwork)
        
        album_container_layout.addWidget(artwork_section)
        
        # Album info section - flexible height and width, no text cutting!
        album_info_section = QWidget()
        album_info_section.setMinimumHeight(150)  # Match artwork height
        album_info_section.setMinimumWidth(450)   # Much wider to prevent text cutting
        album_info_section.setStyleSheet("background-color: #333; border-radius: 5px; padding: 5px;")
        
        album_layout = QVBoxLayout(album_info_section)
        album_layout.setContentsMargins(20, 20, 20, 20)
        album_layout.setSpacing(12)
        
        # Album title - no height restrictions, full word wrap
        title_text = album_data.get('name', 'Unknown Album')
        title = QLabel(f"<b>{title_text}</b>")
        title.setStyleSheet("font-size: 18px; color: white; font-weight: bold; line-height: 1.3;")
        title.setWordWrap(True)
        # No maximum height - let it expand as needed
        album_layout.addWidget(title)
        
        # Artist - no height restrictions
        artist_text = album_data.get('artist', 'Unknown Artist')
        artist = QLabel(f"by {artist_text}")
        artist.setStyleSheet("color: #ccc; font-size: 15px; line-height: 1.2;")
        artist.setWordWrap(True)
        album_layout.addWidget(artist)
        
        # Album stats
        year = album_data.get('year', 'Unknown')
        song_count = album_data.get('songCount', 'Unknown')
        duration_minutes = album_data.get('duration', 0) // 60 if album_data.get('duration') else 0
        
        stats_text = f"Year: {year}"
        if song_count != 'Unknown':
            stats_text += f" • {song_count} tracks"
        if duration_minutes > 0:
            stats_text += f" • {duration_minutes} minutes"
        
        stats = QLabel(stats_text)
        stats.setStyleSheet("color: #aaa; font-size: 13px; line-height: 1.2;")
        stats.setWordWrap(True)
        album_layout.addWidget(stats)
        
        # Genre (if available)
        if album_data.get('genre'):
            genre = QLabel(f"Genre: {album_data['genre']}")
            genre.setStyleSheet("color: #aaa; font-size: 13px; line-height: 1.2;")
            genre.setWordWrap(True)
            album_layout.addWidget(genre)
        
        # Add stretch to push content to top
        album_layout.addStretch()
        
        album_container_layout.addWidget(album_info_section)
        
        # Add the complete album container to the content layout
        self.content_layout.addWidget(album_container)
        self.content_layout.addStretch()
    
    def create_album_widget(self, album_data, sonic_client=None):
        """Create a compact album widget for the contextual panel"""
        widget = QWidget()
        widget.setMinimumWidth(160)  # Wider to prevent text cutting
        widget.setMinimumHeight(160)  # Match the increased contextual panel height
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Album artwork
        artwork_label = QLabel()
        artwork_label.setFixedSize(100, 100)  # Much larger thumbnail
        artwork_label.setStyleSheet("border: 1px solid #555; background-color: #444; border-radius: 4px;")
        artwork_label.setText("♪")
        artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        artwork_label.setStyleSheet(artwork_label.styleSheet() + "; font-size: 20px;")

        
        # Load artwork if available
        if album_data.get('coverArt') and sonic_client:
            def load_artwork():
                try:
                    image_data = sonic_client.getCoverArt(album_data['coverArt'], size=100)
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                    
                    # Scale maintaining aspect ratio, but leave some padding for border
                    scaled_pixmap = pixmap.scaled(98, 98, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    artwork_label.setPixmap(scaled_pixmap)
                    artwork_label.setText("")
                except:
                    pass
            
            QTimer.singleShot(100, load_artwork)
        
        layout.addWidget(artwork_label)
        
        # Album name - with proper wrapping and no truncation
        name = album_data.get('name', 'Unknown')
        name_label = QLabel(name)
        name_label.setStyleSheet("color: white; font-size: 11px; font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)  # Enable word wrapping
        name_label.setMaximumHeight(40)  # Allow for multiple lines
        layout.addWidget(name_label)
        
        widget.setStyleSheet("background-color: #333; border-radius: 4px; margin: 3px;")
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


class AlbumGridWidget(QWidget):
    """Custom widget for displaying albums in a 3-column grid with artwork"""
    album_selected = pyqtSignal(object)  # Emits album data when selected
    album_double_clicked = pyqtSignal(object)  # Emits album data when double-clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.albums = []
        self.selected_album = None
        self.sonic_client = None
        self.play_counts = {}
        self.active_threads = []  # Track active download threads
        
        # Apply the same styling as QListWidget to match other panes
        # Colors will be set dynamically when theme is applied
        self.theme_colors = None
        
        self.setup_ui()
    
    def __del__(self):
        """Cleanup when widget is destroyed"""
        self.cleanup_threads()
    
    def cleanup_threads(self):
        """Stop and cleanup all active download threads"""
        for thread in self.active_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait(1000)  # Wait up to 1 second
        self.active_threads.clear()
        
    def setup_ui(self):
        """Setup the grid layout"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Match other panes
        self.main_layout.setSpacing(0)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameStyle(0)  # Remove frame to match list widgets
        # Styling will be set when theme colors are available
        
        # Create widget to hold the grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins
        
        self.scroll_area.setWidget(self.grid_widget)
        
        # Viewport styling will be set when theme colors are available
        
        self.main_layout.addWidget(self.scroll_area)
        
    def clear(self):
        """Clear all albums from the grid"""
        # Stop any active download threads first
        self.cleanup_threads()
        
        self.albums = []
        self.selected_album = None
        
        # Clear grid layout
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def set_sonic_client(self, sonic_client):
        """Set the sonic client for artwork loading"""
        self.sonic_client = sonic_client
        
    def set_play_counts(self, play_counts):
        """Set play count data"""
        self.play_counts = play_counts
        
    def apply_theme_colors(self, theme_colors):
        """Apply theme colors to match other panes"""
        self.theme_colors = theme_colors
        
        surface_color = theme_colors.get('surface', '#2a2139')
        border_color = theme_colors.get('border', '#495495')
        
        # Apply styling to match QListWidget - no border since container handles it
        self.setStyleSheet(f"""
            AlbumGridWidget {{
                background-color: {surface_color};
                border: none;
            }}
        """)
        
        # Apply to scroll area
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {surface_color};
                border: none;
            }}
        """)
        
        # Apply to grid widget
        self.grid_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {surface_color};
            }}
        """)
        
        # Apply to viewport
        if self.scroll_area.viewport():
            self.scroll_area.viewport().setStyleSheet(f"background-color: {surface_color};")
        
    def populate_albums(self, albums):
        """Populate the grid with album data"""
        self.clear()
        self.albums = albums
        
        # Calculate responsive columns based on widget width
        self.update_grid_layout()
        
    def update_grid_layout(self):
        """Update grid layout with responsive columns"""
        if not self.albums:
            return
            
        # Calculate columns based on available width
        available_width = self.width() if self.width() > 0 else 800  # fallback width
        album_widget_width = 180 + 15  # widget width + spacing
        columns = max(1, min(3, available_width // album_widget_width))  # 1-3 columns
        
        # Clear existing layout
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().hide()  # Hide instead of delete to reuse
        
        # Re-add widgets with new column count
        for i, album in enumerate(self.albums):
            row = i // columns
            col = i % columns
            
            album_widget = self.create_album_widget(album)
            self.grid_layout.addWidget(album_widget, row, col)
            
        # Add stretch to push items to top
        self.grid_layout.setRowStretch(len(self.albums) // columns + 1, 1)
        
    def resizeEvent(self, event):
        """Handle resize events to update grid layout"""
        super().resizeEvent(event)
        if hasattr(self, 'albums') and self.albums:
            # Use QTimer to avoid too frequent updates during resize
            if not hasattr(self, '_resize_timer'):
                self._resize_timer = QTimer()
                self._resize_timer.timeout.connect(self.update_grid_layout)
                self._resize_timer.setSingleShot(True)
            self._resize_timer.start(100)  # 100ms delay
        
    def create_album_widget(self, album_data):
        """Create a widget for a single album"""
        widget = QWidget()
        widget.setFixedSize(180, 250)
        widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.3);
                border: 2px solid transparent;
                border-radius: 8px;
                padding: 8px;
            }
            QWidget:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Album artwork
        artwork_label = QLabel()
        artwork_label.setFixedSize(150, 150)
        artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        artwork_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        
        # Load artwork or show placeholder
        if album_data.get('coverArt') and self.sonic_client:
            self.load_album_artwork(artwork_label, album_data['coverArt'])
        else:
            artwork_label.setText("♪")
            artwork_label.setStyleSheet(artwork_label.styleSheet() + """
                font-size: 48px;
                color: rgba(255, 255, 255, 0.6);
            """)
        
        layout.addWidget(artwork_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Album name
        name_label = QLabel(album_data.get('name', 'Unknown Album'))
        name_label.setWordWrap(True)
        name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
                background: transparent;
                border: none;
                padding: 2px;
            }
        """)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Artist name
        artist_label = QLabel(album_data.get('artist', 'Unknown Artist'))
        artist_label.setWordWrap(True)
        artist_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 10px;
                text-align: center;
                background: transparent;
                border: none;
                padding: 1px;
            }
        """)
        artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(artist_label)
        
        # Store album data in widget for later access
        widget.album_data = album_data
        
        # Install event filter for mouse events
        widget.installEventFilter(self)
        
        return widget
    
    def load_album_artwork(self, label, cover_art_id):
        """Load album artwork asynchronously"""
        if self.sonic_client:
            try:
                # Try relative import first
                from .background_tasks import ImageDownloadThread
                thread = ImageDownloadThread(self.sonic_client, cover_art_id)
                thread.image_ready.connect(lambda pixmap: self.set_artwork(label, pixmap))
                thread.finished.connect(lambda: self.thread_finished(thread))
                self.active_threads.append(thread)
                thread.start()
            except ImportError:
                try:
                    # Fall back to absolute import
                    from background_tasks import ImageDownloadThread
                    thread = ImageDownloadThread(self.sonic_client, cover_art_id)
                    thread.image_ready.connect(lambda pixmap: self.set_artwork(label, pixmap))
                    thread.finished.connect(lambda: self.thread_finished(thread))
                    self.active_threads.append(thread)
                    thread.start()
                except ImportError:
                    # Fallback if background_tasks not available - load synchronously
                    try:
                        cover_art = self.sonic_client.getCoverArt(cover_art_id, size=150)
                        if cover_art:
                            pixmap = QPixmap()
                            pixmap.loadFromData(cover_art)
                            if not pixmap.isNull():
                                scaled_pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                self.set_artwork(label, scaled_pixmap)
                    except Exception as e:
                        logger.error(f"Error loading album artwork: {e}")
    
    def thread_finished(self, thread):
        """Remove finished thread from active list"""
        if thread in self.active_threads:
            self.active_threads.remove(thread)
    
    def set_artwork(self, label, pixmap):
        """Set artwork on label"""
        if not pixmap.isNull():
            label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            label.setText("")
    
    def eventFilter(self, obj, event):
        """Handle mouse events on album widgets"""
        if hasattr(obj, 'album_data'):
            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.select_album_widget(obj)
                    return True
                elif event.button() == Qt.MouseButton.RightButton:
                    self.show_context_menu(obj, event.globalPosition().toPoint())
                    return True
            elif event.type() == event.Type.MouseButtonDblClick:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.album_double_clicked.emit(obj.album_data)
                    return True
        
        return super().eventFilter(obj, event)
    
    def select_album_widget(self, widget):
        """Select an album widget"""
        # Clear previous selection
        if self.selected_album:
            self.selected_album.setStyleSheet("""
                QWidget {
                    background-color: rgba(0, 0, 0, 0.3);
                    border: 2px solid transparent;
                    border-radius: 8px;
                    padding: 8px;
                }
                QWidget:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }
            """)
        
        # Select new widget
        self.selected_album = widget
        widget.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.5);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # Emit selection signal
        self.album_selected.emit(widget.album_data)
    
    def show_context_menu(self, widget, global_pos):
        """Show context menu for album widget"""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        # Add to Queue action
        add_to_queue_action = menu.addAction("Add to Queue")
        add_to_queue_action.triggered.connect(lambda: self.add_album_to_queue(widget.album_data))
        
        # Play Now action
        play_now_action = menu.addAction("Play Now")
        play_now_action.triggered.connect(lambda: self.album_double_clicked.emit(widget.album_data))
        
        menu.addSeparator()
        
        # Go to Album action
        go_to_album_action = menu.addAction("Go to Album")
        go_to_album_action.triggered.connect(lambda: self.go_to_album(widget.album_data))
        
        # Go to Artist action
        go_to_artist_action = menu.addAction("Go to Artist")
        go_to_artist_action.triggered.connect(lambda: self.go_to_artist(widget.album_data))
        
        menu.exec(global_pos)
    
    def add_album_to_queue(self, album_data):
        """Signal to add album to queue"""
        if hasattr(self.parent(), 'add_album_songs_to_queue'):
            self.parent().add_album_songs_to_queue(album_data)
            
    def go_to_album(self, album_data):
        """Signal to navigate to album"""
        if hasattr(self.parent(), 'go_to_browse_item'):
            self.parent().go_to_browse_item(album_data, 'album')
            
    def go_to_artist(self, album_data):
        """Signal to navigate to artist"""
        if hasattr(self.parent(), 'go_to_browse_item'):
            artist_data = {'name': album_data.get('artist'), 'id': album_data.get('artistId')}
            self.parent().go_to_browse_item(artist_data, 'artist') 