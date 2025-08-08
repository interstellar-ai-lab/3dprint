#!/usr/bin/env python3
"""
Studio Module
Handles studio-specific functionality like serving generated images, metadata, etc.
"""

from flask import Blueprint, request, jsonify, send_file, redirect
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import pathlib
import zipfile
import uuid
from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
import shutil
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for studio routes
studio_bp = Blueprint('studio', __name__)

# Global variables to be set by main app
gcp_storage_client = None
GCP_BUCKET_NAME = None

def init_studio_module(gcp_client, bucket_name):
    """Initialize studio module with GCP client"""
    global gcp_storage_client, GCP_BUCKET_NAME
    gcp_storage_client = gcp_client
    GCP_BUCKET_NAME = bucket_name

# Simple in-memory registry of imported models
_imported_models: Dict[str, pathlib.Path] = {}

def _ensure_models_dir() -> pathlib.Path:
    base_dir = pathlib.Path('downloads') / 'studio_models'
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def _parse_gcs_from_url(url: str) -> Optional[Dict[str, str]]:
    """Return {bucket, path} if URL is GCS (gs:// or https://storage.googleapis.com/...), else None."""
    try:
        if url.startswith('gs://'):
            # gs://bucket/path/to/file
            no_scheme = url.replace('gs://', '', 1)
            parts = no_scheme.split('/', 1)
            if len(parts) == 2:
                return {'bucket': parts[0], 'path': parts[1]}
        parsed = urlparse(url)
        if parsed.scheme in ('http', 'https') and parsed.netloc == 'storage.googleapis.com':
            # /bucket/path
            if parsed.path.startswith('/'):
                path_parts = parsed.path[1:].split('/', 1)
                if len(path_parts) == 2:
                    return {'bucket': path_parts[0], 'path': path_parts[1]}
    except Exception:
        return None
    return None

