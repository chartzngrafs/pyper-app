"""
Metadata Enrichment Module for Dynamic Themes
Enhances track metadata using MusicBrainz and Last.fm APIs
"""

import logging
import musicbrainzngs
import time
import requests
from typing import Dict, Optional, List
from threading import Lock
import hashlib
import json
import numpy as np

logger = logging.getLogger('DynamicThemes.MetadataEnricher')

# Silence verbose MusicBrainz logging that floods the console
musicbrainz_logger = logging.getLogger('musicbrainzngs')
musicbrainz_logger.setLevel(logging.WARNING)  # Only show warnings and errors

class MetadataEnricher:
    """Enhanced metadata enrichment using multiple free APIs"""
    
    def __init__(self, config):
        self.config = config
        # Get rate limit from config, default to 0.5s (MusicBrainz allows 1 req/sec)
        if hasattr(config, 'config'):
            self.rate_limit_delay = config.config.get('external_services', {}).get('rate_limit_delay', 0.5)
        else:
            self.rate_limit_delay = 0.5
        self.last_mb_request = 0.0
        self.last_lastfm_request = 0.0
        self.metadata_cache = {}
        self.cache_lock = Lock()
        
        # Initialize MusicBrainz
        musicbrainzngs.set_useragent("Pyper", "2.1.0", "https://github.com/pyper-app")
        musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)
        
        # Last.fm API setup (free tier)
        self.lastfm_api_key = self._get_lastfm_api_key()
        self.lastfm_enabled = self.lastfm_api_key is not None
        
        logger.info("Enhanced metadata enricher initialized with MusicBrainz + Last.fm")
    
    def _get_lastfm_api_key(self) -> Optional[str]:
        """Get Last.fm API key from config or environment"""
        # Check config first
        try:
            # Try different config access patterns
            if hasattr(self.config, 'config'):
                # DynamicThemesConfig object
                api_key = self.config.config.get('external_apis', {}).get('lastfm_api_key')
            elif hasattr(self.config, 'get'):
                # Dict-like config object
                api_key = self.config.get('external_apis', {}).get('lastfm_api_key')
            else:
                # Direct attribute access
                api_key = getattr(self.config, 'external_apis', {}).get('lastfm_api_key')
            
            if api_key:
                logger.info("Using Last.fm API key from configuration")
                return api_key
        except (AttributeError, TypeError) as e:
            logger.debug(f"Config access failed: {e}")
            pass
            
        # Check environment variable
        import os
        api_key = os.getenv('LASTFM_API_KEY')
        if api_key:
            logger.info("Using Last.fm API key from environment variable")
            return api_key
            
        logger.info("No Last.fm API key found - using MusicBrainz only")
        return None
    
    def enrich_track_metadata(self, track_info: Dict) -> Dict:
        """Enhanced track metadata enrichment using multiple APIs"""
        try:
            track_id = track_info.get('id', 'unknown')
            
            # Check cache first
            if track_id in self.metadata_cache:
                logger.debug(f"Using cached metadata for track {track_id}")
                return self.metadata_cache[track_id]
            
            enriched_data = {}
            
            # 1. MusicBrainz enrichment (genres, styles, advanced metadata)
            mb_data = self._query_musicbrainz_enhanced(track_info)
            if mb_data:
                enriched_data.update(mb_data)
            
            # 2. Last.fm enrichment (tags, similar tracks, listening data)
            if self.lastfm_enabled:
                lastfm_data = self._query_lastfm(track_info)
                if lastfm_data:
                    enriched_data.update(lastfm_data)
            
            # 3. Derive intelligent features from enriched metadata
            intelligent_features = self._derive_intelligent_features(enriched_data, track_info)
            enriched_data.update(intelligent_features)
            
            # Cache the results
            with self.cache_lock:
                self.metadata_cache[track_id] = enriched_data
            
            logger.debug(f"Enriched metadata for track {track_id} with {len(enriched_data)} features")
            return enriched_data
            
        except Exception as e:
            logger.error(f"Metadata enrichment failed for track {track_info.get('id', 'unknown')}: {e}")
            return {}
    
    def _query_musicbrainz_enhanced(self, track_info: Dict) -> Optional[Dict]:
        """Enhanced MusicBrainz query focusing on genres, styles, and mood data"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_mb_request
            if time_since_last < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - time_since_last)
            
            self.last_mb_request = time.time()
            
            # Build focused search query
            title = track_info.get('title', '').strip()
            artist = track_info.get('artist', '').strip()
            
            if not title or not artist:
                return None
            
            # Clean up search terms for better matching
            clean_title = self._clean_search_term(title)
            clean_artist = self._clean_search_term(artist)
            
            search_query = f'recording:"{clean_title}" AND artist:"{clean_artist}"'
            
            result = musicbrainzngs.search_recordings(
                query=search_query,
                limit=1,  # Just need the best match
                offset=0,
                strict=False
            )
            
            if not result.get('recording-list'):
                logger.debug(f"No MusicBrainz results for: {artist} - {title}")
                return None
            
            recording = result['recording-list'][0]
            enriched_data = {}
            
            # Extract genre/style tags with better error handling
            if 'tag-list' in recording:
                tags = []
                for tag in recording['tag-list']:
                    try:
                        count = tag.get('count', 0)
                        count = int(count) if count is not None else 0
                        if count > 0:  # Any tagged occurrence
                            tags.append(tag['name'].lower())
                    except (ValueError, TypeError):
                        continue
                
                if tags:
                    enriched_data['mb_tags'] = tags[:10]  # Top 10 tags
                    enriched_data['mb_primary_genre'] = tags[0]
                    
                    # Categorize tags into types
                    enriched_data['mb_genres'] = [t for t in tags if self._is_genre_tag(t)][:5]
                    enriched_data['mb_moods'] = [t for t in tags if self._is_mood_tag(t)][:3]
                    enriched_data['mb_styles'] = [t for t in tags if self._is_style_tag(t)][:3]
            
            # Extract release information
            if 'release-list' in recording:
                release = recording['release-list'][0]
                if 'release-group' in release:
                    rg = release['release-group']
                    if 'primary-type' in rg:
                        enriched_data['mb_release_type'] = rg['primary-type'].lower()
            
            # Extract artist country/origin
            if 'artist-credit' in recording:
                artist_credit = recording['artist-credit'][0]
                if 'artist' in artist_credit:
                    artist_mb = artist_credit['artist']
                    if 'area' in artist_mb:
                        enriched_data['mb_artist_country'] = artist_mb['area'].get('name', '').lower()
            
            return enriched_data if enriched_data else None
            
        except Exception as e:
            logger.debug(f"MusicBrainz query failed: {e}")
            return None
    
    def _query_lastfm(self, track_info: Dict) -> Optional[Dict]:
        """Query Last.fm for social listening data and community tags"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_lastfm_request
            if time_since_last < 0.5:  # Last.fm allows 5 calls/second
                time.sleep(0.5 - time_since_last)
            
            self.last_lastfm_request = time.time()
            
            title = track_info.get('title', '').strip()
            artist = track_info.get('artist', '').strip()
            
            if not title or not artist:
                return None
            
            # Query Last.fm track info
            url = "http://ws.audioscrobbler.com/2.0/"
            params = {
                'method': 'track.getInfo',
                'api_key': self.lastfm_api_key,
                'artist': artist,
                'track': title,
                'format': 'json',
                'autocorrect': 1  # Auto-correct artist/track names
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if 'track' not in data:
                return None
            
            track_data = data['track']
            enriched_data = {}
            
            # Extract community tags
            if 'toptags' in track_data and 'tag' in track_data['toptags']:
                tags = []
                for tag in track_data['toptags']['tag']:
                    tag_name = tag.get('name', '').lower()
                    if tag_name and len(tag_name) > 1:
                        tags.append(tag_name)
                
                if tags:
                    enriched_data['lastfm_tags'] = tags[:10]
                    enriched_data['lastfm_primary_tag'] = tags[0]
                    
                    # Categorize Last.fm tags
                    enriched_data['lastfm_genres'] = [t for t in tags if self._is_genre_tag(t)][:5]
                    enriched_data['lastfm_moods'] = [t for t in tags if self._is_mood_tag(t)][:3]
            
            # Extract popularity metrics
            if 'playcount' in track_data:
                try:
                    playcount = int(track_data['playcount'])
                    enriched_data['lastfm_playcount'] = playcount
                    # Normalize popularity (log scale)
                    enriched_data['lastfm_popularity'] = min(1.0, np.log10(max(1, playcount)) / 7.0)
                except (ValueError, TypeError):
                    pass
            
            if 'listeners' in track_data:
                try:
                    listeners = int(track_data['listeners'])
                    enriched_data['lastfm_listeners'] = listeners
                    enriched_data['lastfm_reach'] = min(1.0, np.log10(max(1, listeners)) / 6.0)
                except (ValueError, TypeError):
                    pass
            
            return enriched_data if enriched_data else None
            
        except Exception as e:
            logger.debug(f"Last.fm query failed: {e}")
            return None
    
    def _derive_intelligent_features(self, enriched_data: Dict, track_info: Dict) -> Dict:
        """Derive intelligent clustering features from enriched metadata"""
        features = {}
        
        # Combine all genre/tag information
        all_genres = []
        all_genres.extend(enriched_data.get('mb_genres', []))
        all_genres.extend(enriched_data.get('lastfm_genres', []))
        all_genres.extend(enriched_data.get('mb_tags', []))
        all_genres.extend(enriched_data.get('lastfm_tags', []))
        
        # Genre intelligence
        if all_genres:
            features['intelligent_primary_genre'] = all_genres[0]
            features['genre_diversity'] = len(set(all_genres))
            
            # Electronic music detection
            electronic_keywords = ['electronic', 'techno', 'house', 'ambient', 'edm', 'synth', 'electro']
            features['is_electronic'] = any(keyword in ' '.join(all_genres) for keyword in electronic_keywords)
            
            # Rock music detection  
            rock_keywords = ['rock', 'metal', 'punk', 'grunge', 'alternative', 'indie rock']
            features['is_rock'] = any(keyword in ' '.join(all_genres) for keyword in rock_keywords)
            
            # Jazz/experimental detection
            jazz_keywords = ['jazz', 'experimental', 'avant-garde', 'fusion', 'improvisation']
            features['is_experimental'] = any(keyword in ' '.join(all_genres) for keyword in jazz_keywords)
        
        # Mood intelligence
        all_moods = []
        all_moods.extend(enriched_data.get('mb_moods', []))
        all_moods.extend(enriched_data.get('lastfm_moods', []))
        
        if all_moods:
            # Mood scoring
            energetic_moods = ['energetic', 'upbeat', 'happy', 'danceable', 'party']
            chill_moods = ['chill', 'relaxing', 'mellow', 'ambient', 'peaceful']
            dark_moods = ['dark', 'melancholy', 'sad', 'atmospheric', 'brooding']
            
            mood_text = ' '.join(all_moods)
            features['mood_energetic'] = sum(1 for mood in energetic_moods if mood in mood_text) / len(energetic_moods)
            features['mood_chill'] = sum(1 for mood in chill_moods if mood in mood_text) / len(chill_moods)
            features['mood_dark'] = sum(1 for mood in dark_moods if mood in mood_text) / len(dark_moods)
        
        # Popularity/discovery intelligence
        lastfm_popularity = enriched_data.get('lastfm_popularity', 0.5)
        local_play_count = track_info.get('play_count', 0)
        
        # Hidden gems detection (low global popularity, high local play count)
        if local_play_count > 5 and lastfm_popularity < 0.3:
            features['is_hidden_gem'] = True
            features['discovery_score'] = 0.8
        elif lastfm_popularity > 0.7:
            features['is_mainstream'] = True
            features['discovery_score'] = 0.2
        else:
            features['discovery_score'] = 0.5
        
        # Era intelligence (combine year with genre evolution)
        year = track_info.get('year', 0)
        if year and all_genres:
            if year < 1980 and any('rock' in g for g in all_genres):
                features['era_signature'] = 'classic_rock'
            elif 1980 <= year < 1990 and features.get('is_electronic'):
                features['era_signature'] = 'early_electronic'
            elif 1990 <= year < 2000 and any('alternative' in g for g in all_genres):
                features['era_signature'] = '90s_alternative'
            elif 2000 <= year < 2010 and any('indie' in g for g in all_genres):
                features['era_signature'] = '2000s_indie'
            elif year >= 2010:
                features['era_signature'] = 'modern'
        
        return features
    
    def _clean_search_term(self, term: str) -> str:
        """Clean search terms for better API matching"""
        # Remove common parenthetical additions
        import re
        term = re.sub(r'\([^)]*\)', '', term)  # Remove (feat. Artist)
        term = re.sub(r'\[[^\]]*\]', '', term)  # Remove [Remix]
        return term.strip()
    
    def _is_genre_tag(self, tag: str) -> bool:
        """Identify if a tag represents a musical genre"""
        genre_keywords = [
            'rock', 'pop', 'jazz', 'blues', 'country', 'folk', 'electronic', 'hip hop',
            'rap', 'metal', 'punk', 'reggae', 'classical', 'ambient', 'techno', 'house',
            'indie', 'alternative', 'experimental', 'funk', 'soul', 'r&b'
        ]
        return any(keyword in tag for keyword in genre_keywords)
    
    def _is_mood_tag(self, tag: str) -> bool:
        """Identify if a tag represents a mood or atmosphere"""
        mood_keywords = [
            'chill', 'relaxing', 'energetic', 'upbeat', 'melancholy', 'happy', 'sad',
            'dark', 'atmospheric', 'peaceful', 'aggressive', 'mellow', 'dreamy'
        ]
        return any(keyword in tag for keyword in mood_keywords)
    
    def _is_style_tag(self, tag: str) -> bool:
        """Identify if a tag represents a musical style"""
        style_keywords = [
            'acoustic', 'instrumental', 'vocal', 'live', 'studio', 'remix', 'cover',
            'orchestral', 'symphonic', 'minimalist', 'progressive', 'psychedelic'
        ]
        return any(keyword in tag for keyword in style_keywords)
    
    def clear_cache(self):
        """Clear metadata enrichment cache"""
        with self.cache_lock:
            self.metadata_cache.clear()
        logger.info("Metadata cache cleared") 