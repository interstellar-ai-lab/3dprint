#!/usr/bin/env python3
"""
Fix GCS URLs in metadata files
Updates gs:// URLs to https:// URLs for proper image serving
"""

import os
import json
import pathlib
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_gcs_urls():
    """Fix GCS URLs in all metadata files"""
    fixed_count = 0
    total_count = 0
    
    generated_images_dir = pathlib.Path("generated_images")
    if not generated_images_dir.exists():
        logger.warning("Generated images directory not found")
        return
    
    # Find all metadata files
    for metadata_file in generated_images_dir.rglob("metadata_*.json"):
        total_count += 1
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            updated = False
            
            # Fix gcs_url if it's using gs:// format
            gcs_url = metadata.get("gcs_url", "")
            if gcs_url.startswith("gs://"):
                # Convert gs://vicino.ai/path to https://storage.googleapis.com/vicino.ai/path
                new_url = gcs_url.replace("gs://", "https://storage.googleapis.com/")
                metadata["gcs_url"] = new_url
                updated = True
                logger.info(f"Fixed URL: {gcs_url} -> {new_url}")
            
            # Fix gcs_image_path if it's missing
            gcs_image_path = metadata.get("gcs_image_path", "")
            if not gcs_image_path and gcs_url:
                # Extract path from URL
                if gcs_url.startswith("https://storage.googleapis.com/"):
                    path = gcs_url.replace("https://storage.googleapis.com/", "")
                    metadata["gcs_image_path"] = path
                    updated = True
                    logger.info(f"Added missing gcs_image_path: {path}")
            
            # Write back if updated
            if updated:
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                fixed_count += 1
                
        except Exception as e:
            logger.error(f"Error processing {metadata_file}: {e}")
    
    logger.info(f"Fixed {fixed_count} out of {total_count} metadata files")
    return fixed_count, total_count

def main():
    """Main function"""
    print("🔧 Fixing GCS URLs in metadata files...")
    fixed, total = fix_gcs_urls()
    print(f"✅ Fixed {fixed} out of {total} metadata files")
    
    if fixed > 0:
        print("🔄 Please restart your web application to see the changes")
    else:
        print("ℹ️  No URLs needed fixing")

if __name__ == "__main__":
    main()