def _download_zip(zip_url: str, dest_path: pathlib.Path) -> None:
    # Try GCS download when applicable and client available
    gcs_info = _parse_gcs_from_url(zip_url)
    if gcs_info and gcp_storage_client:
        bucket = gcp_storage_client.bucket(gcs_info['bucket'])
        blob = bucket.blob(gcs_info['path'])
        if not blob.exists():
            raise FileNotFoundError(f"GCS object not found: gs://{gcs_info['bucket']}/{gcs_info['path']}")
        blob.download_to_filename(str(dest_path))
        return

    # Fallback to HTTP(S) download
    try:
        with urlopen(zip_url) as response, open(dest_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except HTTPError as e:
        # Re-raise with clear message to map status in handler
        raise HTTPError(e.url, e.code, f"HTTP Error {e.code}: {e.reason}", hdrs=e.hdrs, fp=e.fp)
    except URLError as e:
        raise RuntimeError(f"Network error while downloading ZIP: {e.reason}")

def _extract_zip(zip_path: pathlib.Path, extract_dir: pathlib.Path) -> None:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

def _scan_for_model_files(extract_dir: pathlib.Path) -> Dict[str, Optional[str]]:
    obj_files: List[pathlib.Path] = []
    mtl_files: List[pathlib.Path] = []
    gltf_files: List[pathlib.Path] = []
    glb_files: List[pathlib.Path] = []

    for root, _, files in os.walk(extract_dir):
        for fname in files:
            fpath = pathlib.Path(root) / fname
            lower = fname.lower()
            if lower.endswith('.obj'):
                obj_files.append(fpath)
            elif lower.endswith('.mtl'):
                mtl_files.append(fpath)
            elif lower.endswith('.gltf'):
                gltf_files.append(fpath)
            elif lower.endswith('.glb'):
                glb_files.append(fpath)

    # Prefer OBJ+MTL
    primary_obj = str(obj_files[0].relative_to(extract_dir)) if obj_files else None
    # Try to find matching MTL in same directory
    primary_mtl = None
    if primary_obj:
        obj_dir = (extract_dir / primary_obj).parent
        mtl_in_dir = [m for m in mtl_files if m.parent == obj_dir]
        if mtl_in_dir:
            primary_mtl = str(mtl_in_dir[0].relative_to(extract_dir))

    # If no OBJ, fall back to GLTF/GLB
    primary_gltf = str(gltf_files[0].relative_to(extract_dir)) if gltf_files else None
    primary_glb = str(glb_files[0].relative_to(extract_dir)) if glb_files else None

    return {
        'obj': primary_obj,
        'mtl': primary_mtl,
        'gltf': primary_gltf,
        'glb': primary_glb,
    }

@studio_bp.route('/api/studio/import-model', methods=['POST'])
def import_model():
    """Import a model ZIP from a URL, extract it, and return serving info."""
    try:
        data = request.get_json(force=True)
        zip_url = data.get('zip_url')
        if not zip_url:
            return jsonify({"error": "zip_url is required"}), 400

        base_dir = _ensure_models_dir()
        model_id = str(uuid.uuid4())
        zip_path = base_dir / f"{model_id}.zip"
        extract_dir = base_dir / model_id

        # Download and extract
        _download_zip(zip_url, zip_path)
        extract_dir.mkdir(parents=True, exist_ok=True)
        _extract_zip(zip_path, extract_dir)

        # Optionally remove zip to save space
        try:
            zip_path.unlink(missing_ok=True)  # type: ignore[arg-type]
        except TypeError:
            # Python < 3.8 fallback
            if zip_path.exists():
                zip_path.unlink()

        file_info = _scan_for_model_files(extract_dir)
        _imported_models[model_id] = extract_dir

        return jsonify({
            'model_id': model_id,
            'files': file_info,
            'serve_base_url': f"/api/studio/models/{model_id}/"
        })
    except HTTPError as e:
        logger.error(f"HTTP error importing model ZIP: {e}")
        return jsonify({"error": f"{e}"}), e.code
    except FileNotFoundError as e:
        logger.error(f"ZIP not found: {e}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error importing model ZIP: {e}")
        return jsonify({"error": str(e)}), 500

@studio_bp.route('/api/studio/models/<model_id>/<path:filename>')
def serve_imported_model_file(model_id: str, filename: str):
    """Serve a file from an imported model directory."""
    try:
        if model_id not in _imported_models:
            return jsonify({"error": "model_id not found"}), 404
        base_dir = _imported_models[model_id]
        target_path = (base_dir / filename).resolve()

        # Security: ensure path is within base_dir
        if not str(target_path).startswith(str(base_dir.resolve())):
            return jsonify({"error": "invalid path"}), 400
        if not target_path.exists():
            return jsonify({"error": "file not found"}), 404
        # Infer mimetype lightly
        mime = 'application/octet-stream'
        lower = target_path.name.lower()
        if lower.endswith('.mtl') or lower.endswith('.obj'):
            mime = 'text/plain'
        elif lower.endswith('.png'):
            mime = 'image/png'
        elif lower.endswith('.jpg') or lower.endswith('.jpeg'):
            mime = 'image/jpeg'
        elif lower.endswith('.gltf'):
            mime = 'model/gltf+json'
        elif lower.endswith('.glb'):
            mime = 'model/gltf-binary'
        return send_file(str(target_path), mimetype=mime)
    except Exception as e:
        logger.error(f"Error serving model file: {e}")
        return jsonify({"error": str(e)}), 500

# -------------------------------
# GCS public generated images APIs
# -------------------------------

def _public_gcs_url(gcs_path: str) -> str:
    return f"https://storage.googleapis.com/{GCP_BUCKET_NAME}/{gcs_path}"

def _get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', '34.187.201.209'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'vicinoAI123!')
    )

def _check_zipurl_for_image(imageurl: str) -> Optional[str]:
    """Check if an image has an associated zipurl in the database"""
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT zipurl FROM imageand3durl WHERE imageurl = %s", (imageurl,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error checking zipurl for image {imageurl}: {e}")
        return None

