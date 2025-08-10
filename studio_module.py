#!/usr/bin/env python3
"""
Studio Module for GCP Cloud Storage Operations
Provides functionality to fetch and display images from public GCP buckets
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
    from google.cloud import storage
    from google.auth.exceptions import DefaultCredentialsError
    from google.api_core.exceptions import GoogleAPIError
    GCP_AVAILABLE = True
except ImportError:
    logger.warning("Google Cloud Storage library not installed. Install with: pip install google-cloud-storage")
    GCP_AVAILABLE = False

class StudioGCPManager:
    """Manager class for Studio GCP Cloud Storage operations"""
    
    def __init__(self, bucket_name: str = "vicino.ai", project_id: Optional[str] = None, credentials_path: Optional[str] = None):
        """
        Initialize Studio GCP Storage manager
        
        Args:
            bucket_name: Name of the GCS bucket (default: vicino.ai)
            project_id: GCP project ID (optional, will be auto-detected)
            credentials_path: Path to service account JSON key file (optional)
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.client = None
        self.bucket = None
        self._authenticated = False
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', '34.187.201.209'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'vicinoAI123!')
        }
        
    def initialize(self) -> Dict[str, Any]:
        """Initialize GCP connection and authentication"""
        result = {
            "success": False,
            "error": None,
            "project_id": None,
            "bucket_accessible": False
        }
        
        if not GCP_AVAILABLE:
            result["error"] = "Google Cloud Storage library not available"
            return result
            
        try:
            # Initialize the client with credentials if provided
            if self.credentials_path and os.path.exists(self.credentials_path):
                # Check if it's a service account file or default credentials file
                with open(self.credentials_path, 'r') as f:
                    cred_data = json.load(f)
                
                if 'type' in cred_data and cred_data['type'] == 'service_account':
                    # Service account JSON file
                    from google.oauth2 import service_account
                    credentials = service_account.Credentials.from_service_account_file(self.credentials_path)
                    self.client = storage.Client(project=self.project_id, credentials=credentials)
                    logger.info(f"✅ Using service account credentials from: {self.credentials_path}")
                else:
                    # Default credentials file (user credentials)
                    from google.oauth2 import credentials as user_credentials
                    credentials = user_credentials.Credentials.from_authorized_user_file(self.credentials_path)
                    self.client = storage.Client(project=self.project_id, credentials=credentials)
                    logger.info(f"✅ Using default user credentials from: {self.credentials_path}")
            else:
                # Try to use environment variable or default credentials
                self.client = storage.Client(project=self.project_id)
                logger.info("✅ Using default credentials")
            
            # Test bucket access
            self.bucket = self.client.bucket(self.bucket_name)
            bucket_exists = self.bucket.exists()
            
            result["project_id"] = self.client.project
            result["bucket_accessible"] = bucket_exists
            result["success"] = True
            self._authenticated = True
            
            if bucket_exists:
                logger.info(f"✅ Successfully connected to bucket: {self.bucket_name}")
            else:
                logger.warning(f"⚠️ Bucket '{self.bucket_name}' not accessible or doesn't exist")
                
        except DefaultCredentialsError as e:
            result["error"] = f"Authentication failed - no default credentials found: {e}"
            logger.error(f"❌ {result['error']}")
            
        except Exception as e:
            result["error"] = f"Initialization error: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def list_public_images(self, prefix: str = "public_images/", max_results: int = 100) -> Dict[str, Any]:
        """
        List images from the public_images/ folder in the bucket
        
        Args:
            prefix: Folder prefix to search in (default: public_images/)
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
            # List blobs with the specified prefix
            blobs = self.client.list_blobs(
                self.bucket_name, 
                prefix=prefix, 
                max_results=max_results
            )
            
            images = []
            for blob in blobs:
                # Only include image files
                if self._is_image_file(blob.name):
                    # Generate authenticated URLs
                    authenticated_url = self._generate_authenticated_url(blob.name)
                    
                    # Get zipurl from database using the authenticated URL
                    zipurl_result = self.get_zipurl_from_db(authenticated_url)
                    zipurl = zipurl_result.get("zipurl") if zipurl_result.get("success") else None
                    
                    image_info = {
                        "name": blob.name,
                        "filename": os.path.basename(blob.name),
                        "size": blob.size,
                        "updated": blob.updated.isoformat() if blob.updated else None,
                        "content_type": blob.content_type,
                        "public_url": authenticated_url,
                        "thumbnail_url": authenticated_url,
                        "authenticated_url": authenticated_url,
                        "signed_url": None,  # Will be generated on-demand if needed
                        "zipurl": zipurl,  # 3D model zip file URL from database
                        "has_3d_model": zipurl is not None
                    }
                    images.append(image_info)
            
            # Sort by update time (newest first)
            images.sort(key=lambda x: x['updated'] or '', reverse=True)
            
            result["images"] = images
            result["total_count"] = len(images)
            result["success"] = True
            
            logger.info(f"✅ Found {len(images)} images in {self.bucket_name}/{prefix}")
            
        except Exception as e:
            result["error"] = f"Error listing images: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def get_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Get detailed metadata for a specific image
        
        Args:
            image_path: Path to the image in the bucket
            
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
            
        try:
            blob = self.bucket.blob(image_path)
            
            if not blob.exists():
                result["error"] = f"Image does not exist: {image_path}"
                return result
            
            # Refresh blob to get latest metadata
            blob.reload()
            
            metadata = {
                "name": blob.name,
                "filename": os.path.basename(blob.name),
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "public_url": f"https://storage.googleapis.com/{self.bucket_name}/{blob.name}",
                "cache_control": blob.cache_control,
                "custom_metadata": blob.metadata or {}
            }
            
            result["metadata"] = metadata
            result["success"] = True
            
        except Exception as e:
            result["error"] = f"Error getting image metadata: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def _is_image_file(self, filename: str) -> bool:
        """Check if a file is an image based on its extension"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.ico'}
        return any(filename.lower().endswith(ext) for ext in image_extensions)
    
    def _generate_authenticated_url(self, blob_name: str, authuser: int = 3) -> str:
        """
        Generate an authenticated URL for accessing the blob
        
        Args:
            blob_name: Name of the blob in the bucket
            authuser: Google account index (default: 3, adjust as needed)
            
        Returns:
            Authenticated URL string
        """
        # Use the Google Cloud Console authenticated URL format
        base_url = f"https://storage.cloud.google.com/{self.bucket_name}/{blob_name}"
        authenticated_url = f"{base_url}?authuser={authuser}"
        return authenticated_url
    
    def generate_signed_url(self, blob_name: str, expiration_minutes: int = 60) -> Dict[str, Any]:
        """
        Generate a signed URL for temporary access to a blob
        
        Args:
            blob_name: Name of the blob in the bucket
            expiration_minutes: URL expiration time in minutes
            
        Returns:
            Dict containing signed URL or error
        """
        result = {
            "success": False,
            "error": None,
            "signed_url": None,
            "expires_in_minutes": expiration_minutes
        }
        
        if not self._authenticated or not self.bucket:
            result["error"] = "Bucket not accessible. Call initialize() first."
            return result
        
        try:
            from datetime import datetime, timedelta
            
            blob = self.bucket.blob(blob_name)
            
            if not blob.exists():
                result["error"] = f"Blob does not exist: {blob_name}"
                return result
            
            # Generate signed URL
            expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET"
            )
            
            result["signed_url"] = signed_url
            result["success"] = True
            
            logger.info(f"✅ Generated signed URL for {blob_name} (expires in {expiration_minutes} min)")
            
        except Exception as e:
            result["error"] = f"Error generating signed URL: {e}"
            logger.error(f"❌ {result['error']}")
        
        return result
    
    def get_zipurl_from_db(self, imageurl: str) -> Dict[str, Any]:
        """
        Query PostgreSQL database to get zipurl for the given imageurl
        
        Args:
            imageurl: The image URL to search for
            
        Returns:
            Dict containing zipurl or error
        """
        result = {
            "success": False,
            "error": None,
            "zipurl": None,
            "imageurl": imageurl
        }
        
        if not DB_AVAILABLE:
            result["error"] = "PostgreSQL library not available"
            return result
        
        try:
            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Query for zipurl based on imageurl
            cursor.execute("""
                SELECT zipurl FROM imageand3durl 
                WHERE imageurl = %s
                LIMIT 1;
            """, (imageurl,))
            
            row = cursor.fetchone()
            
            if row:
                result["zipurl"] = row[0]
                result["success"] = True
                logger.info(f"✅ Found zipurl for image: {imageurl}")
            else:
                result["error"] = f"No zipurl found for imageurl: {imageurl}"
                logger.warning(f"⚠️ {result['error']}")
            
            cursor.close()
            conn.close()
            
        except psycopg2.Error as e:
            result["error"] = f"Database error: {e}"
            logger.error(f"❌ {result['error']}")
        except Exception as e:
            result["error"] = f"Unexpected error: {e}"
            logger.error(f"❌ {result['error']}")
        
        return result
    
    def search_images(self, query: str, prefix: str = "public_images/", max_results: int = 50) -> Dict[str, Any]:
        """
        Search for images by filename containing the query
        
        Args:
            query: Search query string
            prefix: Folder prefix to search in
            max_results: Maximum number of results
            
        Returns:
            Dict containing matching images
        """
        # Get all images first
        all_images_result = self.list_public_images(prefix, max_results * 2)  # Get more to filter
        
        if not all_images_result["success"]:
            return all_images_result
        
        # Filter images based on query
        query_lower = query.lower()
        matching_images = []
        
        for image in all_images_result["images"]:
            if query_lower in image["filename"].lower() or query_lower in image["name"].lower():
                matching_images.append(image)
        
        # Limit results
        matching_images = matching_images[:max_results]
        
        return {
            "success": True,
            "error": None,
            "images": matching_images,
            "total_count": len(matching_images),
            "query": query
        }
    
    def get_bucket_info(self) -> Dict[str, Any]:
        """Get information about the bucket"""
        result = {
            "success": False,
            "error": None,
            "bucket_info": None
        }
        
        if not self._authenticated or not self.bucket:
            result["error"] = "Bucket not accessible. Call initialize() first."
            return result
            
        try:
            # Get bucket info
            # Convert lifecycle_rules generator to list to get count
            lifecycle_rules_count = 0
            try:
                lifecycle_rules = list(self.bucket.lifecycle_rules) if self.bucket.lifecycle_rules else []
                lifecycle_rules_count = len(lifecycle_rules)
            except Exception:
                lifecycle_rules_count = 0
            
            bucket_info = {
                "name": self.bucket.name,
                "location": self.bucket.location,
                "storage_class": self.bucket.storage_class,
                "created": self.bucket.time_created.isoformat() if self.bucket.time_created else None,
                "updated": self.bucket.updated.isoformat() if self.bucket.updated else None,
                "versioning_enabled": self.bucket.versioning_enabled,
                "lifecycle_rules": lifecycle_rules_count
            }
            
            result["bucket_info"] = bucket_info
            result["success"] = True
            
        except Exception as e:
            result["error"] = f"Error getting bucket info: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result

def create_studio_manager(credentials_path: Optional[str] = None) -> StudioGCPManager:
    """
    Factory function to create and initialize a StudioGCPManager
    
    Args:
        credentials_path: Optional path to credentials file
        
    Returns:
        Initialized StudioGCPManager instance
    """
    # Use default credentials path if not provided
    if not credentials_path:
        credentials_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    
    manager = StudioGCPManager(
        bucket_name="vicino.ai",
        credentials_path=credentials_path if os.path.exists(credentials_path) else None
    )
    
    # Initialize the manager
    init_result = manager.initialize()
    
    if not init_result["success"]:
        logger.warning(f"⚠️ Studio manager initialization failed: {init_result['error']}")
    
    return manager


