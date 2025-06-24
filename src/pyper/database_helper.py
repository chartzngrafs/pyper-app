"""
Database Helper Module for Pyper Music Player
Handles access to Navidrome's SQLite database for play counts and stats
"""

import os
import sqlite3
import subprocess
import tempfile
import shutil
import logging

# Get logger
logger = logging.getLogger('Pyper')


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
    
    def get_all_tracks_for_themes(self, limit=None):
        """Get all tracks with metadata for dynamic theme analysis"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    mf.id,
                    mf.title,
                    mf.artist,
                    mf.album,
                    mf.album_artist,
                    mf.genre,
                    mf.year,
                    mf.duration,
                    mf.track_number,
                    mf.disc_number,
                    mf.path,
                    mf.created_at,
                    mf.updated_at,
                    COALESCE(an.play_count, 0) as play_count,
                    an.play_date as last_played,
                    COALESCE(an.rating, 0) as rating
                FROM media_file mf
                LEFT JOIN annotation an ON mf.id = an.item_id AND an.item_type = 'media_file'
                ORDER BY mf.artist, mf.album, mf.track_number
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            
            results = []
            for row in cursor.fetchall():
                (track_id, title, artist, album, album_artist, genre, year, 
                 duration, track_number, disc_number, path, created_at, updated_at,
                 play_count, last_played, rating) = row
                
                results.append({
                    'id': track_id,
                    'title': title,
                    'artist': artist or album_artist,
                    'album': album,
                    'genre': genre,
                    'year': year,
                    'duration': duration,
                    'trackNumber': track_number,
                    'discNumber': disc_number,
                    'path': path,
                    'created': created_at,
                    'updated': updated_at,
                    'playCount': play_count or 0,
                    'lastPlayed': last_played,
                    'rating': rating or 0
                })
            
            conn.close()
            logger.info(f"Retrieved {len(results)} tracks for theme analysis")
            return results
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            conn.close()
            return [] 