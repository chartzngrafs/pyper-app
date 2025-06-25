"""
Audio Analysis Module for Dynamic Themes
Extracts advanced audio features using librosa for intelligent theme clustering
"""

import logging
import librosa
import numpy as np
import io
import tempfile
import os
from typing import Dict, Optional, Tuple
import requests
from threading import Lock
import time

logger = logging.getLogger('DynamicThemes.AudioAnalyzer')


class AudioAnalyzer:
    """Advanced audio analysis using librosa for theme discovery"""
    
    def __init__(self, config):
        self.config = config
        self.cache_lock = Lock()
        self.analysis_cache = {}
        
        # Audio analysis parameters
        self.sample_rate = 22050  # Standard rate for analysis
        self.duration = config.get_sample_duration()  # From config (45s default)
        
        logger.info(f"Audio analyzer initialized (sample duration: {self.duration}s)")
    
    def analyze_track_audio(self, sonic_client, track_id: str, track_info: Dict) -> Dict:
        """
        Analyze a track's audio features using Subsonic streaming
        
        Args:
            sonic_client: Subsonic/Navidrome client
            track_id: Track ID for streaming
            track_info: Track metadata dict
            
        Returns:
            Dict with audio features: bpm, energy, spectral_centroid, etc.
        """
        try:
            # TEMPORARILY DISABLED: Network-based audio analysis too slow (6+ seconds/track)
            # At 6s/track, analyzing 3,073 tracks would take over 5 hours!
            # TODO: Re-enable with either:
            #   1. Local file access (much faster)
            #   2. Parallel processing 
            #   3. Much shorter sample duration (5-10s)
            #   4. Smart sampling (only analyze representative tracks)
            logger.debug("Audio analysis temporarily disabled due to performance issues")
            return self._get_default_features()
            
            # Check cache first
            cache_key = f"{track_id}_{self.duration}s"
            if cache_key in self.analysis_cache:
                logger.debug(f"Using cached audio features for track {track_id}")
                return self.analysis_cache[cache_key]
            
            # Stream audio data from Navidrome
            audio_data = self._stream_track_audio(sonic_client, track_id)
            if audio_data is None:
                logger.warning(f"Failed to stream audio for track {track_id}")
                return self._get_default_features()
            
            # Analyze audio with librosa
            features = self._extract_audio_features(audio_data)
            
            # Add track metadata context
            features['track_duration'] = track_info.get('duration', 0)
            features['file_format'] = track_info.get('suffix', 'unknown')
            
            # Cache results
            with self.cache_lock:
                self.analysis_cache[cache_key] = features
            
            logger.debug(f"Analyzed audio features for track {track_id}: BPM={features.get('bpm', 0):.1f}")
            return features
            
        except Exception as e:
            logger.error(f"Audio analysis failed for track {track_id}: {e}")
            return self._get_default_features()
    
    def _stream_track_audio(self, sonic_client, track_id: str) -> Optional[bytes]:
        """Stream audio data from Navidrome server"""
        try:
            # Use Subsonic stream endpoint with quality/format control
            stream_params = {
                'id': track_id,
                'format': 'mp3',  # Force MP3 for compatibility
                'maxBitRate': 128,  # Lower bitrate for faster streaming
                'timeOffset': 0,    # Start from beginning
                'size': self.duration * 128 * 1000 // 8  # Rough size calculation
            }
            
            # Stream first portion of track for analysis with timeout
            response = sonic_client._make_request('stream', stream_params, stream=True)
            
            if response.status_code == 200:
                # Read limited amount of data (first N seconds) with timeout
                audio_data = b''
                max_size = 1024 * 1024 * 1  # Reduced to 1MB max for faster analysis
                bytes_read = 0
                
                # Add timeout to prevent hanging on slow streams
                start_time = time.time()
                timeout_seconds = 15  # 15 second timeout per track
                
                try:
                    for chunk in response.iter_content(chunk_size=8192):
                        # Check timeout
                        if time.time() - start_time > timeout_seconds:
                            logger.debug(f"Audio stream timeout for track {track_id}")
                            break
                            
                        audio_data += chunk
                        bytes_read += len(chunk)
                        
                        if bytes_read >= max_size:
                            break
                
                    logger.debug(f"Streamed {len(audio_data)} bytes for track {track_id} in {time.time() - start_time:.1f}s")
                    
                    # Ensure we have enough data for analysis (at least 100KB)
                    if len(audio_data) < 100 * 1024:
                        logger.debug(f"Insufficient audio data for track {track_id}: {len(audio_data)} bytes")
                        return None
                        
                    return audio_data
                    
                except Exception as e:
                    logger.debug(f"Error reading audio stream for track {track_id}: {e}")
                    return None
                    
            else:
                logger.debug(f"Stream request failed for track {track_id}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.debug(f"Audio streaming failed for track {track_id}: {e}")
            return None
    
    def _extract_audio_features(self, audio_data: bytes) -> Dict:
        """Extract comprehensive audio features using librosa"""
        try:
            # Create temporary file for librosa (it works better with files)
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Load audio with librosa
                y, sr = librosa.load(temp_path, sr=self.sample_rate, duration=self.duration)
                
                # Extract comprehensive features
                features = {}
                
                # 1. Tempo/BPM Analysis
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
                features['bpm'] = float(tempo)
                features['beat_strength'] = float(np.mean(librosa.onset.onset_strength(y=y, sr=sr)))
                
                # 2. Energy Analysis
                rms = librosa.feature.rms(y=y)[0]
                features['energy'] = float(np.mean(rms))
                features['energy_variance'] = float(np.var(rms))
                
                # 3. Spectral Features
                spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
                features['spectral_centroid'] = float(np.mean(spectral_centroid))
                features['spectral_brightness'] = float(np.percentile(spectral_centroid, 75))
                
                # 4. Harmonic/Percussive Separation
                y_harmonic, y_percussive = librosa.effects.hpss(y)
                features['harmonicity'] = float(np.mean(librosa.feature.rms(y=y_harmonic)[0]))
                features['percussiveness'] = float(np.mean(librosa.feature.rms(y=y_percussive)[0]))
                
                # 5. Zero Crossing Rate (rhythm/texture)
                zcr = librosa.feature.zero_crossing_rate(y)[0]
                features['zero_crossing_rate'] = float(np.mean(zcr))
                
                # 6. Chroma Features (key/harmony)
                chroma = librosa.feature.chroma_stft(y=y, sr=sr)
                features['chroma_strength'] = float(np.mean(np.max(chroma, axis=0)))
                
                # 7. Quantization Detection (electronic music indicator)
                # Look for very regular beat patterns
                beat_times = librosa.frames_to_time(beats, sr=sr)
                if len(beat_times) > 3:
                    beat_intervals = np.diff(beat_times)
                    beat_regularity = 1.0 - np.std(beat_intervals) / np.mean(beat_intervals)
                    features['quantization'] = float(max(0.0, min(1.0, beat_regularity)))
                else:
                    features['quantization'] = 0.0
                
                # 8. Mood Indicators
                # High energy + high tempo = energetic
                # Low energy + slow tempo = chill
                energy_norm = min(1.0, features['energy'] * 10)  # Normalize energy
                tempo_norm = min(1.0, features['bpm'] / 180.0)   # Normalize tempo
                
                features['mood_energetic'] = float((energy_norm + tempo_norm) / 2.0)
                features['mood_chill'] = float(1.0 - features['mood_energetic'])
                
                logger.debug(f"Extracted {len(features)} audio features successfully")
                return features
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Librosa analysis failed: {e}")
            return self._get_default_features()
    
    def _get_default_features(self) -> Dict:
        """Return default/neutral audio features when analysis fails"""
        return {
            'bpm': 120.0,
            'energy': 0.5,
            'spectral_centroid': 1500.0,
            'beat_strength': 0.5,
            'energy_variance': 0.1,
            'spectral_brightness': 2000.0,
            'harmonicity': 0.5,
            'percussiveness': 0.5,
            'zero_crossing_rate': 0.1,
            'chroma_strength': 0.5,
            'quantization': 0.0,
            'mood_energetic': 0.5,
            'mood_chill': 0.5,
            'track_duration': 0,
            'file_format': 'unknown'
        }
    
    def get_feature_vector(self, features: Dict) -> np.ndarray:
        """Convert audio features to normalized vector for clustering"""
        # Define feature order and normalization
        feature_keys = [
            'bpm', 'energy', 'spectral_centroid', 'beat_strength',
            'harmonicity', 'percussiveness', 'quantization',
            'mood_energetic', 'mood_chill'
        ]
        
        # Create feature vector
        vector = []
        for key in feature_keys:
            value = features.get(key, 0.5)
            
            # Normalize different feature types
            if key == 'bpm':
                normalized = min(1.0, value / 200.0)  # Max 200 BPM
            elif key == 'spectral_centroid':
                normalized = min(1.0, value / 4000.0)  # Max 4kHz
            else:
                normalized = min(1.0, max(0.0, value))  # Clamp 0-1
            
            vector.append(normalized)
        
        return np.array(vector, dtype=np.float32)
    
    def clear_cache(self):
        """Clear audio analysis cache"""
        with self.cache_lock:
            self.analysis_cache.clear()
        logger.info("Audio analysis cache cleared")
    
    def get_cache_size(self) -> int:
        """Get current cache size in number of tracks"""
        return len(self.analysis_cache) 