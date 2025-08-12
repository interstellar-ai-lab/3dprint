#!/usr/bin/env python3
"""
Studio Module for Storage Operations (Supabase)
Provides functionality to fetch and display images from Supabase storage
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# Database imports
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DB_AVAILABLE = True
except ImportError:
    logger.warning("PostgreSQL library not installed. Install with: pip install psycopg2-binary")
    DB_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    logger.warning("Supabase library not installed. Install with: pip install supabase")
    SUPABASE_AVAILABLE = False


class StudioSupabaseManager:
    """Manager class for Studio Supabase Storage operations"""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None, bucket_name: str = "generated-images-bucket"):
        """
        Initialize Studio Supabase Storage manager
        
        Args:
            supabase_url: Supabase project URL (optional, will use env var)
            supabase_key: Supabase anon key (optional, will use env var)
            bucket_name: Name of the storage bucket (default: generated-images-bucket)
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_ANON_KEY')
        self.bucket_name = bucket_name
        self.client: Optional[Client] = None
        self._authenticated = False
        
        # Database configuration (if needed for metadata)
        self.db_config = {
            'host': os.getenv('DB_HOST', '34.187.201.209'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'vicinoAI123!')
        }
        
    def initialize(self) -> Dict[str, Any]:
        """Initialize Supabase connection and authentication"""
        result = {
            "success": False,
            "error": None,
            "bucket_accessible": False
        }
        
        if not SUPABASE_AVAILABLE:
            result["error"] = "Supabase library not available"
            return result
            
        if not self.supabase_url or not self.supabase_key:
            result["error"] = "Supabase URL and key must be provided"
            return result
            
        try:
            # Create Supabase client
            self.client = create_client(self.supabase_url, self.supabase_key)
            
            # Test connection by making a simple database query
            # Try to access the generated_images table
            response = self.client.table('generated_images').select('id').limit(1).execute()
            
            # If we can query the database, we're connected
            self._authenticated = True
            result["success"] = True
            result["bucket_accessible"] = True
            logger.info(f"✅ Supabase storage initialized successfully for bucket: {self.bucket_name}")
                
        except Exception as e:
            result["error"] = f"Initialization error: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def list_public_images(self, prefix: str = "", max_results: int = 100) -> Dict[str, Any]:
        """
        List images from the Supabase storage bucket by querying the generated_images table
        
        Args:
            prefix: Folder prefix to search in (not used for database queries)
            max_results: Maximum number of images to return
            
        Returns:
            Dict containing success status, images list, and any errors
        """
        result = {
            "success": False,
            "error": None,
            "images": [],
            "total_count": 0
        }
        
        if not self._authenticated or not self.client:
            result["error"] = "Client not initialized. Call initialize() first."
            return result
            
        try:
            # Query the generated_images table to get all images
            query = """
                SELECT 
                    id,
                    created_at,
                    target_object,
                    iteration,
                    image_url,
                    "3d_url" as model_3d_url
                FROM generated_images 
                WHERE image_url IS NOT NULL
                ORDER BY id DESC
                LIMIT %s
            """
            
            response = self.client.table('generated_images').select(
                'id, created_at, target_object, iteration, image_url, 3d_url'
            ).order('id', desc=True).limit(max_results).execute()
            
            if response.data:
                images = []
                for row in response.data:
                    # Extract filename from image_url
                    image_url = row.get('image_url', '')
                    filename = image_url.split('/')[-1] if image_url else f"image_{row.get('id')}"
                    
                    # Check if 3D model exists
                    model_3d_url = row.get('3d_url')
                    has_3d_model = model_3d_url is not None and model_3d_url.strip() != ''
                    
                    image_info = {
                        "id": row.get('id'),
                        "name": filename,
                        "filename": filename,
                        "size": 0,  # We don't have size info in the database
                        "updated": row.get('created_at'),
                        "content_type": "image/png" if filename.endswith('.png') else "image/jpeg",
                        "public_url": image_url,
                        "thumbnail_url": image_url,
                        "authenticated_url": image_url,
                        "signed_url": None,
                        "zipurl": model_3d_url,  # 3D model URL from database
                        "has_3d_model": has_3d_model,
                        "target_object": row.get('target_object'),
                        "iteration": row.get('iteration'),
                        "created_at": row.get('created_at')
                    }
                    images.append(image_info)
                
                result["images"] = images
                result["total_count"] = len(images)
                result["success"] = True
                
                logger.info(f"✅ Found {len(images)} images in generated_images table")
            else:
                result["images"] = []
                result["total_count"] = 0
                result["success"] = True
                logger.info("ℹ️ No images found in generated_images table")
            
        except Exception as e:
            result["error"] = f"Error listing images: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def get_image_metadata(self, image_id: int = None, image_url: str = None) -> Dict[str, Any]:
        """
        Get detailed metadata for a specific image from the database
        
        Args:
            image_id: ID of the image in the database
            image_url: URL of the image (alternative to image_id)
            
        Returns:
            Dict containing image metadata
        """
        result = {
            "success": False,
            "error": None,
            "metadata": None
        }
        
        if not self._authenticated or not self.client:
            result["error"] = "Client not initialized. Call initialize() first."
            return result
            
        if not image_id and not image_url:
            result["error"] = "Either image_id or image_url must be provided"
            return result
            
        try:
            # Query the database for the specific image
            if image_id:
                response = self.client.table('generated_images').select('*').eq('id', image_id).execute()
            else:
                response = self.client.table('generated_images').select('*').eq('image_url', image_url).execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]
                
                # Extract filename from image_url
                image_url = row.get('image_url', '')
                filename = image_url.split('/')[-1] if image_url else f"image_{row.get('id')}"
                
                # Check if 3D model exists
                model_3d_url = row.get('3d_url')
                has_3d_model = model_3d_url is not None and model_3d_url.strip() != ''
                
                metadata = {
                    "id": row.get('id'),
                    "name": filename,
                    "filename": filename,
                    "public_url": image_url,
                    "content_type": "image/png" if filename.endswith('.png') else "image/jpeg",
                    "bucket": self.bucket_name,
                    "storage_type": "supabase",
                    "target_object": row.get('target_object'),
                    "iteration": row.get('iteration'),
                    "created_at": row.get('created_at'),
                    "model_3d_url": model_3d_url,
                    "has_3d_model": has_3d_model
                }
                
                result["metadata"] = metadata
                result["success"] = True
            else:
                result["error"] = "Image not found in database"
                
        except Exception as e:
            result["error"] = f"Error getting metadata: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def _is_image_file(self, filename: str) -> bool:
        """Check if a file is an image based on its extension"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        return Path(filename).suffix.lower() in image_extensions
    
    def generate_signed_url(self, image_path: str, expiration_minutes: int = 60) -> Dict[str, Any]:
        """
        Generate a signed URL for an image (Supabase storage is public by default)
        
        Args:
            image_path: Path to the image in the bucket
            expiration_minutes: Expiration time in minutes (not used for Supabase)
            
        Returns:
            Dict containing the public URL (Supabase storage is public by default)
        """
        result = {
            "success": False,
            "error": None,
            "signed_url": None,
            "expires_at": None
        }
        
        if not self._authenticated or not self.client:
            result["error"] = "Client not initialized. Call initialize() first."
            return result
            
        try:
            # Supabase storage URLs are public by default, so we just return the public URL
            public_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{image_path}"
            
            result["signed_url"] = public_url
            result["expires_at"] = None  # Public URLs don't expire
            result["success"] = True
            
        except Exception as e:
            result["error"] = f"Error generating signed URL: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def insert_image(self, target_object: str, image_url: str, model_3d_url: str = None, iteration: int = None) -> Dict[str, Any]:
        """
        Insert a new image record into the generated_images table
        
        Args:
            target_object: Description of the target object
            image_url: URL of the generated image
            model_3d_url: URL of the 3D model (optional)
            iteration: Iteration number (optional)
            
        Returns:
            Dict containing success status and inserted record info
        """
        result = {
            "success": False,
            "error": None,
            "inserted_id": None,
            "record": None
        }
        
        if not self._authenticated or not self.client:
            result["error"] = "Client not initialized. Call initialize() first."
            return result
            
        if not target_object or not image_url:
            result["error"] = "target_object and image_url are required"
            return result
            
        try:
            # Prepare data for insertion
            data = {
                "target_object": target_object,
                "image_url": image_url,
                "iteration": iteration
            }
            
            # Add 3D model URL if provided
            if model_3d_url:
                data["3d_url"] = model_3d_url
            
            # Insert the record
            response = self.client.table('generated_images').insert(data).execute()
            
            if response.data and len(response.data) > 0:
                inserted_record = response.data[0]
                result["success"] = True
                result["inserted_id"] = inserted_record.get('id')
                result["record"] = inserted_record
                logger.info(f"✅ Inserted image record with ID: {result['inserted_id']}")
            else:
                result["error"] = "No data returned from insert operation"
                
        except Exception as e:
            result["error"] = f"Error inserting image: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def upload_image(self, image_data: bytes, filename: str, content_type: str = "image/png") -> Dict[str, Any]:
        """
        Upload an image to Supabase storage
        
        Args:
            image_data: Image data as bytes
            filename: Name of the file to upload
            content_type: MIME type of the image
            
        Returns:
            Dict containing success status and uploaded file info
        """
        result = {
            "success": False,
            "error": None,
            "file_path": None,
            "public_url": None
        }
        
        if not self._authenticated or not self.client:
            result["error"] = "Client not initialized. Call initialize() first."
            return result
            
        if not image_data or not filename:
            result["error"] = "image_data and filename are required"
            return result
            
        try:
            # Upload file to Supabase storage
            response = self.client.storage.from_(self.bucket_name).upload(
                path=filename,
                file=image_data,
                file_options={"content-type": content_type}
            )
            
            if response:
                result["success"] = True
                result["file_path"] = filename
                result["public_url"] = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{filename}"
                logger.info(f"✅ Uploaded image: {filename}")
            else:
                result["error"] = "Upload failed - no response from storage"
                
        except Exception as e:
            result["error"] = f"Error uploading image: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def search_images(self, query: str, max_results: int = 50) -> Dict[str, Any]:
        """
        Search images by target_object description
        
        Args:
            query: Search query to match against target_object
            max_results: Maximum number of results
            
        Returns:
            Dict containing matching images
        """
        result = {
            "success": False,
            "error": None,
            "images": [],
            "total_count": 0,
            "query": query
        }
        
        if not self._authenticated or not self.client:
            result["error"] = "Client not initialized. Call initialize() first."
            return result
            
        try:
            # Search in the database using ILIKE for case-insensitive search
            response = self.client.table('generated_images').select(
                'id, created_at, target_object, iteration, image_url, 3d_url'
            ).ilike('target_object', f'%{query}%').order('id', desc=True).limit(max_results).execute()
            
            if response.data:
                images = []
                for row in response.data:
                    # Extract filename from image_url
                    image_url = row.get('image_url', '')
                    filename = image_url.split('/')[-1] if image_url else f"image_{row.get('id')}"
                    
                    # Check if 3D model exists
                    model_3d_url = row.get('3d_url')
                    has_3d_model = model_3d_url is not None and model_3d_url.strip() != ''
                    
                    image_info = {
                        "id": row.get('id'),
                        "name": filename,
                        "filename": filename,
                        "size": 0,
                        "updated": row.get('created_at'),
                        "content_type": "image/png" if filename.endswith('.png') else "image/jpeg",
                        "public_url": image_url,
                        "thumbnail_url": image_url,
                        "authenticated_url": image_url,
                        "signed_url": None,
                        "zipurl": model_3d_url,
                        "has_3d_model": has_3d_model,
                        "target_object": row.get('target_object'),
                        "iteration": row.get('iteration'),
                        "created_at": row.get('created_at')
                    }
                    images.append(image_info)
                
                result["images"] = images
                result["total_count"] = len(images)
                result["success"] = True
                
                logger.info(f"✅ Found {len(images)} images matching query: '{query}'")
            else:
                result["images"] = []
                result["total_count"] = 0
                result["success"] = True
                logger.info(f"ℹ️ No images found matching query: '{query}'")
                
        except Exception as e:
            result["error"] = f"Error searching images: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result


def create_supabase_studio_manager(supabase_url: Optional[str] = None, supabase_key: Optional[str] = None) -> StudioSupabaseManager:
    """
    Factory function to create a Studio Supabase Storage manager
    
    Args:
        supabase_url: Supabase project URL (optional)
        supabase_key: Supabase anon key (optional)
        
    Returns:
        StudioSupabaseManager instance
    """
    return StudioSupabaseManager(supabase_url=supabase_url, supabase_key=supabase_key)