@studio_bp.route('/api/studio/gcs-sessions')
def list_gcs_sessions():
    """List session IDs found under generated_images/session_* in the GCS bucket."""
    try:
        if not gcp_storage_client:
            return jsonify({"error": "GCP Storage not available"}), 500
        bucket = gcp_storage_client.bucket(GCP_BUCKET_NAME)
        prefix = 'generated_images/session_'
        iterator = bucket.list_blobs(prefix=prefix)
        session_ids = set()
        for blob in iterator:
            # blob.name like generated_images/session_<id>/filename
            name = blob.name
            if not name.startswith(prefix):
                continue
            remainder = name[len(prefix):]
            parts = remainder.split('/', 1)
            if len(parts) >= 1 and parts[0]:
                session_ids.add(parts[0])
        sessions = sorted(session_ids)
        return jsonify({"sessions": sessions})
    except Exception as e:
        logger.error(f"Error listing GCS sessions: {e}")
        return jsonify({"error": str(e)}), 500

@studio_bp.route('/api/studio/gcs-session-images/<session_id>')
def list_gcs_session_images(session_id: str):
    """List public image URLs for a given session ID under generated_images/session_<id>/"""
    try:
        if not gcp_storage_client:
            return jsonify({"error": "GCP Storage not available"}), 500
        bucket = gcp_storage_client.bucket(GCP_BUCKET_NAME)
        prefix = f'generated_images/session_{session_id}/'
        iterator = bucket.list_blobs(prefix=prefix)
        images: List[Dict[str, Any]] = []
        for blob in iterator:
            lower = blob.name.lower()
            if lower.endswith('.png') or lower.endswith('.jpg') or lower.endswith('.jpeg'):
                public_url = _public_gcs_url(blob.name)
                print('public_url is: ', public_url)
                zipurl = _check_zipurl_for_image(public_url)
                images.append({
                    'gcs_image_path': blob.name,
                    'public_url': public_url,
                    'zipurl': zipurl,
                    'has_3d': bool(zipurl),
                    'size': getattr(blob, 'size', None),
                    'updated': getattr(blob, 'updated', None).isoformat() if getattr(blob, 'updated', None) else None,
                })
        # Sort by updated time or name
        images.sort(key=lambda x: x.get('updated') or x['gcs_image_path'])
        return jsonify({
            'session_id': session_id,
            'images': images,
        })
    except Exception as e:
        logger.error(f"Error listing images for session {session_id}: {e}")
        return jsonify({"error": str(e)}), 500

def get_sessions_from_files():
    """Get all sessions from the generated_images directory that have GCS images"""
    sessions = []
    generated_images_dir = pathlib.Path("generated_images")
    
    if not generated_images_dir.exists():
        return sessions
    
    # Find all session directories
    for session_dir in generated_images_dir.glob("session_*"):
        session_id = session_dir.name.replace("session_", "")
        
        # Find metadata files for this session
        metadata_files = list(session_dir.glob("metadata_*.json"))
        if not metadata_files:
            continue
        
        # Read the first metadata file to get session info
        try:
            with open(metadata_files[0], 'r') as f:
                first_metadata = json.load(f)
            
            # Get all iterations for this session
            iterations = []
            has_gcs_images = False
            
            for metadata_file in sorted(metadata_files):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Check if this iteration has GCS images
                    gcs_image_path = metadata.get("gcs_image_path", "")
                    gcs_url = metadata.get("gcs_url", "")
                    has_gcs = bool(gcs_image_path or gcs_url)
                    
                    if has_gcs:
                        has_gcs_images = True
                    
                    iterations.append({
                        "iteration": metadata.get("iteration", 1),
                        # Canonical object path
                        "gcs_image_path": gcs_image_path,
                        # Legacy public URL field
                        "gcs_url": gcs_url,
                        # New fields for clarity
                        "public_url": metadata.get("public_url", gcs_url),
                        "gsutil_uri": metadata.get("gsutil_uri", f"gs://{GCP_BUCKET_NAME}/{gcs_image_path}" if gcs_image_path else None),
                        "has_gcs_image": has_gcs,
                        "evaluation": metadata.get("evaluation_results", {}),
                        "metadata_file": str(metadata_file)
                    })
                except Exception as e:
                    logger.warning(f"Could not read metadata file {metadata_file}: {e}")
            
            # Only include sessions that have at least one GCS image
            if has_gcs_images:
                # Create session object
                session = {
                    "session_id": session_id,
                    "target_object": first_metadata.get("target_object", "Unknown"),
                    "mode": first_metadata.get("mode", "quick"),
                    "status": "completed",  # Assume completed if we have metadata
                    "iterations": iterations,
                    "timestamp": first_metadata.get("timestamp"),
                    "max_iterations": len(iterations),
                    "current_iteration": len(iterations),
                    "final_score": max([iter.get("evaluation", {}).get("scores", {}).get("overall", 0) for iter in iterations], default=0),
                    "gcs_images_count": sum(1 for iter in iterations if iter.get("has_gcs_image", False))
                }
                
                sessions.append(session)
            
        except Exception as e:
            logger.warning(f"Could not process session {session_id}: {e}")
    
    return sessions

