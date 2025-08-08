#!/usr/bin/env python3
"""
GCS Upload Script for vicino.ai
Uploads existing local images to GCS and updates metadata files
"""

import os
import json
import pathlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import tempfile
import shutil

# GCP Storage imports
try:
    from google.cloud import storage
    from google.oauth2 import credentials as user_credentials
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    print("❌ Google Cloud Storage library not installed. Install with: pip install google-cloud-storage")
    GCP_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gcs_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GCSUploader:
    def __init__(self, bucket_name: str = "vicino.ai", credentials_path: str = None):
        self.bucket_name = bucket_name
        self.gcp_storage_client = None
        self.upload_stats = {
            "total_sessions": 0,
            "total_iterations": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "metadata_updates": 0,
            "errors": []
        }
        
        if not GCP_AVAILABLE:
            raise ValueError("GCP libraries not available")
        
        self._initialize_gcp_client(credentials_path)
    
    def _initialize_gcp_client(self, credentials_path: str = None):
        """Initialize GCP Storage client"""
        try:
            # Use the same configuration as the main app
            GCP_PROJECT_ID = "fabled-pivot-468319-q2"
            GCP_CREDENTIALS_PATH = "/Users/Interstellar/.config/gcloud/application_default_credentials.json"
            
            if credentials_path and os.path.exists(credentials_path):
                # Load credentials from specified file
                with open(credentials_path, 'r') as f:
                    cred_data = json.load(f)
                
                if 'type' in cred_data and cred_data['type'] == 'service_account':
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
                else:
                    credentials = user_credentials.Credentials.from_authorized_user_file(credentials_path)
            elif os.path.exists(GCP_CREDENTIALS_PATH):
                # Load credentials from the default credentials file
                with open(GCP_CREDENTIALS_PATH, 'r') as f:
                    cred_data = json.load(f)
                
                if 'type' in cred_data and cred_data['type'] == 'service_account':
                    credentials = service_account.Credentials.from_service_account_file(GCP_CREDENTIALS_PATH)
                else:
                    credentials = user_credentials.Credentials.from_authorized_user_file(GCP_CREDENTIALS_PATH)
            else:
                # Use application default credentials
                credentials = None
            
            # Initialize client with project ID
            self.gcp_storage_client = storage.Client(project=GCP_PROJECT_ID, credentials=credentials)
            logger.info(f"✅ GCP Storage client initialized for bucket: {self.bucket_name}, project: {GCP_PROJECT_ID}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GCP client: {e}")
            raise
    
    def find_local_images(self) -> List[Dict]:
        """Find all sessions with local images that need GCS upload"""
        sessions_to_upload = []
        generated_images_dir = pathlib.Path("generated_images")
        
        if not generated_images_dir.exists():
            logger.warning("Generated images directory not found")
            return sessions_to_upload
        
        for session_dir in generated_images_dir.glob("session_*"):
            session_id = session_dir.name.replace("session_", "")
            metadata_files = list(session_dir.glob("metadata_*.json"))
            
            if not metadata_files:
                continue
            
            session_data = {
                "session_id": session_id,
                "iterations": [],
                "has_gcs_images": False
            }
            
            for metadata_file in sorted(metadata_files):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    iteration = metadata.get("iteration", 1)
                    image_url = metadata.get("image_url", "")
                    local_image_path = metadata.get("local_image_path", "")
                    gcs_image_path = metadata.get("gcs_image_path", "")
                    gcs_url = metadata.get("gcs_url", "")
                    
                    # Check if we have a local image path
                    local_path = None
                    if image_url and image_url.startswith("file://"):
                        local_path = image_url.replace("file://", "")
                    elif local_image_path:
                        local_path = local_image_path.replace("file://", "")
                    
                    # Check if local file exists
                    local_exists = local_path and os.path.exists(local_path)
                    
                    # Check if already has GCS data
                    has_gcs = bool(gcs_image_path or gcs_url)
                    
                    if has_gcs:
                        session_data["has_gcs_images"] = True
                    
                    iteration_data = {
                        "iteration": iteration,
                        "metadata_file": str(metadata_file),
                        "local_path": local_path,
                        "local_exists": local_exists,
                        "has_gcs": has_gcs,
                        "gcs_image_path": gcs_image_path,
                        "gcs_url": gcs_url,
                        "target_object": metadata.get("target_object", ""),
                        "timestamp": metadata.get("timestamp", "")
                    }
                    
                    session_data["iterations"].append(iteration_data)
                    
                except Exception as e:
                    logger.error(f"Error reading metadata file {metadata_file}: {e}")
            
            # Only include sessions that need GCS upload
            if session_data["iterations"]:
                sessions_to_upload.append(session_data)
        
        return sessions_to_upload
    
    def upload_image_to_gcs(self, local_path: str, session_id: str, iteration: int, target_object: str) -> Tuple[bool, str, str]:
        """Upload a single image to GCS"""
        try:
            if not os.path.exists(local_path):
                return False, "", f"Local file not found: {local_path}"
            
            # Generate GCS path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"iteration_{iteration:02d}_{timestamp}.png"
            gcs_path = f"generated_images/session_{session_id}/{filename}"
            
            # Upload to GCS
            bucket = self.gcp_storage_client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_path)
            
            # Set metadata
            blob.metadata = {
                "session_id": session_id,
                "iteration": str(iteration),
                "target_object": target_object,
                "upload_timestamp": timestamp,
                "original_filename": os.path.basename(local_path)
            }
            
            # Upload the file
            blob.upload_from_filename(local_path)
            
            # Note: Don't call make_public() for uniform bucket-level access
            # The bucket should be configured to allow public read access
            
            # Generate public URL (assuming bucket is configured for public access)
            gcs_url = f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"
            
            logger.info(f"✅ Uploaded: {local_path} -> {gcs_path}")
            return True, gcs_path, gcs_url
            
        except Exception as e:
            error_msg = f"Failed to upload {local_path}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, "", error_msg
    
    def update_metadata_file(self, metadata_file: str, gcs_path: str, gcs_url: str) -> bool:
        """Update metadata file with GCS information"""
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Add GCS information
            metadata["gcs_image_path"] = gcs_path
            metadata["gcs_url"] = gcs_url
            metadata["gcs_upload_timestamp"] = datetime.now().isoformat()
            
            # Write back to file
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Updated metadata: {metadata_file}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to update metadata {metadata_file}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False
    
    def process_session(self, session_data: Dict) -> Dict:
        """Process a single session for GCS upload"""
        session_id = session_data["session_id"]
        session_stats = {
            "session_id": session_id,
            "iterations_processed": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "metadata_updates": 0,
            "errors": []
        }
        
        logger.info(f"🔄 Processing session: {session_id}")
        
        for iteration_data in session_data["iterations"]:
            iteration = iteration_data["iteration"]
            local_path = iteration_data["local_path"]
            local_exists = iteration_data["local_exists"]
            has_gcs = iteration_data["has_gcs"]
            metadata_file = iteration_data["metadata_file"]
            target_object = iteration_data["target_object"]
            
            session_stats["iterations_processed"] += 1
            
            # Skip if already has GCS data
            if has_gcs:
                logger.info(f"⏭️  Skipping iteration {iteration} - already has GCS data")
                continue
            
            # Skip if local file doesn't exist
            if not local_exists:
                error_msg = f"Local file not found: {local_path}"
                session_stats["errors"].append(error_msg)
                session_stats["failed_uploads"] += 1
                logger.warning(f"⚠️  {error_msg}")
                continue
            
            # Upload to GCS
            success, gcs_path, gcs_url = self.upload_image_to_gcs(
                local_path, session_id, iteration, target_object
            )
            
            if success:
                session_stats["successful_uploads"] += 1
                
                # Update metadata file
                if self.update_metadata_file(metadata_file, gcs_path, gcs_url):
                    session_stats["metadata_updates"] += 1
                else:
                    session_stats["errors"].append(f"Failed to update metadata for iteration {iteration}")
            else:
                session_stats["failed_uploads"] += 1
                session_stats["errors"].append(f"Failed to upload iteration {iteration}: {gcs_url}")
        
        return session_stats
    
    def run_upload(self) -> Dict:
        """Run the complete GCS upload process"""
        logger.info("🚀 Starting GCS upload process...")
        
        # Find sessions to process
        sessions_to_upload = self.find_local_images()
        logger.info(f"📋 Found {len(sessions_to_upload)} sessions to process")
        
        # Process each session
        for session_data in sessions_to_upload:
            session_stats = self.process_session(session_data)
            
            # Update global stats
            self.upload_stats["total_sessions"] += 1
            self.upload_stats["total_iterations"] += session_stats["iterations_processed"]
            self.upload_stats["successful_uploads"] += session_stats["successful_uploads"]
            self.upload_stats["failed_uploads"] += session_stats["failed_uploads"]
            self.upload_stats["metadata_updates"] += session_stats["metadata_updates"]
            self.upload_stats["errors"].extend(session_stats["errors"])
        
        return self.upload_stats
    
    def generate_report(self, stats: Dict) -> str:
        """Generate a comprehensive upload report"""
        success_rate = (stats["successful_uploads"] / max(stats["total_iterations"], 1)) * 100
        
        report = f"""
=== GCS Upload Report ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 SUMMARY:
- Total Sessions Processed: {stats['total_sessions']}
- Total Iterations Processed: {stats['total_iterations']}
- Successful Uploads: {stats['successful_uploads']}
- Failed Uploads: {stats['failed_uploads']}
- Metadata Updates: {stats['metadata_updates']}
- Success Rate: {success_rate:.1f}%

"""
        
        if stats["errors"]:
            report += "❌ ERRORS:\n"
            for error in stats["errors"][:10]:  # Show first 10 errors
                report += f"- {error}\n"
            
            if len(stats["errors"]) > 10:
                report += f"... and {len(stats['errors']) - 10} more errors\n"
        
        return report

def main():
    """Main function to run the GCS upload process"""
    print("🚀 Vicino.ai GCS Upload Script")
    print("=" * 50)
    
    if not GCP_AVAILABLE:
        print("❌ GCP libraries not available. Please install:")
        print("   pip install google-cloud-storage")
        return
    
    try:
        # Initialize uploader
        uploader = GCSUploader()
        
        # Run upload process
        stats = uploader.run_upload()
        
        # Generate and display report
        report = uploader.generate_report(stats)
        print(report)
        
        # Save report to file
        with open("gcs_upload_report.txt", "w") as f:
            f.write(report)
        print("📄 Report saved to gcs_upload_report.txt")
        
        if stats["successful_uploads"] > 0:
            print("🎉 Upload process completed successfully!")
        else:
            print("⚠️  No images were uploaded. Check the errors above.")
            
    except Exception as e:
        print(f"❌ Upload process failed: {e}")
        logger.error(f"Upload process failed: {e}")

if __name__ == "__main__":
    main()
