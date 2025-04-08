# This will make all the directories for the project.

import os

structure = {
    "dicom_album_explorer": [
        "static/css",
        "static/js",
        "templates",
        "utils",
        "database"
    ]
}

files = [
    "app.py",
    "static/css/main.css",
    "static/js/main.js",
    "templates/index.html",
    "templates/album.html",
    "templates/advanced_query.html",
    "utils/__init__.py",
    "utils/dicom_processor.py",
    "utils/album_manager.py",
    "utils/query_engine.py",
    "database/db.py",
    "config.py",
    "requirements.txt",
    "README.md"
]

base = "."

for root, folders in structure.items():
    for folder in folders:
        path = os.path.join(base, root, folder)
        os.makedirs(path, exist_ok=True)

for file in files:
    path = os.path.join(base, "dicom_album_explorer", file)
    with open(path, 'w') as f:
        f.write("")  
