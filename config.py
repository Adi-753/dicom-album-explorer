"""
Configuration settings for the DICOM Album Explorer application
"""

import os

APP_NAME = "DICOM Album Explorer"
DEBUG = True
SECRET_KEY = "your-secret-key-here"  


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALBUMS_FOLDER = os.path.join(BASE_DIR, "albums")
ALLOWED_EXTENSIONS = {"dcm"}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max upload


DATABASE_PATH = os.path.join(BASE_DIR, "database", "dicom_albums.db")

for directory in [UPLOAD_FOLDER, ALBUMS_FOLDER, os.path.dirname(DATABASE_PATH)]:
    os.makedirs(directory, exist_ok=True)