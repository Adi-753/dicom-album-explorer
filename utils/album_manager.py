import os
import json
import shutil
import pandas as pd
import shortuuid
from datetime import datetime
import pydicom
from .dicom_processor import DICOMProcessor

class AlbumManager:
    """
    Class for managing albums of DICOM images
    """
    
    def __init__(self, base_dir='./albums', db_manager=None):
        """Initialize with the base directory for storing albums"""
        self.base_dir = base_dir
        self.db_manager = db_manager
        os.makedirs(base_dir, exist_ok=True)
    
    def create_album(self, name, description, creator, file_paths=None, query_results=None):
        """
        Create a new album with the provided DICOM files
        
        Parameters:
        - name: Album name
        - description: Album description
        - creator: User who created the album
        - file_paths: List of paths to DICOM files to include
        - query_results: DataFrame with query results including FilePath column
        
        Returns:
        - album_id: Unique ID for the created album
        """
        album_id = shortuuid.uuid()
        
        album_dir = os.path.join(self.base_dir, album_id)
        os.makedirs(album_dir, exist_ok=True)
        
        dicom_dir = os.path.join(album_dir, 'dicom')
        os.makedirs(dicom_dir, exist_ok=True)
        
        paths_to_process = []
        if file_paths:
            paths_to_process = file_paths
        elif query_results is not None and 'FilePath' in query_results.columns:
            paths_to_process = query_results['FilePath'].tolist()
        
        file_metadata = []
        for i, file_path in enumerate(paths_to_process):
            if os.path.exists(file_path):
                file_name = f"{i+1}_{os.path.basename(file_path)}"
                dest_path = os.path.join(dicom_dir, file_name)
                
                try:
                    shutil.copy2(file_path, dest_path)
                    
                    # Extract metadata
                    ds = DICOMProcessor.load_dicom_file(dest_path)
                    if ds is not None:
                        metadata = DICOMProcessor.extract_metadata(ds)
                        metadata['AlbumFilePath'] = dest_path
                        metadata['OriginalFilePath'] = file_path
                        file_metadata.append(metadata)
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
        
        album_metadata = {
            'id': album_id,
            'name': name,
            'description': description,
            'creator': creator,
            'created_date': datetime.now().isoformat(),
            'file_count': len(file_metadata),
            'share_url': f"/album/{album_id}"
        }
        
        with open(os.path.join(album_dir, 'metadata.json'), 'w') as f:
            json.dump(album_metadata, f, indent=2)
        
        if file_metadata:
            pd.DataFrame(file_metadata).to_csv(os.path.join(album_dir, 'files.csv'), index=False)
        
        if self.db_manager:
            self.db_manager.save_album(album_metadata, file_metadata)
        
        return album_id
    
    def get_album_metadata(self, album_id):
        """Get metadata for a specific album"""
        album_dir = os.path.join(self.base_dir, album_id)
        
        if not os.path.exists(album_dir):
            return None
        
        metadata_path = os.path.join(album_dir, 'metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return None
    
    def get_album_files(self, album_id):
        """Get metadata of files in the album"""
        album_dir = os.path.join(self.base_dir, album_id)
        
        if not os.path.exists(album_dir):
            return None
        
        files_path = os.path.join(album_dir, 'files.csv')
        if os.path.exists(files_path):
            return pd.read_csv(files_path)
        return None
    
    def get_all_albums(self):
        """Get a list of all albums"""
        albums = []
        
        if not os.path.exists(self.base_dir):
            return albums
        
        for album_id in os.listdir(self.base_dir):
            album_dir = os.path.join(self.base_dir, album_id)
            if os.path.isdir(album_dir):
                metadata_path = os.path.join(album_dir, 'metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        albums.append(json.load(f))
        
        albums.sort(key=lambda x: x.get('created_date', ''), reverse=True)
        
        return albums
    
    def delete_album(self, album_id):
        """Delete an album"""
        album_dir = os.path.join(self.base_dir, album_id)
        
        if os.path.exists(album_dir):
            shutil.rmtree(album_dir)
            
            if self.db_manager:
                self.db_manager.delete_album(album_id)
            
            return True
        return False
    
    def get_dicom_file(self, album_id, file_index):
        """Get a specific DICOM file from an album"""
        album_files = self.get_album_files(album_id)
        
        if album_files is None or file_index >= len(album_files):
            return None
        
        file_path = album_files.iloc[file_index]['AlbumFilePath']
        if os.path.exists(file_path):
            return DICOMProcessor.load_dicom_file(file_path)
        return None