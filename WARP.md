# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

DICOM Album Explorer is a Flask web application for organizing and sharing DICOM medical images. It allows users to create shareable "albums" from locally stored DICOM files using metadata queries and provides advanced querying capabilities.

### Tech Stack
- **Backend**: Flask (Python), SQLite database
- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **DICOM Processing**: PyDICOM library
- **Dependencies**: pandas, pillow, numpy, matplotlib, sqlalchemy, shortuuid

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment (Windows)
python -m venv venv
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Start development server
python app.py

# Application runs at http://localhost:5000
```

### Testing Individual Components
```bash
# Test DICOM processing functionality
python -c "from utils.dicom_processor import DICOMProcessor; print(DICOMProcessor.scan_directory('path/to/dicom/files'))"

# Test database connection
python -c "from database.db import DatabaseManager; db = DatabaseManager(); print('Database initialized successfully')"
```

## Architecture Overview

The application follows a modular Flask architecture with clear separation of concerns:

### Core Components

**Flask Application (`app.py`)**
- Main Flask routes and request handlers
- Coordinates between utility modules and database
- Manages global DICOM data state (`current_dicom_data`)
- Handles file uploads, directory scanning, and album creation

**Utils Package (`utils/`)**
- `dicom_processor.py`: DICOM file handling, metadata extraction, image conversion with windowing
- `album_manager.py`: Album creation, file management, metadata persistence  
- `query_engine.py`: Simple and advanced querying with multiple operators (=, !=, >, <, contains, regex)

**Database Layer (`database/db.py`)**
- SQLite database management with thread-safe connections
- Tables: albums, files, query_history
- Handles album metadata storage and query history tracking

**Templates (`templates/`)**
- Bootstrap 5-based responsive UI
- `index.html`: Main interface with upload, scan, query, and album creation
- `album.html`: Album viewing with DICOM image display and windowing controls
- `advanced_query.html`: Complex multi-condition query interface

### Key Data Flow Patterns

**DICOM Processing Pipeline**
1. Upload files or scan directory → `DICOMProcessor.scan_directory()`
2. Extract metadata → `DICOMProcessor.extract_metadata()`  
3. Store in global DataFrame → `current_dicom_data`
4. Query operations → `QueryEngine.simple_query()` or `QueryEngine.advanced_query()`
5. Create albums → `AlbumManager.create_album()` with file copying and metadata storage

**Query System Architecture**
- Simple queries: Single field, value, operator combinations
- Advanced queries: Multiple conditions with AND/OR operators
- Query history tracking in SQLite for analytics
- Results limited to first 100 records for performance

**Album Management**
- File-based storage structure: `albums/{album_id}/dicom/` for DICOM files
- JSON metadata files: `albums/{album_id}/metadata.json`
- CSV file listings: `albums/{album_id}/files.csv`
- Database mirrors file system for efficient querying

### Configuration

**Key Settings (`config.py`)**
- Upload folder: `uploads/`
- Albums storage: `albums/`
- Database path: `database/dicom_albums.db`
- File size limit: 100MB
- Allowed extensions: `.dcm` only

**Important Flask Config**
- Debug mode enabled by default
- File uploads handled with secure filename sanitization
- Session management with secret key

## Working with DICOM Files

### DICOM Metadata Fields
The application extracts standard DICOM tags:
- Patient info: PatientID, PatientName, PatientBirthDate, PatientSex
- Study info: StudyInstanceUID, StudyDescription, StudyDate, StudyTime  
- Series info: SeriesInstanceUID, SeriesDescription, Modality
- Instance info: SOPInstanceUID, InstanceNumber, SliceLocation
- Imaging: ImageType, PixelSpacing, WindowCenter, WindowWidth

### Image Processing Features
- Automatic DICOM to PNG conversion with base64 encoding
- Windowing controls for medical image display optimization
- Handles multi-value DICOM fields and various data types
- Pixel array normalization for consistent visualization

### Query Capabilities
- **Operators**: =, !=, >, <, >=, <=, contains, starts_with, ends_with, regex
- **Data types**: Automatic string/numeric conversion
- **Complex queries**: Multiple conditions with AND/OR logic
- **Date range queries**: YYYYMMDD format handling
- **Modality filtering**: Multiple modality selection

## Database Schema

**Albums Table**
- id (TEXT PRIMARY KEY): Unique album identifier
- name, description, creator: Album metadata
- created_date: ISO format timestamp
- file_count, share_url: Album statistics

**Files Table**
- album_id (FOREIGN KEY): Links to albums
- file_path, original_path: File location tracking
- DICOM identifiers: patient_id, study_instance_uid, series_instance_uid, sop_instance_uid
- metadata (TEXT): Full DICOM metadata as JSON

**Query_History Table**
- query, executed_date, result_count: Query analytics and debugging

## Development Patterns

### Error Handling
- DICOM file validation with pydicom error catching
- Database operations wrapped in connection management
- File system operations with existence checks
- Frontend AJAX error display with Bootstrap alerts

### Security Considerations
- File upload validation (extension and content)
- Secure filename generation with werkzeug
- SQL injection prevention with parameterized queries
- No authentication system (local development focused)

### Performance Optimizations
- Global DataFrame caching for repeated queries
- Query result limiting (100 records)
- Database connection pooling per thread
- Lazy loading of DICOM pixel data

## Common Development Tasks

### Adding New DICOM Fields
1. Update `DICOMProcessor.extract_metadata()` fields list
2. Modify database schema in `db.py` if needed for indexing
3. Update frontend templates to display new fields

### Extending Query Operators  
1. Add operator logic in `QueryEngine.simple_query()`
2. Update frontend dropdown in templates
3. Add operator description in `generate_query_summary()`

### Album Feature Extensions
1. Modify `AlbumManager.create_album()` for new metadata
2. Update database schema and album storage structure
3. Extend album viewing templates and routes

### Frontend Customization
- Bootstrap 5 components used throughout
- JavaScript handles AJAX requests and dynamic UI updates
- CSS customizations in referenced but not included `static/css/main.css`