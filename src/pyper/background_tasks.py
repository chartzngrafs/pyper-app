"""
Background Tasks Module for Pyper Music Player
Contains thread classes for asynchronous operations
"""

import os
import re
import json
import logging
import urllib.request
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont, QPainter
import requests

# Get logger
logger = logging.getLogger('Pyper')


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
            
            self.progress.emit("Fetching radio stations...")
            radio_stations = self.sonic_client.getInternetRadioStations()
            if radio_stations:
                library_data['radio_stations'] = radio_stations.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
            else:
                library_data['radio_stations'] = []
            
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


class ICYMetadataParser(QThread):
    """Thread for parsing ICY metadata from radio streams"""
    metadata_updated = pyqtSignal(dict)
    artwork_ready = pyqtSignal(QPixmap)
    
    def __init__(self, stream_url):
        super().__init__()
        self.stream_url = stream_url
        self.running = False
        self.current_track = {}
        
    def run(self):
        """Monitor ICY metadata from the stream"""
        self.running = True
        
        while self.running:
            try:
                self.fetch_icy_metadata()
                self.msleep(10000)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"ICY metadata error: {e}")
                self.msleep(5000)  # Wait 5 seconds before retry
    
    def stop(self):
        """Stop the metadata monitoring"""
        self.running = False
        
    def fetch_icy_metadata(self):
        """Fetch ICY metadata from the stream"""
        try:
            # Create request with ICY metadata headers
            req = urllib.request.Request(self.stream_url)
            req.add_header('Icy-MetaData', '1')
            req.add_header('User-Agent', 'Pyper/1.0')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                # Check if ICY metadata is supported
                icy_metaint = response.headers.get('icy-metaint')
                if not icy_metaint:
                    return
                    
                metaint = int(icy_metaint)
                
                # Read stream data up to metadata block
                stream_data = response.read(metaint)
                
                # Read metadata length
                meta_length_byte = response.read(1)
                if not meta_length_byte:
                    return
                    
                meta_length = ord(meta_length_byte) * 16
                
                if meta_length > 0:
                    # Read metadata
                    metadata_bytes = response.read(meta_length)
                    metadata_str = metadata_bytes.decode('utf-8', errors='ignore').strip('\x00')
                    
                    # Parse metadata
                    self.parse_metadata(metadata_str)
                    
        except Exception as e:
            logger.debug(f"ICY metadata fetch error: {e}")
    
    def parse_metadata(self, metadata_str):
        """Parse ICY metadata string"""
        if not metadata_str:
            return
            
        # Extract StreamTitle
        title_match = re.search(r"StreamTitle='([^']*)'", metadata_str)
        if not title_match:
            return
            
        stream_title = title_match.group(1)
        if not stream_title or stream_title == self.current_track.get('title', ''):
            return  # No change
            
        # Parse artist and title (common formats: "Artist - Title" or "Title")
        if ' - ' in stream_title:
            parts = stream_title.split(' - ', 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            artist = "Unknown Artist"
            title = stream_title.strip()
        
        # Update current track info
        track_info = {
            'title': title,
            'artist': artist,
            'raw_title': stream_title
        }
        
        # Only emit if track actually changed
        if track_info != self.current_track:
            self.current_track = track_info
            self.metadata_updated.emit(track_info)
            logger.info(f"ICY metadata: {artist} - {title}")
            
            # Try to fetch album art
            self.fetch_album_art(artist, title)
    
    def fetch_album_art(self, artist, title):
        """Fetch album art using multiple sources"""
        try:
            logger.info(f"=== Starting album art search for: {artist} - {title} ===")
            
            # Try multiple sources in order of preference
            artwork_url = None
            
            # 1. Try MusicBrainz + Cover Art Archive
            logger.info("Trying source 1: MusicBrainz + Cover Art Archive")
            artwork_url = self.search_musicbrainz_art(artist, title)
            
            # 2. Try Last.fm as fallback
            if not artwork_url:
                logger.info("Trying source 2: Last.fm API")
                artwork_url = self.search_lastfm_art(artist, title)
            else:
                logger.info("Skipping Last.fm - already found artwork from MusicBrainz")
            
            # 3. Try iTunes Search API as another fallback
            if not artwork_url:
                logger.info("Trying source 3: iTunes Search API")
                artwork_url = self.search_itunes_art(artist, title)
            else:
                logger.info("Skipping iTunes - already found artwork")
            
            if artwork_url:
                logger.info(f"SUCCESS: Found album art URL: {artwork_url}")
                self.download_artwork(artwork_url)
            else:
                logger.info(f"FAILURE: No album art found for: {artist} - {title}")
                logger.info("All sources exhausted, using default artwork")
                # Emit a default music icon instead of no artwork
                self.emit_default_radio_artwork()
            
            logger.info(f"=== Album art search complete for: {artist} - {title} ===")
                
        except Exception as e:
            logger.error(f"Album art fetch error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def search_musicbrainz_art(self, artist, title):
        """Search for album artwork using MusicBrainz + Cover Art Archive"""
        try:
            logger.info(f"Searching MusicBrainz for: {artist} - {title}")
            
            # Clean up artist and title for better search
            clean_artist = artist.replace('"', '').strip()
            clean_title = title.replace('"', '').strip()
            
            # Try different search strategies
            search_queries = [
                f'artist:"{clean_artist}" AND recording:"{clean_title}"',
                f'artist:{clean_artist} AND recording:{clean_title}',
                f'{clean_artist} {clean_title}'
            ]
            
            for i, query in enumerate(search_queries):
                try:
                    logger.info(f"MusicBrainz query {i+1}/3: {query}")
                    mb_url = "https://musicbrainz.org/ws/2/recording/"
                    params = {
                        'query': query,
                        'fmt': 'json',
                        'limit': 5
                    }
                    
                    headers = {
                        'User-Agent': 'Pyper/1.0 (Music Player; kevin@example.com)'
                    }
                    
                    response = requests.get(mb_url, params=params, headers=headers, timeout=10)
                    logger.info(f"MusicBrainz response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        recordings = data.get('recordings', [])
                        logger.info(f"Found {len(recordings)} recordings")
                        
                        if len(recordings) == 0:
                            logger.info("No recordings found for query")
                            continue
                        
                        for j, recording in enumerate(recordings):
                            logger.info(f"Checking recording {j+1}: {recording.get('title', 'Unknown')}")
                            releases = recording.get('releases', [])
                            logger.info(f"Recording has {len(releases)} releases")
                            
                            for k, release in enumerate(releases):
                                release_id = release.get('id')
                                release_title = release.get('title', 'Unknown')
                                logger.info(f"Checking release {k+1}: {release_title} (ID: {release_id})")
                                
                                if release_id:
                                    cover_url = f"https://coverartarchive.org/release/{release_id}/front-250"
                                    logger.info(f"Checking cover art: {cover_url}")
                                    
                                    try:
                                        cover_response = requests.head(cover_url, timeout=5, allow_redirects=True)
                                        logger.info(f"Cover art response: {cover_response.status_code}")
                                        if cover_response.status_code == 200:
                                            logger.info(f"Found MusicBrainz cover art: {cover_url}")
                                            return cover_url
                                        elif cover_response.status_code == 307:
                                            # Follow redirect manually
                                            redirect_url = cover_response.headers.get('Location')
                                            if redirect_url:
                                                logger.info(f"Following redirect to: {redirect_url}")
                                                redirect_response = requests.head(redirect_url, timeout=5)
                                                if redirect_response.status_code == 200:
                                                    logger.info(f"Found MusicBrainz cover art via redirect: {redirect_url}")
                                                    return redirect_url
                                        else:
                                            logger.info(f"Cover art not available (HTTP {cover_response.status_code})")
                                    except Exception as e:
                                        logger.info(f"Cover art check failed: {e}")
                                        continue
                    else:
                        logger.info(f"MusicBrainz API error: HTTP {response.status_code}")
                        if response.status_code == 503:
                            logger.info("MusicBrainz rate limited, waiting longer...")
                            self.msleep(2000)
                    
                    # Rate limiting respect
                    self.msleep(1000)
                    
                except Exception as e:
                    logger.info(f"MusicBrainz query failed: {e}")
                    continue
            
            logger.info("No MusicBrainz artwork found after all queries")
            return None
            
        except Exception as e:
            logger.info(f"MusicBrainz search error: {e}")
            return None
    
    def search_lastfm_art(self, artist, title):
        """Search for album artwork using Last.fm API (free, no key needed for some endpoints)"""
        try:
            logger.info(f"Searching Last.fm for: {artist} - {title}")
            
            # Last.fm track.getInfo API (requires API key, so we'll skip this for now)
            # Instead, try a different approach or skip Last.fm
            logger.info("Last.fm requires API key - skipping for now")
            return None
            
        except Exception as e:
            logger.info(f"Last.fm search error: {e}")
            return None
    
    def search_itunes_art(self, artist, title):
        """Search for album artwork using iTunes Search API"""
        try:
            logger.info(f"Searching iTunes for: {artist} - {title}")
            
            # Clean up title - remove parenthetical year info for better matching
            clean_title = title
            if '(' in title and ')' in title:
                clean_title = title.split('(')[0].strip()
                logger.info(f"Cleaned title: '{title}' -> '{clean_title}'")
            
            search_term = f"{artist} {clean_title}".replace(' ', '+')
            itunes_url = f"https://itunes.apple.com/search"
            params = {
                'term': search_term,
                'media': 'music',
                'entity': 'song',
                'limit': 10  # Increase limit for better chances
            }
            
            headers = {
                'User-Agent': 'Pyper/1.0 (Music Player)'
            }
            
            logger.info(f"iTunes search term: {search_term}")
            response = requests.get(itunes_url, params=params, headers=headers, timeout=10)
            logger.info(f"iTunes response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                logger.info(f"iTunes found {len(results)} results")
                
                for i, result in enumerate(results):
                    track_name = result.get('trackName', 'Unknown')
                    artist_name = result.get('artistName', 'Unknown')
                    logger.info(f"iTunes result {i+1}: {artist_name} - {track_name}")
                    
                    # Look for artwork URL
                    artwork_url = result.get('artworkUrl100', '')
                    if artwork_url:
                        # Convert to higher resolution
                        artwork_url = artwork_url.replace('100x100', '600x600')
                        logger.info(f"Found iTunes album art: {artwork_url}")
                        return artwork_url
                    else:
                        logger.info(f"No artwork URL for result {i+1}")
                
                logger.info("No iTunes artwork found in any results")
            else:
                logger.info(f"iTunes API error: HTTP {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.info(f"iTunes search error: {e}")
            return None
    
    def download_artwork(self, artwork_url):
        """Download and emit artwork"""
        try:
            logger.info(f"Downloading artwork from: {artwork_url}")
            
            headers = {
                'User-Agent': 'Pyper/1.0 (Music Player)'
            }
            
            response = requests.get(artwork_url, timeout=15, headers=headers)
            logger.info(f"Artwork download response: {response.status_code}")
            
            if response.status_code == 200:
                content = response.content
                content_type = response.headers.get('content-type', 'unknown')
                logger.info(f"Downloaded {len(content)} bytes, content-type: {content_type}")
                
                # Check if it's actually an image
                if not content_type.startswith('image/'):
                    logger.warning(f"Content type is not an image: {content_type}")
                    # Try to load anyway, sometimes servers don't set proper content-type
                
                pixmap = QPixmap()
                success = pixmap.loadFromData(content)
                
                if success and not pixmap.isNull():
                    logger.info(f"Successfully loaded artwork: {pixmap.width()}x{pixmap.height()}")
                    scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.artwork_ready.emit(scaled_pixmap)
                    logger.info("Emitted artwork successfully")
                else:
                    logger.warning("Failed to load pixmap from downloaded data")
                    logger.info(f"Content preview (first 100 bytes): {content[:100]}")
            else:
                logger.warning(f"Failed to download artwork: HTTP {response.status_code}")
                if response.status_code == 404:
                    logger.info("Artwork URL returned 404 - not found")
                elif response.status_code == 403:
                    logger.info("Artwork URL returned 403 - forbidden")
                    
        except Exception as e:
            logger.error(f"Artwork download error: {e}")
            import traceback
            logger.error(f"Download traceback: {traceback.format_exc()}")
    
    def emit_default_radio_artwork(self):
        """Create and emit a default radio artwork when no album art is found"""
        try:
            logger.info("Creating default radio artwork...")
            
            # Create a simple default radio artwork
            pixmap = QPixmap(200, 200)
            pixmap.fill(Qt.GlobalColor.darkGray)
            
            # Draw a musical note or radio icon
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Arial", 48))
            
            # Use a simple text character instead of emoji which might not render
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
            painter.end()
            
            logger.info(f"Created default artwork: {pixmap.width()}x{pixmap.height()}")
            self.artwork_ready.emit(pixmap)
            logger.info("Emitted default radio artwork")
            
        except Exception as e:
            logger.error(f"Error creating default artwork: {e}")
            import traceback
            logger.error(f"Default artwork traceback: {traceback.format_exc()}") 