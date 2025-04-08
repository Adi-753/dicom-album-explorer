import os
import pydicom
import numpy as np
from PIL import Image
import io
import base64
import pandas as pd
import datetime

class DICOMProcessor:
    """
    Class for processing DICOM files, extracting metadata and preparing images for display
    """

    @staticmethod
    def load_dicom_file(file_path):
        """Load a DICOM file and return the dataset"""
        try:
            return pydicom.dcmread(file_path)
        except Exception as e:
            print(f"Error loading DICOM file {file_path}: {e}")
            return None

    @staticmethod
    def extract_metadata(dicom_dataset):
        """Extract important metadata from a DICOM dataset"""
        if dicom_dataset is None:
            return {}
        
        fields = [
            'PatientID', 'PatientName', 'PatientBirthDate', 'PatientSex',
            'StudyInstanceUID', 'StudyDescription', 'StudyDate', 'StudyTime',
            'SeriesInstanceUID', 'SeriesDescription', 'Modality',
            'SOPInstanceUID', 'InstanceNumber', 'SliceLocation',
            'ImageType', 'PixelSpacing', 'WindowCenter', 'WindowWidth'
        ]
        
        metadata = {}
        for field in fields:
            if hasattr(dicom_dataset, field):
                value = getattr(dicom_dataset, field)
                if isinstance(value, pydicom.valuerep.PersonName):
                    metadata[field] = str(value)
                elif isinstance(value, pydicom.valuerep.DSfloat):
                    metadata[field] = float(value)
                elif isinstance(value, pydicom.multival.MultiValue):
                    metadata[field] = [str(x) for x in value]
                else:
                    metadata[field] = str(value)
            else:
                metadata[field] = None
                
        return metadata

    @staticmethod
    def convert_to_image(dicom_dataset, window_center=None, window_width=None):
        """Convert DICOM dataset to displayable image format"""
        if dicom_dataset is None:
            return None
        
        try:
            pixel_array = dicom_dataset.pixel_array
            
            if window_center is None and hasattr(dicom_dataset, 'WindowCenter'):
                window_center = dicom_dataset.WindowCenter
                if isinstance(window_center, pydicom.multival.MultiValue):
                    window_center = window_center[0]
            
            if window_width is None and hasattr(dicom_dataset, 'WindowWidth'):
                window_width = dicom_dataset.WindowWidth
                if isinstance(window_width, pydicom.multival.MultiValue):
                    window_width = window_width[0]
            
            if window_center is not None and window_width is not None:
                window_center = float(window_center)
                window_width = float(window_width)
                lower_bound = window_center - window_width / 2
                upper_bound = window_center + window_width / 2
                
                windowed_image = np.clip(pixel_array, lower_bound, upper_bound)
                
                windowed_image = ((windowed_image - lower_bound) / (upper_bound - lower_bound)) * 255.0
                image_data = windowed_image.astype(np.uint8)
            else:
                min_val = np.min(pixel_array)
                max_val = np.max(pixel_array)
                if max_val != min_val:
                    image_data = ((pixel_array - min_val) / (max_val - min_val)) * 255.0
                    image_data = image_data.astype(np.uint8)
                else:
                    image_data = np.zeros_like(pixel_array, dtype=np.uint8)
            
            img = Image.fromarray(image_data)
            
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return img_str
        
        except Exception as e:
            print(f"Error converting DICOM to image: {e}")
            return None
    
    @staticmethod
    def scan_directory(directory_path):
        """Scan a directory for DICOM files and extract metadata"""
        dicom_files = []
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    dicom_dataset = pydicom.dcmread(file_path, force=True)
                    metadata = DICOMProcessor.extract_metadata(dicom_dataset)
                    metadata['FilePath'] = file_path
                    dicom_files.append(metadata)
                except Exception as e:
                    print(f"Not a DICOM file or error: {file_path} - {e}")
        
        if dicom_files:
            return pd.DataFrame(dicom_files)
        else:
            return pd.DataFrame()
    
    @staticmethod
    def anonymize_dicom(dicom_dataset, fields_to_anonymize=None):
        """Anonymize sensitive information in DICOM file"""
        if fields_to_anonymize is None:
            fields_to_anonymize = [
                'PatientName', 'PatientID', 'PatientBirthDate',
                'AccessionNumber', 'ReferringPhysicianName'
            ]
        
        for field in fields_to_anonymize:
            if hasattr(dicom_dataset, field):
                if field == 'PatientName':
                    setattr(dicom_dataset, field, 'ANONYMOUS')
                elif field == 'PatientID':
                    setattr(dicom_dataset, field, 'ID000000')
                elif field == 'PatientBirthDate':
                    setattr(dicom_dataset, field, '19000101')
                else:
                    setattr(dicom_dataset, field, '')
        
        return dicom_dataset