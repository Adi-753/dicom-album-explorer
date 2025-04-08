# DICOM Album Explorer

This is a web application for organizing and sharing DICOM images. This tool allows users to create shareable "albums" from locally stored DICOM images by querying metadata and also allowing user to make advanced queries. The languages and technologies used in this project are: HTML, CSS, JavaScript, Python, Flask, SQLite, PyDICOM, BootStrap 5.

## Features

- Upload DICOM files or scan a local directory
- View and extract DICOM metadata
- Simple and advanced querying capabilities
- Create albums based on query results
- Share albums via unique URLs
- View DICOM images with windowing controls
- Download original DICOM files from albums
- Query history tracking
- Customizable image windowing

## Architecture

This application is built with the following technologies:
- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **Database**: SQLite (local storage)
- **DICOM Processing**: PyDICOM

## Procedure for running it on your own Device:

### Prerequisites

- Python 3.7 or higher
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dicom-album-explorer.git
cd dicom-album-explorer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate.bat
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Procedure for how to use the website: 

### Loading DICOM Files

- **Upload Files**: Use the upload form to select and upload DICOM (.dcm) files from your locally stored DICOM images.
- **Scan Directory**: Enter a local directory path to scan for DICOM files.

### Creating Albums

1. Load DICOM files using one of the methods above
2. Use the simple query interface to filter files based on a single criterion
3. If you want then use the advanced query interface(near home button) for more complex filtering with multiple conditions
4. Fill in album details (name, description, creator)
5. Create the album
6. If required share the unique album URL with collaborators

### Viewing Albums

- Albums show thumbnails and metadata for included images
- Use the image viewer to visualize DICOM images
- Adjust windowing parameters to optimize visualization
- Download original DICOM files as needed


## Acknowledgments

- [PyDICOM](https://pydicom.github.io/) for DICOM file handling
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Bootstrap](https://getbootstrap.com/) for UI components

Note: For downloading DICOM images you can use the folder provided and access through the path "C:\your_path\Anonymized_20250408\series-00000" or use any of the DICOM images available on the INTERNET.