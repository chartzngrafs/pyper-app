#!/usr/bin/env python3
"""
Desktop Integration Module for Pyper
Implements MPRIS2 D-Bus protocol for Linux desktop environment integration
"""

import logging
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap
import os
import tempfile
import hashlib
import threading

# Setup logging
logger = logging.getLogger(__name__)

# MPRIS2 constants
MPRIS2_INTERFACE = 'org.mpris.MediaPlayer2'
MPRIS2_PLAYER_INTERFACE = 'org.mpris.MediaPlayer2.Player'
MPRIS2_TRACKLIST_INTERFACE = 'org.mpris.MediaPlayer2.TrackList'
MPRIS2_PLAYLISTS_INTERFACE = 'org.mpris.MediaPlayer2.Playlists'

class MPRIS2Service(dbus.service.Object):
    """MPRIS2 D-Bus service implementation for Pyper"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.session_bus = dbus.SessionBus()
        
        # Request well-known name
        self.bus_name = dbus.service.BusName('org.mpris.MediaPlayer2.pyper', self.session_bus)
        
        # Initialize D-Bus object
        super().__init__(self.bus_name, '/org/mpris/MediaPlayer2')
        
        # Track metadata cache
        self.current_metadata = {}
        self.current_artwork_path = None
        
        logger.info("MPRIS2 service initialized")
    
    # Root Interface Properties
    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE, in_signature='ss', out_signature='v')
    def Get(self, interface_name, property_name):
        """Get property value"""
        return self.GetAll(interface_name)[property_name]
    
    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface_name):
        """Get all properties for an interface"""
        if interface_name == MPRIS2_INTERFACE:
            return {
                'CanQuit': True,
                'CanRaise': True,
                'HasTrackList': True,
                'Identity': 'Pyper',
                'DesktopEntry': 'pyper',
                'SupportedUriSchemes': dbus.Array(['http', 'https'], signature='s'),
                'SupportedMimeTypes': dbus.Array([
                    'audio/mpeg', 'audio/mp4', 'audio/flac', 'audio/ogg',
                    'audio/wav', 'audio/x-wav', 'audio/aac'
                ], signature='s')
            }
        elif interface_name == MPRIS2_PLAYER_INTERFACE:
            return {
                'PlaybackStatus': self.get_playback_status(),
                'LoopStatus': 'None',
                'Rate': 1.0,
                'Shuffle': False,
                'Metadata': dbus.Dictionary(self.get_current_metadata(), signature='sv'),
                'Volume': self.get_volume(),
                'Position': self.get_position(),
                'MinimumRate': 1.0,
                'MaximumRate': 1.0,
                'CanGoNext': self.can_go_next(),
                'CanGoPrevious': self.can_go_previous(),
                'CanPlay': True,
                'CanPause': True,
                'CanSeek': True,
                'CanControl': True
            }
        elif interface_name == MPRIS2_TRACKLIST_INTERFACE:
            return {
                'Tracks': dbus.Array(self.get_tracklist(), signature='o'),
                'CanEditTracks': False
            }
        return {}
    
    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE, in_signature='ssv')
    def Set(self, interface_name, property_name, new_value):
        """Set property value"""
        if interface_name == MPRIS2_PLAYER_INTERFACE:
            if property_name == 'Volume':
                self.set_volume(new_value)
            elif property_name == 'LoopStatus':
                # Could implement loop functionality here
                pass
            elif property_name == 'Shuffle':
                # Could implement shuffle functionality here
                pass
    
    # Root Interface Methods
    @dbus.service.method(dbus_interface=MPRIS2_INTERFACE)
    def Raise(self):
        """Bring the media player to the front"""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
    
    @dbus.service.method(dbus_interface=MPRIS2_INTERFACE)
    def Quit(self):
        """Quit the media player"""
        self.main_window.close()
    
    # Player Interface Methods
    @dbus.service.method(dbus_interface=MPRIS2_PLAYER_INTERFACE)
    def Next(self):
        """Skip to next track"""
        self.main_window.next_track()
    
    @dbus.service.method(dbus_interface=MPRIS2_PLAYER_INTERFACE)
    def Previous(self):
        """Skip to previous track"""
        self.main_window.previous_track()
    
    @dbus.service.method(dbus_interface=MPRIS2_PLAYER_INTERFACE)
    def Pause(self):
        """Pause playback"""
        if self.main_window.media_player.playbackState() == self.main_window.media_player.PlaybackState.PlayingState:
            self.main_window.play_pause()
    
    @dbus.service.method(dbus_interface=MPRIS2_PLAYER_INTERFACE)
    def PlayPause(self):
        """Toggle play/pause"""
        self.main_window.play_pause()
    
    @dbus.service.method(dbus_interface=MPRIS2_PLAYER_INTERFACE)
    def Stop(self):
        """Stop playback"""
        self.main_window.stop()
    
    @dbus.service.method(dbus_interface=MPRIS2_PLAYER_INTERFACE)
    def Play(self):
        """Start playback"""
        if self.main_window.media_player.playbackState() != self.main_window.media_player.PlaybackState.PlayingState:
            self.main_window.play_pause()
    
    @dbus.service.method(dbus_interface=MPRIS2_PLAYER_INTERFACE, in_signature='x')
    def Seek(self, offset):
        """Seek forward/backward by offset (microseconds)"""
        current_position = self.main_window.media_player.position() * 1000  # Convert to microseconds
        new_position = max(0, current_position + offset)
        self.main_window.media_player.setPosition(new_position // 1000)  # Convert back to milliseconds
    
    @dbus.service.method(dbus_interface=MPRIS2_PLAYER_INTERFACE, in_signature='ox')
    def SetPosition(self, track_id, position):
        """Set playback position (microseconds)"""
        # Convert microseconds to milliseconds
        position_ms = position // 1000
        self.main_window.media_player.setPosition(position_ms)
    
    @dbus.service.method(dbus_interface=MPRIS2_PLAYER_INTERFACE, in_signature='s')
    def OpenUri(self, uri):
        """Open URI for playback"""
        # Could implement URI opening functionality
        logger.info(f"OpenUri called with: {uri}")
    
    # TrackList Interface Methods
    @dbus.service.method(dbus_interface=MPRIS2_TRACKLIST_INTERFACE, out_signature='ao')
    def GetTracksMetadata(self, track_ids):
        """Get metadata for specified tracks"""
        # Return empty for now - could implement full tracklist metadata
        return dbus.Array([], signature='a{sv}')
    
    @dbus.service.method(dbus_interface=MPRIS2_TRACKLIST_INTERFACE, in_signature='sob', out_signature='ao')
    def AddTrack(self, uri, after_track, set_as_current):
        """Add track to tracklist"""
        # Could implement track addition
        pass
    
    @dbus.service.method(dbus_interface=MPRIS2_TRACKLIST_INTERFACE, in_signature='o')
    def RemoveTrack(self, track_id):
        """Remove track from tracklist"""
        # Could implement track removal
        pass
    
    @dbus.service.method(dbus_interface=MPRIS2_TRACKLIST_INTERFACE, in_signature='o')
    def GoTo(self, track_id):
        """Go to specified track"""
        # Could implement track navigation
        pass
    
    # Signals
    @dbus.service.signal(dbus_interface=MPRIS2_PLAYER_INTERFACE, signature='x')
    def Seeked(self, position):
        """Emitted when seek occurs"""
        pass
    
    # Helper methods for property values
    def get_playback_status(self):
        """Get current playback status"""
        state = self.main_window.media_player.playbackState()
        if state == self.main_window.media_player.PlaybackState.PlayingState:
            return 'Playing'
        elif state == self.main_window.media_player.PlaybackState.PausedState:
            return 'Paused'
        else:
            return 'Stopped'
    
    def get_current_metadata(self):
        """Get metadata for currently playing track"""
        if (self.main_window.current_playing_index >= 0 and 
            self.main_window.current_playing_index < len(self.main_window.current_queue)):
            
            song = self.main_window.current_queue[self.main_window.current_playing_index]
            
            # Create track ID
            track_id = f"/org/mpris/MediaPlayer2/Track/{song.get('id', '0')}"
            
            metadata = {
                'mpris:trackid': dbus.ObjectPath(track_id),
                'xesam:title': song.get('title', 'Unknown Title'),
                'xesam:artist': dbus.Array([song.get('artist', 'Unknown Artist')], signature='s'),
                'xesam:album': song.get('album', 'Unknown Album'),
                'xesam:albumArtist': dbus.Array([song.get('albumArtist', song.get('artist', 'Unknown Artist'))], signature='s'),
                'mpris:length': dbus.Int64((song.get('duration', 0)) * 1000000),  # Convert to microseconds
                'xesam:trackNumber': song.get('track', 0),
                'xesam:discNumber': song.get('discNumber', 1),
                'xesam:genre': dbus.Array([song.get('genre', '')], signature='s') if song.get('genre') else dbus.Array([], signature='s'),
                'xesam:url': f"navidrome://track/{song.get('id', '0')}"
            }
            
            # Add artwork URL if available
            if self.current_artwork_path and os.path.exists(self.current_artwork_path):
                metadata['mpris:artUrl'] = f"file://{self.current_artwork_path}"
            
            return metadata
        
        return {}
    
    def get_volume(self):
        """Get current volume (0.0 to 1.0)"""
        return self.main_window.audio_output.volume()
    
    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)"""
        self.main_window.audio_output.setVolume(float(volume))
    
    def get_position(self):
        """Get current playback position in microseconds"""
        return dbus.Int64(self.main_window.media_player.position() * 1000)
    
    def can_go_next(self):
        """Check if can go to next track"""
        return (self.main_window.current_playing_index < 
                len(self.main_window.current_queue) - 1)
    
    def can_go_previous(self):
        """Check if can go to previous track"""
        return self.main_window.current_playing_index > 0
    
    def get_tracklist(self):
        """Get list of track IDs in current queue"""
        track_ids = []
        for i, song in enumerate(self.main_window.current_queue):
            track_id = f"/org/mpris/MediaPlayer2/Track/{song.get('id', i)}"
            track_ids.append(dbus.ObjectPath(track_id))
        return track_ids
    
    def update_metadata(self, song_data, artwork_pixmap=None):
        """Update current track metadata and emit PropertiesChanged"""
        logger.info(f"Updating MPRIS2 metadata for: {song_data.get('title', 'Unknown')} - Artwork: {'Yes' if artwork_pixmap and not artwork_pixmap.isNull() else 'No'}")
        
        # Save artwork to temporary file for MPRIS2
        if artwork_pixmap and not artwork_pixmap.isNull():
            self.save_artwork_for_mpris(artwork_pixmap)
        else:
            logger.info("No artwork provided for MPRIS2 metadata update")
        
        # Get updated metadata (which includes artwork path if available)
        self.current_metadata = self.get_current_metadata()
        
        # Emit PropertiesChanged signal
        changed_properties = {
            'Metadata': dbus.Dictionary(self.current_metadata, signature='sv'),
            'PlaybackStatus': self.get_playback_status(),
            'Position': self.get_position(),
            'CanGoNext': self.can_go_next(),
            'CanGoPrevious': self.can_go_previous()
        }
        
        self.PropertiesChanged(MPRIS2_PLAYER_INTERFACE, changed_properties, [])
    
    def update_playback_status(self):
        """Update playback status and emit PropertiesChanged"""
        changed_properties = {
            'PlaybackStatus': self.get_playback_status(),
            'Position': self.get_position()
        }
        
        self.PropertiesChanged(MPRIS2_PLAYER_INTERFACE, changed_properties, [])
    
    def save_artwork_for_mpris(self, pixmap):
        """Save artwork to temporary file for MPRIS2 artUrl"""
        try:
            # Create temp file with unique name
            temp_dir = tempfile.gettempdir()
            artwork_filename = f"pyper_artwork_{hashlib.md5(str(id(pixmap)).encode()).hexdigest()[:8]}.png"
            artwork_path = os.path.join(temp_dir, artwork_filename)
            
            # Save pixmap to file
            if pixmap.save(artwork_path, 'PNG'):
                # Clean up old artwork file
                if self.current_artwork_path and os.path.exists(self.current_artwork_path):
                    try:
                        os.remove(self.current_artwork_path)
                    except:
                        pass
                
                self.current_artwork_path = artwork_path
                logger.info(f"Saved artwork for MPRIS2: {artwork_path}")
            else:
                logger.error(f"Failed to save pixmap to {artwork_path}")
            
        except Exception as e:
            logger.error(f"Failed to save artwork for MPRIS2: {e}")
    
    @dbus.service.signal(dbus_interface=dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface_name, changed_properties, invalidated_properties):
        """Emit PropertiesChanged signal"""
        pass
    
    def cleanup(self):
        """Clean up temporary files and D-Bus connection"""
        try:
            # Clean up artwork file
            if self.current_artwork_path and os.path.exists(self.current_artwork_path):
                os.remove(self.current_artwork_path)
                
            # Remove from D-Bus
            self.remove_from_connection()
            
        except Exception as e:
            logger.error(f"Error during MPRIS2 cleanup: {e}")


