"""
Dynamic Theme Engine - Phase 2 Step 2
Core engine for discovering library-specific themes using advanced clustering

Enhanced with audio analysis and metadata enrichment for intelligent themes.
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
    """Main engine orchestrating theme discovery - Phase 2 Step 2"""
    
    def __init__(self, library_data: Dict[str, Any], sonic_client, db_helper=None, config=None):
        self.library_data = library_data
        self.sonic_client = sonic_client
        self.db_helper = db_helper
        self.config = config
        
        # Core discovery engine
        self.discovery_engine = BasicThemeDiscovery(library_data, db_helper)
        self.cache = ThemeCache()
        
        # Phase 2 Step 2: Advanced analysis components
        self.advanced_enabled = config and config.is_advanced_analysis_enabled()
        
        if self.advanced_enabled:
            try:
                # Import Phase 2 modules dynamically to avoid dependency issues
                from .audio_analyzer import AudioAnalyzer
                from .metadata_enricher import MetadataEnricher
                
                self.audio_analyzer = AudioAnalyzer(config)
                self.metadata_enricher = MetadataEnricher(config)
                logger.info("Advanced analysis enabled with audio and metadata enrichment")
            except ImportError as e:
                logger.warning(f"Advanced analysis dependencies not available: {e}")
                self.advanced_enabled = False
                self.audio_analyzer = None
                self.metadata_enricher = None
        else:
            self.audio_analyzer = None
            self.metadata_enricher = None
            logger.info("Basic analysis mode (Phase 1 compatible)")
        
        logger.info(f"Dynamic Theme Engine initialized (Phase 2 Step 2, Advanced: {self.advanced_enabled})")
    
    def discover_library_themes(self, progress_callback: Optional[Callable] = None, force_fresh: bool = False) -> List[Dict[str, Any]]:
        """Enhanced theme discovery pipeline with Phase 2 Step 2 features"""
        try:
            if progress_callback:
                progress_callback("Starting library analysis...", 0)
            
            # Check for cached themes first (unless forced fresh analysis)
            if not force_fresh:
                cached_themes = self.get_cached_themes()
                if cached_themes:
                    logger.info(f"Loaded {len(cached_themes)} themes from cache")
                    if progress_callback:
                        progress_callback(f"Loaded {len(cached_themes)} themes from cache", 100)
                    return cached_themes
            else:
                logger.info("Forcing fresh analysis - ignoring cached themes")
            
            # Get all tracks from library
            all_tracks = self.get_all_library_tracks()
            
            if not all_tracks:
                logger.error("No tracks found in library")
                return []
            
            if progress_callback:
                progress_callback(f"Preparing {len(all_tracks)} tracks...", 10)
            
            # Phase 2 Step 2: Advanced analysis if enabled
            if self.advanced_enabled:
                all_tracks = self._perform_advanced_analysis(all_tracks, progress_callback)
            
            if progress_callback:
                progress_callback(f"Clustering {len(all_tracks)} tracks...", 70)
            
            # Discover themes (now with enriched data)
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
        """Extract all tracks from library data - preferring database over API"""
        all_tracks = []
        
        # Try to get tracks from database first (more complete data)
        if self.db_helper:
            try:
                all_tracks = self.db_helper.get_all_tracks_for_themes()
                if all_tracks:
                    logger.info(f"Extracted {len(all_tracks)} tracks from database")
                    return all_tracks
            except Exception as e:
                logger.warning(f"Failed to get tracks from database: {e}")
        
        # Fallback to API-based library data
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
    
    def _perform_advanced_analysis(self, tracks: List[Dict], progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Phase 2 Step 2: Smart analysis with intelligent sampling for large libraries"""
        try:
            logger.info(f"Starting smart analysis for {len(tracks)} tracks")
            analysis_start_time = time.time()
            
            # Smart approach: For large libraries, use intelligent sampling
            if len(tracks) > 300:
                return self._smart_sampling_analysis(tracks, progress_callback)
            else:
                return self._full_analysis(tracks, progress_callback)
                
        except Exception as e:
            logger.error(f"Advanced analysis failed: {e}")
            return tracks  # Return original tracks if analysis fails
    
    def _smart_sampling_analysis(self, tracks: List[Dict], progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Smart sampling approach for large libraries (300+ tracks)"""
        logger.info(f"Large library detected ({len(tracks)} tracks) - using intelligent sampling")
        
        # Step 1: Get representative sample (5-10% of library, max 100 tracks)
        sample_size = min(100, max(20, len(tracks) // 15))  # 6.7% sample, 20-100 tracks
        sampled_tracks = self._get_representative_sample(tracks, sample_size)
        
        if progress_callback:
            progress_callback(f"Analyzing {len(sampled_tracks)} representative tracks...", 20)
        
        # Step 2: Enrich sample tracks with full analysis
        enriched_sample = self._full_analysis(sampled_tracks, None)  # No progress callback for sample
        
        if progress_callback:
            progress_callback("Learning patterns from sample...", 60)
        
        # Step 3: Apply learned patterns to all tracks
        enriched_tracks = self._apply_enrichment_patterns(tracks, enriched_sample, progress_callback)
        
        logger.info(f"Smart sampling complete: analyzed {len(sampled_tracks)} sample tracks, applied patterns to {len(tracks)} total tracks")
        return enriched_tracks
    
    def _full_analysis(self, tracks: List[Dict], progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Full analysis for smaller libraries or sample tracks"""
        enriched_tracks = []
        successful_metadata = 0
        successful_audio = 0
        total_errors = 0
        
        for i, track in enumerate(tracks):
            if progress_callback and i % max(1, len(tracks) // 10) == 0:
                progress = 20 + int((i / len(tracks)) * 40)  # 20% to 60%
                progress_callback(f"Analyzing track {i+1}/{len(tracks)}...", progress)
            
            enriched_track = dict(track)
            
            # Metadata enrichment (with rate limiting)
            if self.metadata_enricher:
                try:
                    metadata_features = self.metadata_enricher.enrich_track_metadata(enriched_track)
                    enriched_track.update(metadata_features)
                    successful_metadata += 1
                except Exception as e:
                    logger.debug(f"Metadata enrichment failed for track {i}: {e}")
                    total_errors += 1
            
            # Audio analysis (currently disabled for performance)
            # if self.audio_analyzer and track.get('id'):
            #     try:
            #         audio_features = self.audio_analyzer.analyze_track_audio(
            #             self.sonic_client, track['id'], enriched_track
            #         )
            #         enriched_track.update(audio_features)
            #         successful_audio += 1
            #     except Exception as e:
            #         logger.debug(f"Audio analysis failed for track {i}: {e}")
            #         total_errors += 1
            
            enriched_tracks.append(enriched_track)
        
        logger.info(f"Full analysis complete: Metadata: {successful_metadata}/{len(tracks)}, Audio: {successful_audio}/{len(tracks)}, Errors: {total_errors}")
        return enriched_tracks
    
    def _get_representative_sample(self, tracks: List[Dict], sample_size: int) -> List[Dict]:
        """Get a representative sample of tracks for analysis"""
        import random
        
        # Group tracks by artist to ensure diversity
        artist_groups = {}
        for track in tracks:
            artist = track.get('artist', 'Unknown')
            if artist not in artist_groups:
                artist_groups[artist] = []
            artist_groups[artist].append(track)
        
        # Sample from each artist group
        sampled_tracks = []
        artists = list(artist_groups.keys())
        random.shuffle(artists)
        
        tracks_per_artist = max(1, sample_size // len(artists))
        
        for artist in artists:
            artist_tracks = artist_groups[artist]
            # Sample tracks from this artist
            sample_count = min(tracks_per_artist, len(artist_tracks))
            sampled_tracks.extend(random.sample(artist_tracks, sample_count))
            
            if len(sampled_tracks) >= sample_size:
                break
        
        # If we need more tracks, add random ones
        if len(sampled_tracks) < sample_size:
            remaining_tracks = [t for t in tracks if t not in sampled_tracks]
            additional_needed = sample_size - len(sampled_tracks)
            if remaining_tracks:
                sampled_tracks.extend(random.sample(remaining_tracks, min(additional_needed, len(remaining_tracks))))
        
        logger.info(f"Selected {len(sampled_tracks)} representative tracks from {len(artists)} artists")
        return sampled_tracks[:sample_size]
    
    def _apply_enrichment_patterns(self, all_tracks: List[Dict], enriched_sample: List[Dict], progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Apply learned patterns from enriched sample to all tracks"""
        if progress_callback:
            progress_callback("Applying learned patterns to all tracks...", 70)
        
        # Create pattern mappings from enriched sample
        artist_patterns = {}
        genre_patterns = {}
        
        for track in enriched_sample:
            artist = track.get('artist', 'Unknown')
            genre = track.get('genre', 'Unknown')
            
            # Store patterns by artist
            if artist not in artist_patterns:
                artist_patterns[artist] = {}
            
            # Store patterns by genre
            if genre not in genre_patterns:
                genre_patterns[genre] = {}
            
            # Extract learned features
            for key, value in track.items():
                if key.startswith(('mb_', 'lastfm_', 'genre_', 'mood_', 'intelligent_')):
                    # Convert lists to strings to make them hashable
                    if isinstance(value, list):
                        value = ', '.join(str(v) for v in value) if value else ''
                    
                    # Skip None or empty values
                    if value is None or value == '':
                        continue
                    
                    if key not in artist_patterns[artist]:
                        artist_patterns[artist][key] = []
                    artist_patterns[artist][key].append(value)
                    
                    if key not in genre_patterns[genre]:
                        genre_patterns[genre][key] = []
                    genre_patterns[genre][key].append(value)
        
        # Apply patterns to all tracks
        enriched_all_tracks = []
        for i, track in enumerate(all_tracks):
            if progress_callback and i % max(1, len(all_tracks) // 20) == 0:
                progress = 70 + int((i / len(all_tracks)) * 20)  # 70% to 90%
                progress_callback(f"Applying patterns {i+1}/{len(all_tracks)}...", progress)
            
            enriched_track = dict(track)
            
            # Apply artist-based patterns
            artist = track.get('artist', 'Unknown')
            if artist in artist_patterns:
                for feature, values in artist_patterns[artist].items():
                    if values and feature not in enriched_track:
                        try:
                            # Use most common value for this artist, with error handling
                            enriched_track[feature] = max(set(values), key=values.count) if values else None
                        except (TypeError, ValueError) as e:
                            # Handle unhashable types by using first value
                            enriched_track[feature] = values[0] if values else None
            
            # Apply genre-based patterns as fallback
            genre = track.get('genre', 'Unknown')
            if genre in genre_patterns:
                for feature, values in genre_patterns[genre].items():
                    if values and feature not in enriched_track:
                        try:
                            enriched_track[feature] = max(set(values), key=values.count) if values else None
                        except (TypeError, ValueError) as e:
                            # Handle unhashable types by using first value
                            enriched_track[feature] = values[0] if values else None
            
            enriched_all_tracks.append(enriched_track)
        
        logger.info(f"Applied enrichment patterns to {len(enriched_all_tracks)} tracks")
        return enriched_all_tracks
    
    def clear_all_caches(self):
        """Clear all caches (themes, audio, metadata)"""
        self.cache.clear_cache()
        
        if self.audio_analyzer:
            self.audio_analyzer.clear_cache()
        
        if self.metadata_enricher:
            self.metadata_enricher.clear_cache()
        
        logger.info("All caches cleared")
    
    def get_analysis_stats(self) -> Dict:
        """Get statistics about the analysis system"""
        stats = {
            'advanced_enabled': self.advanced_enabled,
            'cached_themes': len(self.cache.load_themes() or [])
        }
        
        if self.audio_analyzer:
            stats['audio_cache_size'] = self.audio_analyzer.get_cache_size()
        
        if self.metadata_enricher:
            stats.update(self.metadata_enricher.get_enrichment_stats())
        
        return stats


class BasicThemeDiscovery:
    """Phase 1 MVP implementation with basic clustering"""
    
    def __init__(self, library_data: Dict[str, Any], db_helper=None):
        self.library_data = library_data
        self.db_helper = db_helper
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
            n_clusters = min(n_themes, max(2, len(tracks)//5))  # Ensure at least 2 clusters
            if n_clusters > len(tracks):
                n_clusters = max(1, len(tracks)//2)
            
            logger.info(f"Applying K-means clustering with {n_clusters} clusters for {len(tracks)} tracks")
            clusters = KMeans(n_clusters=n_clusters, random_state=42).fit_predict(features_normalized)
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
        expected_feature_length = 9  # 1 year + 6 genres + 1 play_count + 1 duration
        
        for i, track in enumerate(tracks):
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
                
                # Validate feature vector length
                if len(track_features) != expected_feature_length:
                    logger.warning(f"Track {i}: Expected {expected_feature_length} features, got {len(track_features)}")
                    track_features = [0.5] * expected_feature_length
                
                features.append(track_features)
                
            except Exception as e:
                logger.warning(f"Failed to extract features for track {i} '{track.get('title', 'Unknown')}': {e}")
                # Add default features
                features.append([0.5] * expected_feature_length)
        
        if not features:
            logger.error("No features extracted from any tracks")
            return None
            
        feature_array = np.array(features)
        logger.info(f"Extracted features: {feature_array.shape} (tracks x features)")
        return feature_array
    
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
            cluster_info['tracks'] = cluster_tracks_list  # Add tracks for enriched analysis
            
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
        """Generate intelligent theme names using enriched metadata"""
        tracks = cluster_info.get('tracks', [])
        
        # Analyze enriched metadata from MusicBrainz/Last.fm
        enriched_features = self._analyze_enriched_features(tracks)
        
        logger.info(f"Theme naming - enriched features: {enriched_features}")
        
        # Smart theme naming based on enriched data
        if enriched_features['mood_dominant']:
            # Mood-based themes: "Chill Electronic", "Energetic Rock", "Dark Ambient"
            mood = enriched_features['primary_mood']
            genre = enriched_features['primary_genre']
            if mood and genre and mood != "Atmospheric" and genre != "Music":
                theme_name = f"{mood} {genre}"
                logger.info(f"Generated mood-based theme name: '{theme_name}'")
                return theme_name
        
        elif enriched_features['style_specific']:
            # Style-specific: "Progressive Rock", "Minimal Techno", "Jazz Fusion"
            style = enriched_features['primary_style']
            if style and len(style) > 2 and style != "Music":
                theme_name = style
                logger.info(f"Generated style-specific theme name: '{theme_name}'")
                return theme_name
            else:
                logger.info(f"Invalid style '{style}' detected, falling back to other naming")
        
        elif enriched_features['energy_coherent']:
            # Energy-based: "High Energy Dance", "Mellow Acoustic", "Upbeat Pop"
            energy = enriched_features['energy_level']
            genre = enriched_features['primary_genre']
            if energy and genre and energy != "Mellow" and genre != "Music":
                theme_name = f"{energy} {genre}"
                logger.info(f"Generated energy-based theme name: '{theme_name}'")
                return theme_name
        
        elif enriched_features['discovery_theme']:
            # Discovery themes: "Hidden Gems", "Deep Cuts", "Rare Finds"
            theme_name = enriched_features['discovery_name']
            logger.info(f"Generated discovery theme name: '{theme_name}'")
            return theme_name
        
        elif enriched_features['era_specific']:
            # Era + style: "90s Alternative", "Classic Rock Anthems", "Modern Indie"
            era = enriched_features['era_name']
            style = enriched_features['style_name']
            if era and style and style != "Music":
                theme_name = f"{era} {style}"
                logger.info(f"Generated era-specific theme name: '{theme_name}' (era: '{era}', style: '{style}')")
                return theme_name
        
        # If enriched features failed or produced invalid results, use fallback
        theme_name = self._generate_fallback_theme_name(cluster_info, tracks)
        logger.info(f"Generated fallback theme name: '{theme_name}'")
        return theme_name
    
    def _generate_fallback_theme_name(self, cluster_info: Dict[str, Any], tracks: List[Dict]) -> str:
        """Generate theme names when enriched features aren't available"""
        if not tracks:
            return "Mixed Collection"
        
        # Analyze basic track characteristics
        genres = []
        artists = []
        years = []
        play_counts = []
        
        for track in tracks:
            genre = track.get('genre', '').strip()
            if genre and genre.lower() not in ['unknown', 'other', '']:
                genres.append(genre.lower().strip())
            if track.get('artist'):
                artists.append(track['artist'])
            if track.get('year'):
                try:
                    years.append(int(track['year']))
                except (ValueError, TypeError):
                    pass
            if track.get('playCount', 0) > 0:
                play_counts.append(track['playCount'])
        
        # Find dominant genre
        genre_counter = Counter(genres)
        primary_genre = self._get_clean_genre_name(genre_counter)
        
        # Debug logging
        logger.info(f"Fallback naming - genres found: {len(genres)}, primary_genre: '{primary_genre}'")
        
        # Check for artist-based themes (multiple tracks from same artist)
        artist_counter = Counter(artists)
        top_artist = artist_counter.most_common(1)[0] if artist_counter else None
        
        # Artist-focused theme (if >40% tracks from same artist)
        if top_artist and top_artist[1] > len(tracks) * 0.4:
            artist_name = top_artist[0]
            if primary_genre and primary_genre != "Music":
                return f"{artist_name} - {primary_genre}"
            else:
                return f"{artist_name} Collection"
        
        # Genre-based themes with descriptive modifiers
        if primary_genre and primary_genre != "Music":
            # Check for play count patterns
            if play_counts:
                avg_plays = sum(play_counts) / len(play_counts)
                if avg_plays < 2:  # Rarely played
                    return f"Rare {primary_genre}"
                elif avg_plays > 10:  # Frequently played
                    return f"Essential {primary_genre}"
            
            # Check for era patterns
            if years:
                year_span = max(years) - min(years)
                avg_year = sum(years) / len(years)
                
                if year_span <= 5:  # Tight era grouping
                    if avg_year >= 2020:
                        return f"Modern {primary_genre}"
                    elif avg_year >= 2010:
                        return f"Contemporary {primary_genre}"
                    elif avg_year >= 2000:
                        return f"2000s {primary_genre}"
                    elif avg_year >= 1990:
                        return f"90s {primary_genre}"
                    elif avg_year >= 1980:
                        return f"80s {primary_genre}"
                    else:
                        return f"Classic {primary_genre}"
                else:
                    # Wide era span - focus on genre
                    return f"{primary_genre} Anthology"
            
            # Pure genre name if no other patterns
            return f"{primary_genre} Collection"
        
        # Multi-genre themes
        if len(genre_counter) >= 2:
            top_genres = [self._clean_genre_name(g) for g, c in genre_counter.most_common(2)]
            if all(g and g != "Music" for g in top_genres):  # Both genres are valid
                return f"{top_genres[0]} & {top_genres[1]}"
        
        # When no genre info is available, create descriptive names
        if not genres:
            # Use artist diversity and year patterns for naming
            if len(artist_counter) >= 2:
                if years:
                    avg_year = sum(years) / len(years)
                    if avg_year >= 2015:
                        return "Modern Mix"
                    elif avg_year >= 2000:
                        return "2000s Mix"
                    elif avg_year >= 1990:
                        return "90s Mix"
                    else:
                        return "Classic Mix"
                else:
                    return "Various Artists"
            elif top_artist:
                return f"{top_artist[0]} Collection"
        
        # Year-based fallback only if no genre info
        if years:
            avg_year = sum(years) / len(years)
            if avg_year >= 2015:
                return "Modern Mix"
            elif avg_year >= 2000:
                return "2000s Mix"
            elif avg_year >= 1990:
                return "90s Mix"
            else:
                return "Classic Mix"
        
        # Final fallback
        cluster_id = cluster_info.get('id', 'Unknown').replace('theme_', '')
        return f"Collection #{cluster_id}"
    
    def _get_clean_genre_name(self, genre_counter: Counter) -> str:
        """Get clean, readable genre name from counter"""
        if not genre_counter:
            return "Music"
        
        top_genre = genre_counter.most_common(1)[0][0]
        return self._clean_genre_name(top_genre)
    
    def _clean_genre_name(self, genre: str) -> str:
        """Clean and standardize genre names"""
        if not genre or genre.lower() in ['unknown', 'other', '']:
            return "Music"
        
        # Handle very short or corrupted genre names
        if len(genre.strip()) <= 2:
            logger.warning(f"Very short genre name received: '{genre}' - defaulting to Music")
            return "Music"
        
        genre = genre.lower().strip()
        
        # Map common variations to standard names
        genre_mapping = {
            'electronic': 'Electronic',
            'electronica': 'Electronic',
            'edm': 'Electronic',
            'rock': 'Rock',
            'pop': 'Pop',
            'jazz': 'Jazz',
            'classical': 'Classical',
            'ambient': 'Ambient',
            'techno': 'Techno',
            'house': 'House',
            'indie': 'Indie',
            'indie rock': 'Indie Rock',
            'alternative': 'Alternative',
            'alternative rock': 'Alternative Rock',
            'alt rock': 'Alternative Rock',
            'metal': 'Metal',
            'folk': 'Folk',
            'experimental': 'Experimental',
            'acoustic': 'Acoustic',
            'hip hop': 'Hip Hop',
            'hip-hop': 'Hip Hop',
            'rap': 'Hip Hop',
            'country': 'Country',
            'blues': 'Blues',
            'r&b': 'R&B',
            'rnb': 'R&B',
            'soul': 'Soul',
            'funk': 'Funk',
            'reggae': 'Reggae',
            'punk': 'Punk',
            'hardcore': 'Hardcore',
            'post-rock': 'Post-Rock',
            'post rock': 'Post-Rock',
            'shoegaze': 'Shoegaze',
            'dream pop': 'Dream Pop',
            'synthwave': 'Synthwave',
            'synthpop': 'Synthpop',
            'new wave': 'New Wave',
            'darkwave': 'Darkwave',
            'industrial': 'Industrial',
            'noise': 'Noise',
            'drone': 'Drone'
        }
        
        # Check for exact matches first
        if genre in genre_mapping:
            return genre_mapping[genre]
        
        # Check for partial matches
        for key, value in genre_mapping.items():
            if key in genre:
                return value
        
        # Capitalize first letter of each word, but handle edge cases
        try:
            words = genre.split()
            if not words:
                return "Music"
            cleaned = ' '.join(word.capitalize() for word in words if word)
            return cleaned if cleaned else "Music"
        except Exception as e:
            logger.warning(f"Error cleaning genre name '{genre}': {e}")
            return "Music"
    
    def _analyze_enriched_features(self, tracks: List[Dict]) -> Dict[str, Any]:
        """Analyze enriched metadata to determine theme characteristics"""
        if not tracks:
            return {'primary_genre': 'Music', 'mood_dominant': False}
        
        # Collect enriched features
        moods = []
        genres = []
        styles = []
        energy_levels = []
        popularity_scores = []
        mb_tags = []
        lastfm_tags = []
        
        for track in tracks:
            # MusicBrainz features
            if track.get('mb_moods'):
                moods.extend(track['mb_moods'])
            if track.get('mb_genres'):
                genres.extend(track['mb_genres'])
            if track.get('mb_styles'):
                styles.extend(track['mb_styles'])
            if track.get('mb_tags'):
                mb_tags.extend(track['mb_tags'])
            
            # Last.fm features
            if track.get('lastfm_tags'):
                lastfm_tags.extend(track['lastfm_tags'])
            
            # Intelligent features
            if track.get('intelligent_mood'):
                moods.append(track['intelligent_mood'])
            if track.get('intelligent_energy'):
                energy_levels.append(track['intelligent_energy'])
            if track.get('intelligent_popularity'):
                popularity_scores.append(track['intelligent_popularity'])
        
        # Analyze patterns
        mood_counter = Counter(moods)
        genre_counter = Counter(genres + mb_tags + lastfm_tags)
        style_counter = Counter(styles)
        energy_counter = Counter(energy_levels)
        
        # Determine theme characteristics
        features = {
            'primary_genre': self._get_smart_genre(genre_counter),
            'primary_mood': self._get_primary_mood(mood_counter),
            'primary_style': self._get_primary_style(style_counter),
            'energy_level': self._get_energy_level(energy_counter),
            'mood_dominant': len(moods) > len(tracks) * 0.3,  # 30% of tracks have mood data
            'style_specific': self._is_style_specific(style_counter, len(tracks)),
            'energy_coherent': self._is_energy_coherent(energy_counter, len(tracks)),
            'discovery_theme': self._is_discovery_theme(popularity_scores),
            'era_specific': self._is_era_specific(tracks),
            'discovery_name': self._get_discovery_name(popularity_scores),
            'era_name': self._get_era_name(tracks),
            'style_name': self._get_style_name(genre_counter)
        }
        
        return features
    
    def _get_smart_genre(self, genre_counter: Counter) -> str:
        """Get smart genre classification"""
        if not genre_counter:
            return "Music"
        
        # Get the most common genre
        top_genre = genre_counter.most_common(1)[0][0].lower()
        
        # Use the same mapping as _clean_genre_name for consistency
        return self._clean_genre_name(top_genre)
    
    def _get_primary_mood(self, mood_counter: Counter) -> str:
        """Get primary mood with smart mapping"""
        if not mood_counter:
            return "Atmospheric"
        
        mood_mapping = {
            'chill': 'Chill',
            'relaxing': 'Relaxing',
            'energetic': 'Energetic',
            'upbeat': 'Upbeat',
            'dark': 'Dark',
            'melancholic': 'Melancholic',
            'happy': 'Happy',
            'aggressive': 'Aggressive',
            'peaceful': 'Peaceful',
            'intense': 'Intense'
        }
        
        top_mood = mood_counter.most_common(1)[0][0].lower()
        return mood_mapping.get(top_mood, top_mood.title())
    
    def _get_primary_style(self, style_counter: Counter) -> str:
        """Get primary style for style-specific themes"""
        if not style_counter:
            return ""
        
        # Filter out invalid styles (single letters, numbers, etc.)
        valid_styles = []
        for style, count in style_counter.most_common():
            style_clean = style.strip()
            # Only accept styles that are:
            # - More than 2 characters long
            # - Not just numbers
            # - Not single letters
            if len(style_clean) > 2 and not style_clean.isdigit() and style_clean.isalpha():
                valid_styles.append((style_clean, count))
        
        if not valid_styles:
            return ""
        
        top_style = valid_styles[0][0]
        return top_style.title()
    
    def _get_energy_level(self, energy_counter: Counter) -> str:
        """Get energy level description"""
        if not energy_counter:
            return "Mellow"
        
        energy_mapping = {
            'high': 'High Energy',
            'medium': 'Upbeat',
            'low': 'Mellow',
            'very_high': 'Intense',
            'very_low': 'Ambient'
        }
        
        top_energy = energy_counter.most_common(1)[0][0]
        return energy_mapping.get(top_energy, 'Balanced')
    
    def _is_style_specific(self, style_counter: Counter, track_count: int) -> bool:
        """Check if cluster is style-specific enough"""
        if not style_counter:
            return False
        
        # Filter out invalid styles first
        valid_styles = []
        for style, count in style_counter.most_common():
            style_clean = style.strip()
            if len(style_clean) > 2 and not style_clean.isdigit() and style_clean.isalpha():
                valid_styles.append((style_clean, count))
        
        if not valid_styles:
            return False
        
        top_style_count = valid_styles[0][1]
        return top_style_count > track_count * 0.4  # 40% of tracks share same style
    
    def _is_energy_coherent(self, energy_counter: Counter, track_count: int) -> bool:
        """Check if cluster has coherent energy level"""
        if not energy_counter:
            return False
        
        top_energy_count = energy_counter.most_common(1)[0][1]
        return top_energy_count > track_count * 0.5  # 50% of tracks share energy level
    
    def _is_discovery_theme(self, popularity_scores: List[float]) -> bool:
        """Check if this is a hidden gems/discovery theme"""
        if not popularity_scores:
            return False
        
        avg_popularity = sum(popularity_scores) / len(popularity_scores)
        return avg_popularity < 0.3  # Low average popularity = hidden gems
    
    def _is_era_specific(self, tracks: List[Dict]) -> bool:
        """Check if cluster is era-specific"""
        years = [int(track['year']) for track in tracks if track.get('year') and str(track['year']).isdigit()]
        if len(years) < len(tracks) * 0.5:
            return False
        
        year_range = max(years) - min(years)
        return year_range <= 10  # Span of 10 years or less
    
    def _get_discovery_name(self, popularity_scores: List[float]) -> str:
        """Get discovery theme name"""
        if not popularity_scores:
            return "Hidden Gems"
        
        avg_popularity = sum(popularity_scores) / len(popularity_scores)
        if avg_popularity < 0.1:
            return "Rare Finds"
        elif avg_popularity < 0.2:
            return "Deep Cuts"
        else:
            return "Hidden Gems"
    
    def _get_era_name(self, tracks: List[Dict]) -> str:
        """Get era-specific name"""
        years = [int(track['year']) for track in tracks if track.get('year') and str(track['year']).isdigit()]
        if not years:
            return "Classic"
        
        avg_year = sum(years) / len(years)
        if avg_year >= 2020:
            return "Modern"
        elif avg_year >= 2010:
            return "2010s"
        elif avg_year >= 2000:
            return "2000s"
        elif avg_year >= 1990:
            return "90s"
        elif avg_year >= 1980:
            return "80s"
        else:
            return "Classic"
    
    def _get_style_name(self, genre_counter: Counter) -> str:
        """Get style name for era-specific themes"""
        if not genre_counter:
            return "Music"
        
        top_genres = [genre for genre, count in genre_counter.most_common(2)]
        
        # Combine multiple genres intelligently
        if len(top_genres) >= 2:
            if 'rock' in top_genres[0].lower() and 'alternative' in top_genres[1].lower():
                return "Alternative Rock"
            elif 'electronic' in top_genres[0].lower():
                return "Electronic"
            elif 'indie' in str(top_genres).lower():
                return "Indie"
        
        return self._get_smart_genre(genre_counter)
    
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