@studio_bp.route('/api/sessions')
def list_sessions():
    """List all sessions with generated images; ensure public_url is included for filtering."""
    try:
        sessions = get_sessions_from_files()
        # No server-side filter; frontend enforces allowed GCS prefix
        return jsonify({"sessions": sessions})
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({"error": str(e)}), 500

@studio_bp.route('/api/session/<session_id>')
def get_session(session_id):
    """Get detailed information about a specific session"""
    try:
        sessions = get_sessions_from_files()
        session = next((s for s in sessions if s["session_id"] == session_id), None)
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify(session)
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        return jsonify({"error": str(e)}), 500

@studio_bp.route('/api/image/<session_id>/<int:iteration>')
def get_iteration_image(session_id, iteration):
    """Get PNG image for a specific iteration from GCS only"""
    try:
        # Find the session directory
        session_dir = pathlib.Path(f"generated_images/session_{session_id}")
        if not session_dir.exists():
            return jsonify({"error": "Session not found"}), 404
        
        # Find the metadata file for this iteration
        metadata_file = session_dir / f"metadata_iteration_{iteration:02d}.json"
        if not metadata_file.exists():
            return jsonify({"error": "Iteration not found"}), 404
        
        # Read metadata to get GCS image path
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Get GCS image path and URL
        gcs_image_path = metadata.get("gcs_image_path", "")
        gcs_url = metadata.get("gcs_url", "")
        
        # Check if we have GCS information
        if not gcs_image_path and not gcs_url:
            logger.warning(f"No GCS image path found for session {session_id}, iteration {iteration}")
            return jsonify({"error": "No GCS image information found"}), 404
        
        # Always download from GCS and serve (since bucket is not publicly accessible)
        if gcs_image_path and gcp_storage_client:
            try:
                # Download from GCS
                bucket = gcp_storage_client.bucket(GCP_BUCKET_NAME)
                blob = bucket.blob(gcs_image_path)
                
                if blob.exists():
                    logger.info(f"Serving GCS image: {gcs_image_path}")
                    # Download to temporary file
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                        blob.download_to_filename(temp_file.name)
                        temp_path = temp_file.name
                    
                    # Serve the file
                    response = send_file(temp_path, mimetype='image/png')
                    
                    # Clean up the temporary file after sending
                    import atexit
                    atexit.register(lambda: os.unlink(temp_path) if os.path.exists(temp_path) else None)
                    
                    return response
                else:
                    logger.warning(f"GCS blob does not exist: {gcs_image_path}")
                    return jsonify({"error": "Image not found in GCS"}), 404
                    
            except Exception as e:
                logger.error(f"Failed to serve GCS image {gcs_image_path}: {e}")
                return jsonify({"error": f"Failed to download from GCS: {str(e)}"}), 500
        
        # No GCS client available
        if not gcp_storage_client:
            logger.error("GCP Storage client not available")
            return jsonify({"error": "GCS not configured"}), 500
        
        # No image found
        logger.warning(f"No GCS image found for session {session_id}, iteration {iteration}")
        return jsonify({"error": "Image not found in GCS"}), 404
        
    except Exception as e:
        logger.error(f"Error serving image for session {session_id}, iteration {iteration}: {e}")
        return jsonify({"error": str(e)}), 500

