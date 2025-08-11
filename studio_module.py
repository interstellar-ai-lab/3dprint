#!/usr/bin/env python3
"""
Studio Module for Storage Operations (GCP and Supabase)
Provides functionality to fetch and display images from GCP buckets and Supabase storage
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

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    logger.warning("Supabase library not installed. Install with: pip install supabase")
    SUPABASE_AVAILABLE = False

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
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            response = self.client.table('generated_images').select(
                'id, created_at, target_object, iteration, image_url, 3d_url'
            ).order('created_at', desc=True).limit(max_results).execute()
            
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
        Generate a signed URL for an image (Supabase doesn't support signed URLs like GCP)
        
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
            ).ilike('target_object', f'%{query}%').order('created_at', desc=True).limit(max_results).execute()
            
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


