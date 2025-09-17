"""
Configuration settings for the DICOM Album Explorer application
"""

import os
from urllib.parse import urlparse

class Config:
    """Base configuration"""
    APP_NAME = "DICOM Album Explorer"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')
    
    # File upload settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(BASE_DIR, "uploads")
    ALBUMS_FOLDER = os.environ.get('ALBUMS_FOLDER') or os.path.join(BASE_DIR, "albums")
    ALLOWED_EXTENSIONS = {'dcm'}
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))  # 100MB default
    
    # Cloud storage settings
    USE_CLOUD_STORAGE = os.environ.get('USE_CLOUD_STORAGE', 'false').lower() == 'true'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')
    AWS_S3_REGION = os.environ.get('AWS_S3_REGION', 'us-east-1')
    
    # Application settings
    ENABLE_USER_AUTH = os.environ.get('ENABLE_USER_AUTH', 'true').lower() == 'true'
    ENABLE_SHARING = os.environ.get('ENABLE_SHARING', 'true').lower() == 'true'
    
    # Database settings
    if not DATABASE_URL:
        DATABASE_PATH = os.path.join(BASE_DIR, "database", "dicom_albums.db")
        DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    
    @staticmethod
    def init_app(app):
        """Initialize app-specific configuration"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DATABASE_URL = os.environ.get('DEV_DATABASE_URL') or f"sqlite:///{os.path.join(Config.BASE_DIR, 'database', 'dicom_albums.db')}"

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Backwards compatibility - create directories
if not os.environ.get('USE_CLOUD_STORAGE', 'false').lower() == 'true':
    for directory in [Config.BASE_DIR, 
                     os.path.join(Config.BASE_DIR, "uploads"),
                     os.path.join(Config.BASE_DIR, "albums"), 
                     os.path.join(Config.BASE_DIR, "database")]:
        os.makedirs(directory, exist_ok=True)