@studio_bp.route('/api/gcs-image/<path:gcs_path>')
def serve_gcs_image(gcs_path):
    """Serve image from GCS by downloading and serving it"""
    try:
        if not gcp_storage_client:
            return jsonify({"error": "GCP Storage not available"}), 500
        
        # Download the image from GCS
        bucket = gcp_storage_client.bucket(GCP_BUCKET_NAME)
        blob = bucket.blob(gcs_path)
        
        if not blob.exists():
            return jsonify({"error": "Image not found in GCS"}), 404
        
        # Download to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            blob.download_to_filename(temp_file.name)
            temp_path = temp_file.name
        
        # Serve the file
        response = send_file(temp_path, mimetype='image/png')
        
        # Clean up the temporary file after sending
        import atexit
        atexit.register(lambda: os.unlink(temp_path) if os.path.exists(temp_path) else None)
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving GCS image {gcs_path}: {e}")
        return jsonify({"error": str(e)}), 500

@studio_bp.route('/api/image-status/<session_id>/<int:iteration>')
def check_image_status(session_id, iteration):
    """Check if image exists in GCS and return status information"""
    try:
        # Find the session directory
        session_dir = pathlib.Path(f"generated_images/session_{session_id}")
        if not session_dir.exists():
            return jsonify({
                "available": False,
                "error": "Session not found",
                "sources": []
            }), 404
        
        # Find the metadata file for this iteration
        metadata_file = session_dir / f"metadata_iteration_{iteration:02d}.json"
        if not metadata_file.exists():
            return jsonify({
                "available": False,
                "error": "Iteration not found",
                "sources": []
            }), 404
        
        # Read metadata to get GCS information
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        sources = []
        available = False
        
        # Check GCS image
        gcs_image_path = metadata.get("gcs_image_path", "")
        gcs_url = metadata.get("gcs_url", "")
        
        if gcs_image_path and gcp_storage_client:
            try:
                bucket = gcp_storage_client.bucket(GCP_BUCKET_NAME)
                blob = bucket.blob(gcs_image_path)
                
                if blob.exists():
                    sources.append({
                        "type": "gcs",
                        "path": gcs_image_path,
                        "url": gcs_url,
                        "available": True,
                        "size": blob.size if hasattr(blob, 'size') else None
                    })
                    available = True
                else:
                    sources.append({
                        "type": "gcs",
                        "path": gcs_image_path,
                        "url": gcs_url,
                        "available": False,
                        "error": "Blob not found in GCS"
                    })
            except Exception as e:
                sources.append({
                    "type": "gcs",
                    "path": gcs_image_path,
                    "url": gcs_url,
                    "available": False,
                    "error": str(e)
                })
        elif gcs_url:
            # If we have a GCS URL but no path, mark as available
            sources.append({
                "type": "gcs_url",
                "url": gcs_url,
                "available": True
            })
            available = True
        else:
            sources.append({
                "type": "gcs",
                "available": False,
                "error": "No GCS information found"
            })
        
        return jsonify({
            "available": available,
            "sources": sources,
            "session_id": session_id,
            "iteration": iteration,
            "target_object": metadata.get("target_object", ""),
            "timestamp": metadata.get("timestamp", "")
        })
        
    except Exception as e:
        logger.error(f"Error checking image status for session {session_id}, iteration {iteration}: {e}")
        return jsonify({
            "available": False,
            "error": str(e),
            "sources": []
        }), 500

@studio_bp.route('/api/studio/health')
def studio_health():
    """Studio-specific health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "studio-module",
        "timestamp": datetime.now().isoformat()
    })
