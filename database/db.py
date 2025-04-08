import os
import json
import sqlite3
import pandas as pd
from datetime import datetime

class DatabaseManager:
    """
    Class for managing the local database
    """
    
    def __init__(self, db_path='./database/dicom_albums.db'):
        """Initialize database manager"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.initialize_db()
    
    def get_connection(self):
        """Get a new database connection for the current thread"""
        return sqlite3.connect(self.db_path)
    
    def initialize_db(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS albums (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                creator TEXT,
                created_date TEXT,
                file_count INTEGER,
                share_url TEXT
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                album_id TEXT,
                file_path TEXT,
                original_path TEXT,
                patient_id TEXT,
                patient_name TEXT,
                study_instance_uid TEXT,
                series_instance_uid TEXT,
                sop_instance_uid TEXT,
                modality TEXT,
                study_date TEXT,
                metadata TEXT,
                FOREIGN KEY (album_id) REFERENCES albums (id) ON DELETE CASCADE
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                executed_date TEXT,
                result_count INTEGER
            )
            ''')
    
    def save_album(self, album_metadata, file_metadata_list):
        """Save album and file metadata to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO albums (id, name, description, creator, created_date, file_count, share_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                album_metadata['id'],
                album_metadata['name'],
                album_metadata['description'],
                album_metadata['creator'],
                album_metadata['created_date'],
                album_metadata['file_count'],
                album_metadata['share_url']
            ))
            
            for file_metadata in file_metadata_list:
                metadata_json = json.dumps({k: v for k, v in file_metadata.items() 
                                           if k not in ['AlbumFilePath', 'OriginalFilePath']})
                
                cursor.execute('''
                INSERT INTO files (
                    album_id, file_path, original_path, patient_id, patient_name,
                    study_instance_uid, series_instance_uid, sop_instance_uid,
                    modality, study_date, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    album_metadata['id'],
                    file_metadata.get('AlbumFilePath'),
                    file_metadata.get('OriginalFilePath'),
                    file_metadata.get('PatientID'),
                    file_metadata.get('PatientName'),
                    file_metadata.get('StudyInstanceUID'),
                    file_metadata.get('SeriesInstanceUID'),
                    file_metadata.get('SOPInstanceUID'),
                    file_metadata.get('Modality'),
                    file_metadata.get('StudyDate'),
                    metadata_json
                ))
    
    def get_album(self, album_id):
        """Get album metadata from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM albums WHERE id = ?', (album_id,))
            album = cursor.fetchone()
            
            if album:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, album))
        return None
    
    def get_album_files(self, album_id):
        """Get files in an album from database"""
        with self.get_connection() as conn:
            query = 'SELECT * FROM files WHERE album_id = ?'
            df = pd.read_sql_query(query, conn, params=(album_id,))
            
            # Parse metadata JSON
            if not df.empty and 'metadata' in df.columns:
                metadata_dfs = []
                for i, row in df.iterrows():
                    metadata = json.loads(row['metadata'])
                    metadata_df = pd.json_normalize(metadata)
                    metadata_df['file_id'] = row['id']
                    metadata_dfs.append(metadata_df)
                
                if metadata_dfs:
                    metadata_combined = pd.concat(metadata_dfs)
                    df = df.merge(metadata_combined, left_on='id', right_on='file_id')
            
            return df
    
    def get_all_albums(self):
        """Get all albums from database"""
        with self.get_connection() as conn:
            query = 'SELECT * FROM albums ORDER BY created_date DESC'
            df = pd.read_sql_query(query, conn)
            
            return df.to_dict('records') if not df.empty else []
    
    def delete_album(self, album_id):
        """Delete album from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM files WHERE album_id = ?', (album_id,))
            cursor.execute('DELETE FROM albums WHERE id = ?', (album_id,))
    
    def save_query_history(self, query_text, result_count):
        """Save query to history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO query_history (query, executed_date, result_count)
            VALUES (?, ?, ?)
            ''', (
                query_text,
                datetime.now().isoformat(),
                result_count
            ))
    
    def get_query_history(self, limit=20):
        """Get recent query history"""
        with self.get_connection() as conn:
            query = 'SELECT * FROM query_history ORDER BY executed_date DESC LIMIT ?'
            df = pd.read_sql_query(query, conn, params=(limit,))
            
            return df.to_dict('records') if not df.empty else []
        
        