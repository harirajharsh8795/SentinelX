import os
from typing import BinaryIO
from utils.crypto import encrypt_file_data # Phase 12

# Phase 6: Enterprise Storage Simulation
# This mimics an S3/Blob storage client that seamlessly interfaces with our local file system
# but is ready to swap out the underlying driver for boto3 or azure.storage.blob
import boto3
import logging

logger = logging.getLogger(__name__)

class BlobStorageClient:
    def __init__(self, bucket_name: str = "sentinel-documents"):
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("AWS_BUCKET_NAME", bucket_name)
        self.region = os.getenv("AWS_REGION", "ap-south-1")
        
        self.s3_client = None
        if self.aws_access_key and self.aws_secret_key:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.region
                )
                logger.info(f"[BlobStorage] AWS S3 Enabled. Bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"[BlobStorage] Failed to initialize S3 client: {e}. Falling back to local mock storage.")
                self.s3_client = None

        self.base_dir = os.path.join(os.getcwd(), "cloud_storage_mock", self.bucket_name)
        os.makedirs(self.base_dir, exist_ok=True)

    def upload_fileobj(self, file_obj: BinaryIO, object_name: str) -> str:
        """
        Uploads a file object to S3 if configured, else falls back to mock S3 storage.
        Returns the simulated or actual public URL/URI.
        """
        # Save a local encrypted copy for local cache/fallback compliance
        file_path = os.path.join(self.base_dir, object_name)
        data = file_obj.read()
        
        # Reset file pointer so s3 upload reads from start
        file_obj.seek(0)
        
        encrypted_data = encrypt_file_data(data)
        with open(file_path, "wb") as f:
            f.write(encrypted_data)
            
        if self.s3_client:
            try:
                self.s3_client.upload_fileobj(file_obj, self.bucket_name, object_name)
                logger.info(f"[BlobStorage] Successfully uploaded {object_name} to S3 bucket {self.bucket_name}")
                return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{object_name}"
            except Exception as e:
                logger.error(f"[BlobStorage] S3 upload failed: {e}. Using local mock URI.")
                
        return f"s3://{self.bucket_name}/{object_name}"

    def get_local_path(self, object_name: str) -> str:
        return os.path.join(self.base_dir, object_name)

# Singleton instance
storage_client = BlobStorageClient()
