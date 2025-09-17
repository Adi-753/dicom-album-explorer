"""
User authentication and session management for DICOM Album Explorer
"""

import uuid
from datetime import datetime
from flask import session, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from functools import wraps
from database.db import DatabaseManager

bcrypt = Bcrypt()

class User(UserMixin):
    """User model for Flask-Login"""
    
    def __init__(self, user_id, username, email, password_hash=None, created_date=None, is_active=True):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_date = created_date
        self.is_active = is_active
    
    def check_password(self, password):
        """Check if provided password matches user's password hash"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    @staticmethod
    def create_password_hash(password):
        """Create password hash"""
        return bcrypt.generate_password_hash(password).decode('utf-8')
    
    @classmethod
    def from_db_record(cls, record):
        """Create User instance from database record"""
        if not record:
            return None
        return cls(
            user_id=record['id'],
            username=record['username'],
            email=record['email'],
            password_hash=record['password_hash'],
            created_date=record['created_date'],
            is_active=record['is_active']
        )

class AuthManager:
    """Manages user authentication and registration"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def register_user(self, username, email, password):
        """Register a new user"""
        try:
            # Check if user already exists
            if self.db_manager.get_user_by_username(username):
                return False, "Username already exists"
            
            if self.db_manager.get_user_by_email(email):
                return False, "Email already registered"
            
            # Create new user
            user_id = str(uuid.uuid4())
            password_hash = User.create_password_hash(password)
            
            self.db_manager.create_user(user_id, username, email, password_hash)
            
            return True, "User registered successfully"
        
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def authenticate_user(self, username, password):
        """Authenticate user with username and password"""
        try:
            user_record = self.db_manager.get_user_by_username(username)
            if not user_record:
                return None, "Invalid username or password"
            
            user = User.from_db_record(user_record)
            if not user or not user.is_active:
                return None, "Account is inactive"
            
            if not user.check_password(password):
                return None, "Invalid username or password"
            
            return user, "Login successful"
        
        except Exception as e:
            return None, f"Authentication failed: {str(e)}"
    
    def get_user_by_id(self, user_id):
        """Get user by ID for Flask-Login user_loader"""
        try:
            user_record = self.db_manager.get_user_by_id(user_id)
            return User.from_db_record(user_record)
        except Exception:
            return None

def auth_required(f):
    """Decorator to require authentication for routes when auth is enabled"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        if current_app.config.get('ENABLE_USER_AUTH', True):
            if not current_user.is_authenticated:
                return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    """Decorator to require ownership of the album"""
    @wraps(f)
    def decorated_function(album_id, *args, **kwargs):
        from flask import current_app
        if current_app.config.get('ENABLE_USER_AUTH', True):
            if not current_user.is_authenticated:
                return redirect(url_for('login', next=request.url))
            
            # Check album ownership
            db_manager = DatabaseManager()
            album = db_manager.get_album(album_id)
            if not album:
                flash('Album not found', 'error')
                return redirect(url_for('index'))
            
            if album.get('owner_id') != current_user.id:
                flash('Access denied. You can only access your own albums.', 'error')
                return redirect(url_for('index'))
        
        return f(album_id, *args, **kwargs)
    return decorated_function