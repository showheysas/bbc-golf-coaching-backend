from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
import os
import shutil
from pathlib import Path
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from azure.storage.blob import BlobServiceClient, BlobClient
from dotenv import load_dotenv

load_dotenv()

class StorageInterface(ABC):
    """Abstract interface for storage operations"""
    
    @abstractmethod
    async def upload_file(self, file: BinaryIO, filename: str, content_type: Optional[str] = None) -> str:
        """Upload a file and return the URL"""
        pass
    
    @abstractmethod
    async def upload_file_with_exact_name(self, file: BinaryIO, exact_filename: str, content_type: Optional[str] = None) -> str:
        """Upload a file with exact filename (no modifications) and return the URL"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_url: str) -> bool:
        """Delete a file by URL"""
        pass
    
    @abstractmethod
    async def get_file_url(self, filename: str) -> str:
        """Get the URL for a file"""
        pass

class LocalStorage(StorageInterface):
    """Local file storage implementation"""
    
    def __init__(self, storage_path: str = "./uploads"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.base_url = "/uploads"  # Use relative path to work with Next.js proxy
    
    async def upload_file(self, file: BinaryIO, filename: str, content_type: Optional[str] = None) -> str:
        """Upload file to local storage"""
        # Generate unique filename with timestamp
        file_extension = Path(filename).suffix
        jst = timezone(timedelta(hours=9))
        now = datetime.now(jst)
        timestamp = now.strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_U99999{file_extension}"
        
        file_path = self.storage_path / unique_filename
        
        # Copy file to local storage
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)
        
        return f"{self.base_url}/{unique_filename}"
    
    async def upload_file_with_exact_name(self, file: BinaryIO, exact_filename: str, content_type: Optional[str] = None) -> str:
        """Upload file to local storage with exact filename"""
        file_path = self.storage_path / exact_filename
        
        # Copy file to local storage
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)
        
        return f"{self.base_url}/{exact_filename}"
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file from local storage"""
        try:
            # Extract filename from URL
            filename = file_url.split("/")[-1]
            file_path = self.storage_path / filename
            
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    async def get_file_url(self, filename: str) -> str:
        """Get URL for local file"""
        return f"{self.base_url}/{filename}"

class AzureBlobStorage(StorageInterface):
    """Azure Blob Storage implementation"""
    
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "bbc-test")
        
        if not self.connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is required for Azure Blob Storage")
        
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def upload_file(self, file: BinaryIO, filename: str, content_type: Optional[str] = None) -> str:
        """Upload file to Azure Blob Storage"""
        # Generate unique filename with timestamp
        file_extension = Path(filename).suffix
        jst = timezone(timedelta(hours=9))
        now = datetime.now(jst)
        timestamp = now.strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_U99999{file_extension}"
        
        # Create blob client
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, 
            blob=unique_filename
        )
        
        # Upload file using thread executor for async operation
        def _upload_blob():
            return blob_client.upload_blob(
                file, 
                content_type=content_type,
                overwrite=True
            )
        
        # Run in thread pool to make it truly async
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _upload_blob)
        
        return blob_client.url
    
    async def upload_file_with_exact_name(self, file: BinaryIO, exact_filename: str, content_type: Optional[str] = None) -> str:
        """Upload file to Azure Blob Storage with exact filename"""
        # Create blob client with exact filename
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, 
            blob=exact_filename
        )
        
        # Upload file using thread executor for async operation
        def _upload_blob():
            return blob_client.upload_blob(
                file, 
                content_type=content_type,
                overwrite=True
            )
        
        # Run in thread pool to make it truly async
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _upload_blob)
        
        return blob_client.url
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file from Azure Blob Storage"""
        try:
            # Extract blob name from URL
            blob_name = file_url.split("/")[-1]
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Delete blob using thread executor for async operation
            def _delete_blob():
                return blob_client.delete_blob()
            
            # Run in thread pool to make it truly async
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, _delete_blob)
            return True
        except Exception:
            return False
    
    async def get_file_url(self, filename: str) -> str:
        """Get URL for Azure blob"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=filename
        )
        return blob_client.url
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

class StorageService:
    """Storage service factory and manager"""
    
    def __init__(self):
        storage_type = os.getenv("STORAGE_TYPE", "local").lower()
        
        if storage_type == "azure_blob":
            self.storage = AzureBlobStorage()
        else:
            # Default to local storage
            storage_path = os.getenv("LOCAL_STORAGE_PATH", "./uploads")
            self.storage = LocalStorage(storage_path)
    
    async def upload_video(self, file: BinaryIO, filename: str) -> str:
        """Upload video file"""
        return await self.storage.upload_file(file, filename, "video/mp4")
    
    async def upload_image(self, file: BinaryIO, filename: str) -> str:
        """Upload image file"""
        return await self.storage.upload_file(file, filename, "image/jpeg")
    
    async def upload_image_with_exact_name(self, file: BinaryIO, exact_filename: str) -> str:
        """Upload image file with exact filename (no timestamp prefix)"""
        return await self.storage.upload_file_with_exact_name(file, exact_filename, "image/jpeg")
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file"""
        return await self.storage.delete_file(file_url)
    
    async def get_file_url(self, filename: str) -> str:
        """Get file URL"""
        return await self.storage.get_file_url(filename)

# Global storage service instance
storage_service = StorageService()