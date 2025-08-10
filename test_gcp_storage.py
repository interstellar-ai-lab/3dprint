#!/usr/bin/env python3
"""
GCP File Storage Connection Test
Tests connection to Google Cloud Storage and basic operations
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

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

class GCPStorageTester:
    """Test class for GCP Cloud Storage operations"""
    
    def __init__(self, bucket_name: str, project_id: Optional[str] = None, credentials_path: Optional[str] = None):
        """
        Initialize GCP Storage tester
        
        Args:
            bucket_name: Name of the GCS bucket to test
            project_id: GCP project ID (optional, will be auto-detected)
            credentials_path: Path to service account JSON key file (optional)
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.client = None
        self.bucket = None
        
    def test_authentication(self) -> Dict[str, Any]:
        """Test GCP authentication and connection"""
        result = {
            "success": False,
            "error": None,
            "project_id": None,
            "credentials_info": None
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
            
            # Get project info
            result["project_id"] = self.client.project
            result["success"] = True
            
            # Get credentials info (if available)
            try:
                credentials = self.client._credentials
                if hasattr(credentials, 'service_account_email'):
                    result["credentials_info"] = {
                        "type": "service_account",
                        "email": credentials.service_account_email
                    }
                else:
                    result["credentials_info"] = {
                        "type": "default_credentials"
                    }
            except Exception as e:
                logger.warning(f"Could not get credentials info: {e}")
                
            logger.info(f"✅ Authentication successful! Project: {result['project_id']}")
            
        except DefaultCredentialsError as e:
            result["error"] = f"Authentication failed - no default credentials found: {e}"
            logger.error(f"❌ {result['error']}")
            logger.info("💡 To fix this, either:")
            logger.info("   1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
            logger.info("   2. Run 'gcloud auth application-default login'")
            logger.info("   3. Use service account key file")
            
        except Exception as e:
            result["error"] = f"Authentication error: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def test_bucket_access(self) -> Dict[str, Any]:
        """Test access to the specified bucket"""
        result = {
            "success": False,
            "error": None,
            "bucket_exists": False,
            "bucket_info": None
        }
        
        if not self.client:
            result["error"] = "Client not initialized. Run test_authentication() first."
            return result
            
        try:
            # Check if bucket exists
            self.bucket = self.client.bucket(self.bucket_name)
            result["bucket_exists"] = self.bucket.exists()
            
            if result["bucket_exists"]:
                # Get bucket info
                result["bucket_info"] = {
                    "name": self.bucket.name,
                    "location": self.bucket.location,
                    "storage_class": self.bucket.storage_class,
                    "created": self.bucket.time_created.isoformat() if self.bucket.time_created else None,
                    "updated": self.bucket.updated.isoformat() if self.bucket.updated else None
                }
                result["success"] = True
                logger.info(f"✅ Bucket '{self.bucket_name}' exists and is accessible")
                logger.info(f"   Location: {result['bucket_info']['location']}")
                logger.info(f"   Storage Class: {result['bucket_info']['storage_class']}")
            else:
                result["error"] = f"Bucket '{self.bucket_name}' does not exist"
                logger.error(f"❌ {result['error']}")
                
        except GoogleAPIError as e:
            result["error"] = f"GCP API error: {e}"
            logger.error(f"❌ {result['error']}")
        except Exception as e:
            result["error"] = f"Bucket access error: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def test_file_upload(self, local_file_path: str, remote_path: Optional[str] = None) -> Dict[str, Any]:
        """Test uploading a file to GCS"""
        result = {
            "success": False,
            "error": None,
            "local_path": local_file_path,
            "remote_path": remote_path,
            "file_size": None,
            "upload_time": None
        }
        
        if not self.bucket:
            result["error"] = "Bucket not accessible. Run test_bucket_access() first."
            return result
            
        if not os.path.exists(local_file_path):
            result["error"] = f"Local file does not exist: {local_file_path}"
            return result
            
        try:
            # Generate remote path if not provided
            if not remote_path:
                filename = os.path.basename(local_file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                remote_path = f"test_uploads/{timestamp}_{filename}"
            
            result["remote_path"] = remote_path
            
            # Get file size
            file_size = os.path.getsize(local_file_path)
            result["file_size"] = file_size
            
            # Upload file
            start_time = datetime.now()
            blob = self.bucket.blob(remote_path)
            blob.upload_from_filename(local_file_path)
            end_time = datetime.now()
            
            result["upload_time"] = (end_time - start_time).total_seconds()
            result["success"] = True
            
            logger.info(f"✅ File uploaded successfully!")
            logger.info(f"   Local: {local_file_path}")
            logger.info(f"   Remote: gs://{self.bucket_name}/{remote_path}")
            logger.info(f"   Size: {file_size} bytes")
            logger.info(f"   Time: {result['upload_time']:.2f} seconds")
            
        except Exception as e:
            result["error"] = f"Upload error: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def test_file_download(self, remote_path: str, local_download_path: Optional[str] = None) -> Dict[str, Any]:
        """Test downloading a file from GCS"""
        result = {
            "success": False,
            "error": None,
            "remote_path": remote_path,
            "local_path": local_download_path,
            "file_size": None,
            "download_time": None
        }
        
        if not self.bucket:
            result["error"] = "Bucket not accessible. Run test_bucket_access() first."
            return result
            
        try:
            # Generate local path if not provided
            if not local_download_path:
                filename = os.path.basename(remote_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                local_download_path = f"test_downloads/{timestamp}_{filename}"
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(local_download_path), exist_ok=True)
            
            result["local_path"] = local_download_path
            
            # Download file
            start_time = datetime.now()
            blob = self.bucket.blob(remote_path)
            
            if not blob.exists():
                result["error"] = f"Remote file does not exist: gs://{self.bucket_name}/{remote_path}"
                return result
                
            blob.download_to_filename(local_download_path)
            end_time = datetime.now()
            
            # Get file size
            file_size = os.path.getsize(local_download_path)
            result["file_size"] = file_size
            result["download_time"] = (end_time - start_time).total_seconds()
            result["success"] = True
            
            logger.info(f"✅ File downloaded successfully!")
            logger.info(f"   Remote: gs://{self.bucket_name}/{remote_path}")
            logger.info(f"   Local: {local_download_path}")
            logger.info(f"   Size: {file_size} bytes")
            logger.info(f"   Time: {result['download_time']:.2f} seconds")
            
        except Exception as e:
            result["error"] = f"Download error: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def test_list_files(self, prefix: str = "", max_results: int = 10) -> Dict[str, Any]:
        """Test listing files in the bucket"""
        result = {
            "success": False,
            "error": None,
            "files": [],
            "total_count": 0
        }
        
        if not self.bucket:
            result["error"] = "Bucket not accessible. Run test_bucket_access() first."
            return result
            
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix, max_results=max_results)
            files = []
            
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "content_type": blob.content_type
                })
            
            result["files"] = files
            result["total_count"] = len(files)
            result["success"] = True
            
            logger.info(f"✅ Listed {len(files)} files in bucket '{self.bucket_name}'")
            if prefix:
                logger.info(f"   Prefix: '{prefix}'")
            
            for file_info in files[:5]:  # Show first 5 files
                logger.info(f"   - {file_info['name']} ({file_info['size']} bytes)")
            
            if len(files) > 5:
                logger.info(f"   ... and {len(files) - 5} more files")
                
        except Exception as e:
            result["error"] = f"List files error: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def test_delete_file(self, remote_path: str) -> Dict[str, Any]:
        """Test deleting a file from GCS"""
        result = {
            "success": False,
            "error": None,
            "remote_path": remote_path
        }
        
        if not self.bucket:
            result["error"] = "Bucket not accessible. Run test_bucket_access() first."
            return result
            
        try:
            blob = self.bucket.blob(remote_path)
            
            if not blob.exists():
                result["error"] = f"File does not exist: gs://{self.bucket_name}/{remote_path}"
                return result
                
            blob.delete()
            result["success"] = True
            
            logger.info(f"✅ File deleted successfully: gs://{self.bucket_name}/{remote_path}")
            
        except Exception as e:
            result["error"] = f"Delete error: {e}"
            logger.error(f"❌ {result['error']}")
            
        return result
    
    def run_full_test(self, test_file_path: Optional[str] = None) -> Dict[str, Any]:
        """Run a complete test suite"""
        logger.info("🚀 Starting GCP Storage Full Test Suite")
        logger.info("=" * 50)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "bucket_name": self.bucket_name,
            "tests": {}
        }
        
        # Test 1: Authentication
        logger.info("\n1️⃣ Testing Authentication...")
        auth_result = self.test_authentication()
        results["tests"]["authentication"] = auth_result
        
        if not auth_result["success"]:
            logger.error("❌ Authentication failed. Stopping tests.")
            return results
        
        # Test 2: Bucket Access
        logger.info("\n2️⃣ Testing Bucket Access...")
        bucket_result = self.test_bucket_access()
        results["tests"]["bucket_access"] = bucket_result
        
        if not bucket_result["success"]:
            logger.error("❌ Bucket access failed. Stopping tests.")
            return results
        
        # Test 3: List Files
        logger.info("\n3️⃣ Testing List Files...")
        list_result = self.test_list_files()
        results["tests"]["list_files"] = list_result
        
        # Test 4: File Upload (if test file provided)
        if test_file_path and os.path.exists(test_file_path):
            logger.info("\n4️⃣ Testing File Upload...")
            upload_result = self.test_file_upload(test_file_path)
            results["tests"]["file_upload"] = upload_result
            
            # Test 5: File Download (if upload was successful)
            if upload_result["success"]:
                logger.info("\n5️⃣ Testing File Download...")
                download_result = self.test_file_download(upload_result["remote_path"])
                results["tests"]["file_download"] = download_result
                
                # Test 6: File Delete (if upload was successful)
                logger.info("\n6️⃣ Testing File Delete...")
                delete_result = self.test_delete_file(upload_result["remote_path"])
                results["tests"]["file_delete"] = delete_result
        else:
            logger.info("\n4️⃣ Skipping File Upload/Download tests (no test file provided)")
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("📊 Test Summary:")
        
        passed = 0
        total = len(results["tests"])
        
        for test_name, test_result in results["tests"].items():
            status = "✅ PASS" if test_result.get("success", False) else "❌ FAIL"
            logger.info(f"   {test_name}: {status}")
            if test_result.get("success", False):
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! GCP Storage is working correctly.")
        else:
            logger.warning("⚠️  Some tests failed. Check the logs above for details.")
        
        return results

def main():
    """Main function to run the GCP storage test"""
    print("🔧 GCP File Storage Connection Test")
    print("=" * 40)
    
    # Configuration
    bucket_name = input("Enter your GCS bucket name: ").strip()
    if not bucket_name:
        print("❌ Bucket name is required")
        return
    
    project_id = input("Enter your GCP project ID (optional, press Enter to auto-detect): ").strip()
    if not project_id:
        project_id = None
    
    # Use the specified default credentials file
    credentials_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    
    if os.path.exists(credentials_path):
        print(f"✅ Using default credentials from: {credentials_path}")
    else:
        print(f"❌ Default credentials file not found: {credentials_path}")
        print("💡 Make sure you've run 'gcloud auth application-default login'")
        return
    
    # Create tester
    tester = GCPStorageTester(bucket_name, project_id, credentials_path)
    
    # Ask for test file
    test_file = input("Enter path to test file for upload/download (optional, press Enter to skip): ").strip()
    if not test_file or not os.path.exists(test_file):
        test_file = None
        print("ℹ️  No test file provided, upload/download tests will be skipped")
    
    # Run tests
    results = tester.run_full_test(test_file)

    print(results)

if __name__ == "__main__":
    main()
