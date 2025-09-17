#!/usr/bin/env python3
"""
Production startup script for DICOM Album Explorer
"""
import os
from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Production settings
    app.run(host=host, port=port, debug=False)