#!/usr/bin/env python3
"""
Image Utilities for vicino.ai
Handles image management, availability checking, and syncing
"""

import os
import json
import pathlib
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

def scan_missing_images() -> Dict[str, List[Dict]]:
    """Scan for sessions with missing GCS images and return detailed report"""
    missing_report = {
        "sessions_with_missing_images": [],
        "total_sessions": 0,
        "total_iterations": 0,
        "missing_iterations": 0,
        "gcs_available_iterations": 0
    }
    
    generated_images_dir = pathlib.Path("generated_images")
    if not generated_images_dir.exists():
        logger.warning("Generated images directory not found")
        return missing_report
    
    # Find all session directories
    for session_dir in generated_images_dir.glob("session_*"):
        session_id = session_dir.name.replace("session_", "")
        missing_report["total_sessions"] += 1
        
        # Find metadata files for this session
        metadata_files = list(session_dir.glob("metadata_*.json"))
        if not metadata_files:
            continue
        
        session_missing = {
            "session_id": session_id,
            "missing_iterations": [],
            "total_iterations": len(metadata_files),
            "available_iterations": 0,
            "gcs_available_iterations": 0
        }
        
        missing_report["total_iterations"] += len(metadata_files)
        
        for metadata_file in sorted(metadata_files):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                iteration = metadata.get("iteration", 1)
                gcs_image_path = metadata.get("gcs_image_path", "")
                gcs_url = metadata.get("gcs_url", "")
                
                # Check if GCS image is available
                gcs_available = bool(gcs_image_path or gcs_url)
                
                if gcs_available:
                    session_missing["gcs_available_iterations"] += 1
                    missing_report["gcs_available_iterations"] += 1
                    session_missing["available_iterations"] += 1
                else:
                    session_missing["missing_iterations"].append({
                        "iteration": iteration,
                        "metadata_file": str(metadata_file),
                        "gcs_path": gcs_image_path,
                        "gcs_url": gcs_url,
                        "gcs_available": gcs_available
                    })
                    missing_report["missing_iterations"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing metadata file {metadata_file}: {e}")
        
        if session_missing["missing_iterations"]:
            missing_report["sessions_with_missing_images"].append(session_missing)
    
    return missing_report

def get_image_info(session_id: str, iteration: int) -> Optional[Dict]:
    """Get detailed information about a specific image"""
    try:
        session_dir = pathlib.Path(f"generated_images/session_{session_id}")
        if not session_dir.exists():
            return None
        
        metadata_file = session_dir / f"metadata_iteration_{iteration:02d}.json"
        if not metadata_file.exists():
            return None
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        local_image_path = metadata.get("local_image_path", "")
        gcs_image_path = metadata.get("gcs_image_path", "")
        gcs_url = metadata.get("gcs_url", "")
        
        # Check local availability
        local_available = False
        local_size = 0
        if local_image_path:
            file_path = local_image_path.replace("file://", "")
            if os.path.exists(file_path):
                local_available = True
                local_size = os.path.getsize(file_path)
        
        return {
            "session_id": session_id,
            "iteration": iteration,
            "local_path": local_image_path,
            "local_available": local_available,
            "local_size": local_size,
            "gcs_path": gcs_image_path,
            "gcs_url": gcs_url,
            "target_object": metadata.get("target_object", ""),
            "timestamp": metadata.get("timestamp", ""),
            "evaluation": metadata.get("evaluation_results", {})
        }
        
    except Exception as e:
        logger.error(f"Error getting image info for session {session_id}, iteration {iteration}: {e}")
        return None

def cleanup_orphaned_files() -> Dict[str, int]:
    """Clean up orphaned image files that don't have corresponding metadata"""
    cleanup_report = {
        "orphaned_files_removed": 0,
        "orphaned_files_found": 0,
        "errors": []
    }
    
    generated_images_dir = pathlib.Path("generated_images")
    if not generated_images_dir.exists():
        return cleanup_report
    
    for session_dir in generated_images_dir.glob("session_*"):
        try:
            # Get all PNG files in the session directory
            png_files = list(session_dir.glob("*.png"))
            metadata_files = list(session_dir.glob("metadata_*.json"))
            
            # Extract expected image paths from metadata
            expected_images = set()
            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    local_path = metadata.get("local_image_path", "")
                    if local_path:
                        file_path = local_path.replace("file://", "")
                        expected_images.add(os.path.basename(file_path))
                except Exception as e:
                    logger.warning(f"Error reading metadata file {metadata_file}: {e}")
            
            # Find orphaned files
            for png_file in png_files:
                if png_file.name not in expected_images:
                    cleanup_report["orphaned_files_found"] += 1
                    try:
                        png_file.unlink()
                        cleanup_report["orphaned_files_removed"] += 1
                        logger.info(f"Removed orphaned file: {png_file}")
                    except Exception as e:
                        cleanup_report["errors"].append(f"Failed to remove {png_file}: {e}")
                        
        except Exception as e:
            cleanup_report["errors"].append(f"Error processing session {session_dir.name}: {e}")
    
    return cleanup_report

def generate_image_report() -> str:
    """Generate a comprehensive report of GCS image status"""
    missing_report = scan_missing_images()
    cleanup_report = cleanup_orphaned_files()
    
    report = f"""
=== Vicino.ai GCS Image Status Report ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 SUMMARY:
- Total Sessions: {missing_report['total_sessions']}
- Total Iterations: {missing_report['total_iterations']}
- GCS Available Iterations: {missing_report['gcs_available_iterations']}
- Missing GCS Images: {missing_report['missing_iterations']}
- Sessions with Missing Images: {len(missing_report['sessions_with_missing_images'])}

📈 AVAILABILITY:
- GCS Image Success Rate: {(missing_report['gcs_available_iterations'] / missing_report['total_iterations'] * 100):.1f}% ({missing_report['gcs_available_iterations']}/{missing_report['total_iterations']})

🧹 CLEANUP:
- Orphaned Files Found: {cleanup_report['orphaned_files_found']}
- Orphaned Files Removed: {cleanup_report['orphaned_files_removed']}
- Cleanup Errors: {len(cleanup_report['errors'])}

📋 DETAILED MISSING GCS IMAGES:
"""
    
    for session in missing_report['sessions_with_missing_images']:
        report += f"""
Session: {session['session_id']}
- Total Iterations: {session['total_iterations']}
- GCS Available: {session['gcs_available_iterations']}
- Missing: {len(session['missing_iterations'])}
"""
        
        for missing in session['missing_iterations']:
            report += f"  - Iteration {missing['iteration']}: GCS Path: {missing['gcs_path'] or 'None'}, URL: {missing['gcs_url'] or 'None'}\n"
    
    if cleanup_report['errors']:
        report += "\n❌ CLEANUP ERRORS:\n"
        for error in cleanup_report['errors']:
            report += f"- {error}\n"
    
    return report

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 Scanning for missing images...")
    report = generate_image_report()
    print(report)
    
    # Save report to file
    with open("image_status_report.txt", "w") as f:
        f.write(report)
    print("\n📄 Report saved to image_status_report.txt")