class DesktopIntegrationManager(QObject):
    """Manager for all desktop integration features"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.mpris2_service = None
        self.dbus_thread = None
        
        self.setup_mpris2()
        self.connect_signals()
        
    def setup_mpris2(self):
        """Initialize MPRIS2 service"""
        try:
            # Initialize D-Bus main loop
            DBusGMainLoop(set_as_default=True)
            
            # Start D-Bus service in a separate thread to avoid blocking Qt
            self.dbus_thread = threading.Thread(target=self._setup_dbus_service, daemon=True)
            self.dbus_thread.start()
            
            logger.info("MPRIS2 desktop integration enabled")
        except Exception as e:
            logger.error(f"Failed to initialize MPRIS2: {e}")
            self.mpris2_service = None
            
    def _setup_dbus_service(self):
        """Setup D-Bus service in separate thread"""
        try:
            import gi
            gi.require_version('GLib', '2.0')
            from gi.repository import GLib
            
            # Create the MPRIS2 service
            self.mpris2_service = MPRIS2Service(self.main_window)
            
            # Run GLib mainloop
            loop = GLib.MainLoop()
            loop.run()
            
        except Exception as e:
            logger.error(f"Error in D-Bus service thread: {e}")
    
    def connect_signals(self):
        """Connect main window signals to update MPRIS2"""
        # Connect to media player state changes
        self.main_window.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.main_window.media_player.positionChanged.connect(self.on_position_changed)
        
        # We'll need to connect to track changes - this will be done when tracks change
    
    def on_playback_state_changed(self, state):
        """Handle playback state changes"""
        if self.mpris2_service:
            self.mpris2_service.update_playback_status()
    
    def on_position_changed(self, position):
        """Handle position changes for seeking"""
        # Only emit Seeked signal for significant position jumps (seeking)
        # This prevents spam during normal playback
        pass
    
    def update_track_metadata(self, song_data, artwork_pixmap=None):
        """Update track metadata in MPRIS2"""
        if self.mpris2_service:
            self.mpris2_service.update_metadata(song_data, artwork_pixmap)
    
    def cleanup(self):
        """Clean up desktop integration"""
        if self.mpris2_service:
            self.mpris2_service.cleanup()
        
        # Note: The D-Bus thread is daemon, so it will be cleaned up automatically