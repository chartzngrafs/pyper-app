"""
Dynamic Theme Engine - Phase 1 MVP
Core engine for discovering library-specific themes using basic clustering

This implementation focuses on simplicity and functionality for the MVP.
Advanced features will be added in later phases.
"""

import logging
import json
import os
import hashlib
import time
from typing import List, Dict, Any, Optional, Callable
from collections import defaultdict, Counter
import re

# Basic dependencies for Phase 1
try:
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
except ImportError as e:
    logging.error(f"Required ML libraries not installed: {e}")
    logging.error("Please install: pip install scikit-learn numpy")
    raise

logger = logging.getLogger('DynamicThemes')


class DynamicThemeEngine:
    """Main engine orchestrating theme discovery - Phase 1 MVP"""
    
    def __init__(self, library_data: Dict[str, Any], sonic_client):
        self.library_data = library_data
        self.sonic_client = sonic_client
        self.discovery_engine = BasicThemeDiscovery(library_data)
        self.cache = ThemeCache()
        
        logger.info("Dynamic Theme Engine initialized (Phase 1 MVP)")
    
    def discover_library_themes(self, progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Main theme discovery pipeline for Phase 1"""
        try:
            if progress_callback:
                progress_callback("Starting library analysis...", 0)
            
            # Get all tracks from library
            all_tracks = self.get_all_library_tracks()
            
            if not all_tracks:
                logger.error("No tracks found in library")
                return []
            
            if progress_callback:
                progress_callback(f"Analyzing {len(all_tracks)} tracks...", 25)
            
            # Discover themes
            themes = self.discovery_engine.discover_themes(all_tracks)
            
            if progress_callback:
                progress_callback("Finalizing themes...", 90)
            
            # Cache results
            self.cache.save_themes(themes)
            
            if progress_callback:
                progress_callback(f"Discovered {len(themes)} themes!", 100)
            
            logger.info(f"Theme discovery complete: {len(themes)} themes generated")
            return themes
            
        except Exception as e:
            logger.error(f"Theme discovery failed: {e}")
            if progress_callback:
                progress_callback(f"Error: {str(e)}", -1)
            return []
    
    def get_all_library_tracks(self) -> List[Dict[str, Any]]:
        """Extract all tracks from library data"""
        all_tracks = []
        
        # Get tracks from artists -> albums -> songs structure
        artists = self.library_data.get('artists', [])
        for artist in artists:
            albums = artist.get('albums', [])
            for album in albums:
                songs = album.get('songs', [])
                for song in songs:
                    # Enrich song data with artist and album info
                    enriched_song = dict(song)
                    enriched_song['artist'] = artist.get('name', 'Unknown Artist')
                    enriched_song['album'] = album.get('name', 'Unknown Album')
                    enriched_song['year'] = album.get('year') or song.get('year')
                    all_tracks.append(enriched_song)
        
        logger.info(f"Extracted {len(all_tracks)} tracks from library")
        return all_tracks
    
    def get_cached_themes(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached themes if available and valid"""
        return self.cache.load_themes()


class BasicThemeDiscovery:
    """Phase 1 MVP implementation with basic clustering"""
    
    def __init__(self, library_data: Dict[str, Any]):
        self.library_data = library_data
        self.scaler = StandardScaler()
        
    def discover_themes(self, tracks: List[Dict], n_themes: int = 15) -> List[Dict[str, Any]]:
        """MVP theme discovery using K-means clustering"""
        logger.info(f"Starting theme discovery for {len(tracks)} tracks")
        
        if len(tracks) < 10:
            logger.warning("Not enough tracks for meaningful theme discovery")
            return []
        
        # Extract features
        features = self.extract_basic_features(tracks)
        if features is None or len(features) == 0:
            logger.error("Failed to extract features from tracks")
            return []
        
        # Normalize features
        features_normalized = self.scaler.fit_transform(features)
        
        # Apply clustering
        try:
            clusters = KMeans(n_clusters=min(n_themes, len(tracks)//5), random_state=42).fit_predict(features_normalized)
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return []
        
        # Generate themes from clusters
        themes = self.generate_basic_themes(tracks, clusters)
        
        logger.info(f"Generated {len(themes)} themes")
        return themes
        
    def extract_basic_features(self, tracks: List[Dict]) -> Optional[np.ndarray]:
        """Extract basic features for MVP clustering"""
        features = []
        
        for track in tracks:
            try:
                track_features = []
                
                # Year feature (normalized 0-1)
                year = self.extract_year(track)
                year_norm = (year - 1950) / (2024 - 1950) if year else 0.5
                track_features.append(year_norm)
                
                # Genre features (simple one-hot encoding for top genres)
                genre_vector = self.extract_genre_features(track)
                track_features.extend(genre_vector)
                
                # Play count feature (normalized)
                play_count = track.get('playCount', 0)
                play_count_norm = min(play_count / 100.0, 1.0)  # Cap at 100 plays
                track_features.append(play_count_norm)
                
                # Duration feature (normalized)
                duration = track.get('duration', 0)
                duration_norm = min(duration / 600.0, 1.0) if duration else 0.5  # Cap at 10 minutes
                track_features.append(duration_norm)
                
                features.append(track_features)
                
            except Exception as e:
                logger.warning(f"Failed to extract features for track {track.get('title', 'Unknown')}: {e}")
                # Add default features
                features.append([0.5] * 8)  # Default feature vector
        
        return np.array(features) if features else None
    
    def extract_year(self, track: Dict) -> Optional[int]:
        """Extract year from track metadata"""
        year = track.get('year')
        if year:
            return int(year)
        
        # Try to extract from date
        date_str = track.get('created') or track.get('date')
        if date_str:
            try:
                return int(date_str[:4])
            except (ValueError, TypeError):
                pass
        
        return None
    
    def extract_genre_features(self, track: Dict) -> List[float]:
        """Extract genre features using simple encoding"""
        genre = track.get('genre', '').lower()
        
        # Top genres for feature encoding (Phase 1 MVP)
        top_genres = ['rock', 'pop', 'electronic', 'classical', 'jazz', 'metal']
        
        genre_features = []
        for target_genre in top_genres:
            if target_genre in genre:
                genre_features.append(1.0)
            else:
                genre_features.append(0.0)
        
        return genre_features
    
    def generate_basic_themes(self, tracks: List[Dict], clusters: np.ndarray) -> List[Dict[str, Any]]:
        """Convert clusters into themed playlists with basic naming"""
        themes = []
        
        # Group tracks by cluster
        cluster_tracks = defaultdict(list)
        for track, cluster_id in zip(tracks, clusters):
            cluster_tracks[cluster_id].append(track)
        
        for cluster_id, cluster_tracks_list in cluster_tracks.items():
            if len(cluster_tracks_list) < 5:  # Skip small clusters
                continue
            
            # Analyze cluster characteristics
            cluster_info = self.analyze_cluster(cluster_tracks_list)
            
            # Generate theme name
            theme_name = self.generate_theme_name(cluster_info)
            
            # Create theme object
            theme = {
                'id': f"theme_{cluster_id}",
                'name': theme_name,
                'description': self.generate_theme_description(cluster_info),
                'tracks': cluster_tracks_list,
                'track_count': len(cluster_tracks_list),
                'characteristics': cluster_info,
                'created_at': time.time()
            }
            
            themes.append(theme)
        
        # Sort themes by size (most tracks first)
        themes.sort(key=lambda x: x['track_count'], reverse=True)
        
        return themes[:20]  # Limit to top 20 themes
    
    def analyze_cluster(self, tracks: List[Dict]) -> Dict[str, Any]:
        """Analyze characteristics of a cluster"""
        years = []
        genres = []
        artists = []
        durations = []
        
        for track in tracks:
            if track.get('year'):
                years.append(int(track['year']))
            if track.get('genre'):
                genres.append(track['genre'].lower())
            if track.get('artist'):
                artists.append(track['artist'])
            if track.get('duration'):
                durations.append(track['duration'])
        
        # Calculate characteristics
        info = {
            'year_range': (min(years), max(years)) if years else None,
            'primary_decade': self.get_primary_decade(years) if years else None,
            'top_genres': [genre for genre, count in Counter(genres).most_common(3)],
            'top_artists': [artist for artist, count in Counter(artists).most_common(3)],
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'track_count': len(tracks)
        }
        
        return info
    
    def get_primary_decade(self, years: List[int]) -> str:
        """Get the primary decade from a list of years"""
        if not years:
            return "Unknown"
        
        decades = [(year // 10) * 10 for year in years]
        most_common_decade = Counter(decades).most_common(1)[0][0]
        return f"{most_common_decade}s"
    
    def generate_theme_name(self, cluster_info: Dict[str, Any]) -> str:
        """Generate theme name using templates"""
        templates = [
            "{decade} {primary_genre}",
            "{primary_genre} {mood}",
            "{decade} Hidden Gems",
            "{primary_artist} & Similar",
            "Classic {primary_genre}",
            "{decade} {primary_genre} Collection"
        ]
        
        # Extract info for naming
        decade = cluster_info.get('primary_decade', 'Mixed Era')
        primary_genre = cluster_info.get('top_genres', ['Music'])[0].title()
        primary_artist = cluster_info.get('top_artists', ['Various'])[0]
        
        # Simple mood inference
        avg_duration = cluster_info.get('avg_duration', 0)
        if avg_duration > 300:  # > 5 minutes
            mood = "Epic"
        elif avg_duration < 180:  # < 3 minutes
            mood = "Quick Hits"
        else:
            mood = "Essentials"
        
        # Choose best template
        template = templates[0]  # Default
        if decade != "Unknown" and primary_genre != "Music":
            template = templates[0]  # "{decade} {primary_genre}"
        elif primary_genre and primary_genre != "Music":
            template = templates[1]  # "{primary_genre} {mood}"
        
        name = template.format(
            decade=decade,
            primary_genre=primary_genre,
            mood=mood,
            primary_artist=primary_artist
        )
        
        return name
    
    def generate_theme_description(self, cluster_info: Dict[str, Any]) -> str:
        """Generate theme description"""
        track_count = cluster_info.get('track_count', 0)
        year_range = cluster_info.get('year_range')
        top_genres = cluster_info.get('top_genres', [])
        top_artists = cluster_info.get('top_artists', [])
        
        description_parts = []
        
        if year_range:
            if year_range[0] == year_range[1]:
                description_parts.append(f"Music from {year_range[0]}")
            else:
                description_parts.append(f"Music spanning {year_range[0]}-{year_range[1]}")
        
        if top_genres:
            genres_str = ", ".join(top_genres[:2])
            description_parts.append(f"featuring {genres_str}")
        
        if top_artists and len(top_artists) > 1:
            description_parts.append(f"including tracks by {top_artists[0]} and others")
        
        base_description = ". ".join(description_parts).capitalize()
        return f"{base_description}. {track_count} tracks total."


class ThemeCache:
    """Simple file-based cache for theme analysis results"""
    
    def __init__(self):
        self.cache_dir = os.path.join(os.path.expanduser('~'), '.pyper', 'theme_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, 'discovered_themes.json')
    
    def save_themes(self, themes: List[Dict[str, Any]]):
        """Save discovered themes to cache"""
        try:
            cache_data = {
                'themes': themes,
                'created_at': time.time(),
                'version': '1.0.0-mvp'
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Cached {len(themes)} themes to {self.cache_file}")
            
        except Exception as e:
            logger.error(f"Failed to cache themes: {e}")
    
    def load_themes(self) -> Optional[List[Dict[str, Any]]]:
        """Load themes from cache if valid"""
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check cache age (valid for 7 days)
            cache_age = time.time() - cache_data.get('created_at', 0)
            if cache_age > (7 * 24 * 60 * 60):  # 7 days in seconds
                logger.info("Theme cache expired, will regenerate")
                return None
            
            themes = cache_data.get('themes', [])
            logger.info(f"Loaded {len(themes)} themes from cache")
            return themes
            
        except Exception as e:
            logger.error(f"Failed to load cached themes: {e}")
            return None
    
    def clear_cache(self):
        """Clear the theme cache"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                logger.info("Theme cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}") 