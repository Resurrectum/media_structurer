'''
Duplicate Detection Database Module

Manages SQLite database for storing perceptual hashes and metadata of media files.
'''

import sqlite3
import os
from typing import Optional, List, Tuple, Dict
from datetime import datetime


class DuplicateDetectionDB:
    '''
    Database manager for media file perceptual hashes and metadata.
    '''

    def __init__(self, db_path: str = 'media_hashes.db'):
        '''
        @brief Initialize database connection and create schema if needed
        @param db_path Path to SQLite database file
        '''
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self):
        '''
        @brief Create database schema with tables and indexes
        '''
        cursor = self.conn.cursor()

        # Main table for media hashes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_hashes (
                file_path TEXT PRIMARY KEY,
                perceptual_hash TEXT NOT NULL,
                file_size INTEGER,
                modification_time REAL,
                media_type TEXT,
                width INTEGER,
                height INTEGER,
                duration REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Index for fast duplicate lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_perceptual_hash
            ON media_hashes(perceptual_hash)
        ''')

        self.conn.commit()

    def file_exists_in_db(self, file_path: str, modification_time: float) -> bool:
        '''
        @brief Check if file already exists in DB with same modification time
        @param file_path Absolute path to file
        @param modification_time File modification timestamp
        @return True if file exists with same mtime, False otherwise
        '''
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT modification_time FROM media_hashes
            WHERE file_path = ?
        ''', (file_path,))

        result = cursor.fetchone()
        if result is None:
            return False

        return abs(result[0] - modification_time) < 0.001

    def insert_hash(self, file_path: str, perceptual_hash: str,
                   file_size: int, modification_time: float, media_type: str,
                   width: Optional[int] = None, height: Optional[int] = None,
                   duration: Optional[float] = None):
        '''
        @brief Insert or replace hash entry for a file
        @param file_path Absolute path to file
        @param perceptual_hash Perceptual hash string
        @param file_size File size in bytes
        @param modification_time File modification timestamp
        @param media_type 'image' or 'video'
        @param width Image/video width in pixels
        @param height Image/video height in pixels
        @param duration Video duration in seconds (None for images)
        '''
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO media_hashes
            (file_path, perceptual_hash, file_size, modification_time,
             media_type, width, height, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (file_path, perceptual_hash, file_size, modification_time,
              media_type, width, height, duration))

        self.conn.commit()

    def get_duplicates(self) -> List[Tuple[str, List[Dict]]]:
        '''
        @brief Find all groups of duplicate files (same perceptual hash)
        @return List of tuples (hash, [file_info_dicts])
        '''
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT perceptual_hash, COUNT(*) as count
            FROM media_hashes
            GROUP BY perceptual_hash
            HAVING count > 1
            ORDER BY count DESC
        ''')

        duplicate_hashes = cursor.fetchall()

        results = []
        for row in duplicate_hashes:
            phash = row[0]
            cursor.execute('''
                SELECT file_path, file_size, media_type, width, height, duration
                FROM media_hashes
                WHERE perceptual_hash = ?
                ORDER BY file_size DESC
            ''', (phash,))

            files = [dict(file_row) for file_row in cursor.fetchall()]
            results.append((phash, files))

        return results

    def get_stats(self) -> Dict[str, int]:
        '''
        @brief Get database statistics
        @return Dictionary with total files, images, videos, duplicates count
        '''
        cursor = self.conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM media_hashes')
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM media_hashes WHERE media_type = 'image'")
        images = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM media_hashes WHERE media_type = 'video'")
        videos = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(DISTINCT perceptual_hash)
            FROM media_hashes
        ''')
        unique_hashes = cursor.fetchone()[0]

        duplicates = total - unique_hashes

        return {
            'total_files': total,
            'images': images,
            'videos': videos,
            'unique_hashes': unique_hashes,
            'duplicate_files': duplicates
        }

    def cleanup_deleted_files(self) -> int:
        '''
        @brief Remove database entries for files that no longer exist on disk
        @return Number of stale entries removed
        '''
        cursor = self.conn.cursor()
        cursor.execute('SELECT file_path FROM media_hashes')

        all_paths = [row[0] for row in cursor.fetchall()]
        deleted_paths = []

        for file_path in all_paths:
            if not os.path.exists(file_path):
                deleted_paths.append(file_path)

        # Remove stale entries
        if deleted_paths:
            cursor.executemany(
                'DELETE FROM media_hashes WHERE file_path = ?',
                [(path,) for path in deleted_paths]
            )
            self.conn.commit()

        return len(deleted_paths)

    def rebuild_database(self):
        '''
        @brief Clear all entries from the database (keeps schema intact)
        '''
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM media_hashes')
        self.conn.commit()

    def close(self):
        '''
        @brief Close database connection
        '''
        self.conn.close()
