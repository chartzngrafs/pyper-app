"""
Subsonic Client Module for Pyper Music Player
Custom Subsonic API client that handles authentication correctly
"""

import hashlib
import random
import string
import requests

# Constants (imported from main module)
DEFAULT_SEARCH_LIMITS = {'artists': 20, 'albums': 20, 'songs': 50}


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
    
    def getAlbumList2_byNewest(self, size=50):
        """Get recently added albums (newest first)"""
        params = {
            'type': 'newest',
            'size': size
        }
        try:
            return self._make_request('getAlbumList2', params)
        except:
            return None
    
    def getInternetRadioStations(self):
        """Get all internet radio stations"""
        try:
            return self._make_request('getInternetRadioStations')
        except:
            return None 