"""
Cloud storage integration for DICOM Album Explorer
"""

import os
import boto3
import uuid
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
from flask import current_app

class CloudStorage:
    """Base class for cloud storage providers"""
    
    def upload_file(self, file_path, key):
        """Upload a file to cloud storage"""
        raise NotImplementedError
    
    def download_file(self, key, local_path):
        """Download a file from cloud storage"""
        raise NotImplementedError
    
    def delete_file(self, key):
        """Delete a file from cloud storage"""
        raise NotImplementedError
    
    def generate_presigned_url(self, key, expiration=3600):
        """Generate a presigned URL for temporary file access"""
        raise NotImplementedError
    
    def list_files(self, prefix=''):
        """List files with optional prefix filter"""
        raise NotImplementedError

class S3Storage(CloudStorage):
    """Amazon S3 storage implementation"""
    
    def __init__(self, bucket_name, region='us-east-1', access_key=None, secret_key=None):
        self.bucket_name = bucket_name
        self.region = region
        
        # Initialize S3 client
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        self.s3_client = session.client('s3')
        self.s3_resource = session.resource('s3')
        
        # Verify credentials and bucket access
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                raise ValueError(f"S3 bucket '{bucket_name}' does not exist")
            elif error_code == 403:
                raise ValueError(f"Access denied to S3 bucket '{bucket_name}'")
            else:
                raise ValueError(f"Error accessing S3 bucket: {e}")
        except NoCredentialsError:
            raise ValueError("AWS credentials not found")
    
    def upload_file(self, file_path, key):
        """Upload a file to S3"""
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, key)
            return f"s3://{self.bucket_name}/{key}"
        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {e}")
    
    def download_file(self, key, local_path):
        """Download a file from S3"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(self.bucket_name, key, local_path)
            return local_path
        except ClientError as e:
            raise Exception(f"Failed to download file from S3: {e}")
    
    def delete_file(self, key):
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete file from S3: {e}")
    
    def generate_presigned_url(self, key, expiration=3600):
        """Generate a presigned URL for temporary file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {e}")
    
    def list_files(self, prefix=''):
        """List files with optional prefix filter"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'url': f"s3://{self.bucket_name}/{obj['Key']}"
                    })
            
            return files
        except ClientError as e:
            raise Exception(f"Failed to list files from S3: {e}")
    
    def copy_file(self, source_key, dest_key):
        """Copy a file within S3"""
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key
            )
            return True
        except ClientError as e:
            raise Exception(f"Failed to copy file in S3: {e}")

class CloudStorageManager:
    """Manager class for cloud storage operations"""
    
    def __init__(self, app=None):
        self.storage = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize cloud storage from Flask app configuration"""
        if not app.config.get('USE_CLOUD_STORAGE', False):
            return
        
        # Configure S3 storage
        bucket_name = app.config.get('AWS_S3_BUCKET')
        if not bucket_name:
            raise ValueError("AWS_S3_BUCKET configuration is required for cloud storage")
        
        self.storage = S3Storage(
            bucket_name=bucket_name,
            region=app.config.get('AWS_S3_REGION', 'us-east-1'),
            access_key=app.config.get('AWS_ACCESS_KEY_ID'),
            secret_key=app.config.get('AWS_SECRET_ACCESS_KEY')
        )
    
    def upload_dicom_file(self, file_path, album_id, filename):
        """Upload a DICOM file to cloud storage"""
        if not self.storage:
            return None
        
        # Generate unique key for the file
        key = f"albums/{album_id}/dicom/{filename}"
        
        try:
            cloud_url = self.storage.upload_file(file_path, key)
            return cloud_url
        except Exception as e:
            current_app.logger.error(f"Failed to upload file to cloud storage: {e}")
            return None
    
    def download_dicom_file(self, cloud_url, local_path):
        """Download a DICOM file from cloud storage"""
        if not self.storage or not cloud_url.startswith('s3://'):
            return None
        
        # Extract key from S3 URL
        key = cloud_url.replace(f"s3://{self.storage.bucket_name}/", "")
        
        try:
            return self.storage.download_file(key, local_path)
        except Exception as e:
            current_app.logger.error(f"Failed to download file from cloud storage: {e}")
            return None
    
    def generate_download_url(self, cloud_url, expiration=3600):
        """Generate a temporary download URL for a file"""
        if not self.storage or not cloud_url.startswith('s3://'):
            return None
        
        # Extract key from S3 URL
        key = cloud_url.replace(f"s3://{self.storage.bucket_name}/", "")
        
        try:
            return self.storage.generate_presigned_url(key, expiration)
        except Exception as e:
            current_app.logger.error(f"Failed to generate download URL: {e}")
            return None
    
    def delete_album_files(self, album_id):
        """Delete all files for an album from cloud storage"""
        if not self.storage:
            return
        
        prefix = f"albums/{album_id}/"
        
        try:
            # List all files for the album
            files = self.storage.list_files(prefix)
            
            # Delete each file
            for file_info in files:
                self.storage.delete_file(file_info['key'])
            
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to delete album files from cloud storage: {e}")
            return False

# Global storage manager instance
storage_manager = CloudStorageManager()