import os
import json
import sqlite3
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from urllib.parse import urlparse

class DatabaseManager:
    """
    Class for managing the database (SQLite for development, PostgreSQL for production)
    """
    
    def __init__(self, database_url=None):
        """Initialize database manager"""
        self.database_url = database_url or os.environ.get('DATABASE_URL', 'sqlite:///./database/dicom_albums.db')
        
        # Handle Heroku postgres URL format
        if self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql://')
        
        # Parse URL to determine database type
        parsed_url = urlparse(self.database_url)
        self.db_type = parsed_url.scheme
        
        # Setup engine based on database type
        if self.db_type == 'sqlite':
            # For SQLite, create directory if it doesn't exist
            if '///' in self.database_url:
                db_path = self.database_url.split('///', 1)[1]
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            self.engine = create_engine(
                self.database_url,
                poolclass=StaticPool,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 20
                }
            )
        else:
            # For PostgreSQL and other databases
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300
            )
        
        self.initialize_db()
    
    def get_connection(self):
        """Get a new database connection"""
        if self.db_type == 'sqlite':
            # For backwards compatibility with SQLite
            db_path = self.database_url.split('///', 1)[1] if '///' in self.database_url else ':memory:'
            return sqlite3.connect(db_path)
        else:
            # For other databases, return SQLAlchemy connection
            return self.engine.connect()
    
    def initialize_db(self):
        """Create database tables if they don't exist"""
        if self.db_type == 'sqlite':
            self._initialize_sqlite_db()
        else:
            self._initialize_sqlalchemy_db()
    
    def _initialize_sqlite_db(self):
        """Initialize SQLite database (backwards compatibility)"""
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
                share_url TEXT,
                is_public BOOLEAN DEFAULT 0,
                owner_id TEXT
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
                result_count INTEGER,
                user_id TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_date TEXT,
                is_active BOOLEAN DEFAULT 1
            )
            ''')
    
    def _initialize_sqlalchemy_db(self):
        """Initialize database using SQLAlchemy (PostgreSQL, etc.)"""
        with self.engine.connect() as conn:
            # Use appropriate SQL syntax for PostgreSQL
            conn.execute(text('''
            CREATE TABLE IF NOT EXISTS albums (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                creator VARCHAR(255),
                created_date TIMESTAMP,
                file_count INTEGER,
                share_url VARCHAR(500),
                is_public BOOLEAN DEFAULT FALSE,
                owner_id VARCHAR(255)
            )
            '''))

            conn.execute(text('''
            CREATE TABLE IF NOT EXISTS files (
                id SERIAL PRIMARY KEY,
                album_id VARCHAR(255),
                file_path VARCHAR(500),
                original_path VARCHAR(500),
                patient_id VARCHAR(255),
                patient_name VARCHAR(255),
                study_instance_uid VARCHAR(255),
                series_instance_uid VARCHAR(255),
                sop_instance_uid VARCHAR(255),
                modality VARCHAR(50),
                study_date VARCHAR(50),
                metadata TEXT,
                FOREIGN KEY (album_id) REFERENCES albums (id) ON DELETE CASCADE
            )
            '''))
            
            conn.execute(text('''
            CREATE TABLE IF NOT EXISTS query_history (
                id SERIAL PRIMARY KEY,
                query TEXT,
                executed_date TIMESTAMP,
                result_count INTEGER,
                user_id VARCHAR(255)
            )
            '''))
            
            conn.execute(text('''
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_date TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
            '''))
            
            conn.commit()
    
    def save_album(self, album_metadata, file_metadata_list):
        """Save album and file metadata to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO albums (id, name, description, creator, created_date, file_count, share_url, is_public, owner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                album_metadata['id'],
                album_metadata['name'],
                album_metadata['description'],
                album_metadata['creator'],
                album_metadata['created_date'],
                album_metadata['file_count'],
                album_metadata['share_url'],
                album_metadata.get('is_public', False),
                album_metadata.get('owner_id')
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
    
    # User management methods
    def create_user(self, user_id, username, email, password_hash):
        """Create a new user"""
        with self.get_connection() as conn:
            if self.db_type == 'sqlite':
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO users (id, username, email, password_hash, created_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    username,
                    email,
                    password_hash,
                    datetime.now().isoformat(),
                    True
                ))
            else:
                conn.execute(text('''
                INSERT INTO users (id, username, email, password_hash, created_date, is_active)
                VALUES (:id, :username, :email, :password_hash, :created_date, :is_active)
                '''), {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'password_hash': password_hash,
                    'created_date': datetime.now(),
                    'is_active': True
                })
                conn.commit()
    
    def get_user_by_username(self, username):
        """Get user by username"""
        with self.get_connection() as conn:
            if self.db_type == 'sqlite':
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                user = cursor.fetchone()
                if user:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, user))
            else:
                result = conn.execute(text('SELECT * FROM users WHERE username = :username'), {'username': username})
                row = result.fetchone()
                if row:
                    return dict(row._mapping)
        return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        with self.get_connection() as conn:
            if self.db_type == 'sqlite':
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
                user = cursor.fetchone()
                if user:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, user))
            else:
                result = conn.execute(text('SELECT * FROM users WHERE email = :email'), {'email': email})
                row = result.fetchone()
                if row:
                    return dict(row._mapping)
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        with self.get_connection() as conn:
            if self.db_type == 'sqlite':
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                user = cursor.fetchone()
                if user:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, user))
            else:
                result = conn.execute(text('SELECT * FROM users WHERE id = :user_id'), {'user_id': user_id})
                row = result.fetchone()
                if row:
                    return dict(row._mapping)
        return None
    
    def get_user_albums(self, user_id):
        """Get all albums owned by a specific user"""
        with self.get_connection() as conn:
            if self.db_type == 'sqlite':
                query = 'SELECT * FROM albums WHERE owner_id = ? ORDER BY created_date DESC'
                df = pd.read_sql_query(query, conn, params=(user_id,))
            else:
                query = 'SELECT * FROM albums WHERE owner_id = :user_id ORDER BY created_date DESC'
                df = pd.read_sql_query(query, conn, params={'user_id': user_id})
            
            return df.to_dict('records') if not df.empty else []
    
    def get_public_albums(self):
        """Get all public albums"""
        with self.get_connection() as conn:
            if self.db_type == 'sqlite':
                query = 'SELECT * FROM albums WHERE is_public = 1 ORDER BY created_date DESC'
            else:
                query = 'SELECT * FROM albums WHERE is_public = TRUE ORDER BY created_date DESC'
            df = pd.read_sql_query(query, conn)
            
            return df.to_dict('records') if not df.empty else []
    
    def update_album_public_status(self, album_id, is_public):
        """Update the public status of an album"""
        with self.get_connection() as conn:
            if self.db_type == 'sqlite':
                cursor = conn.cursor()
                cursor.execute('UPDATE albums SET is_public = ? WHERE id = ?', (1 if is_public else 0, album_id))
            else:
                conn.execute(text('UPDATE albums SET is_public = :is_public WHERE id = :album_id'), 
                           {'is_public': bool(is_public), 'album_id': album_id})
                conn.commit()
    
    def update_album_share_url(self, album_id, share_url):
        """Update the share URL of an album"""
        with self.get_connection() as conn:
            if self.db_type == 'sqlite':
                cursor = conn.cursor()
                cursor.execute('UPDATE albums SET share_url = ? WHERE id = ?', (share_url, album_id))
            else:
                conn.execute(text('UPDATE albums SET share_url = :share_url WHERE id = :album_id'), 
                           {'share_url': share_url, 'album_id': album_id})
                conn.commit()
