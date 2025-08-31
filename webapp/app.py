#!/usr/bin/env python3
"""
Multi agent to generate 3D images - Flask Web App for EC2 Deployment
"""

from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
import json
import os
import sys
import uuid
import pathlib
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import base64
from PIL import Image
import io
from openai import OpenAI, AsyncOpenAI
import aiohttp
import threading
import logging
import stripe
import re
import unicodedata


# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webapp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be compatible with cloud storage services.
    Removes or replaces non-ASCII characters, special characters, and spaces.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for cloud storage
    """
    # Normalize unicode characters (convert to closest ASCII equivalent)
    filename = unicodedata.normalize('NFKD', filename)
    
    # Replace non-ASCII characters with their closest ASCII equivalent or remove them
    # This handles Chinese, Japanese, Korean, Arabic, etc.
    filename = ''.join(c for c in filename if ord(c) < 128)
    
    # Replace spaces and special characters with underscores
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
    
    # Limit length to avoid issues
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

# Import studio module
# Add the project root directory to Python path
project_root = os.path.join(os.path.dirname(__file__), '..')
project_root = os.path.abspath(project_root)
sys.path.insert(0, project_root)

try:
    from studio_module import create_supabase_studio_manager
    SUPABASE_STUDIO_AVAILABLE = True
    logger.info("✅ Studio module imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Studio module not available: {e}")
    SUPABASE_STUDIO_AVAILABLE = False

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://3dviewer.net", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8001", "http://127.0.0.1:8001", "https://vicino.ai", "https://www.vicino.ai", "https://vicino.ai:8001", "https://vicino.ai:443", "http://vicino.ai", "http://www.vicino.ai", "http://vicino.ai:8001"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With", "Cache-Control", "Pragma"],
        "supports_credentials": True
    }
})

# Store active sessions (in production, use a proper database)
active_sessions = {}

# OpenAI clients
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Image generation configuration
DEFAULT_IMAGE_SIZE = "1024x1024"  # Default to portrait to avoid cutting off objects
SUPPORTED_IMAGE_SIZES = ["1024x1024", "1024x1536", "1536x1024"]

# Validate image size
if DEFAULT_IMAGE_SIZE not in SUPPORTED_IMAGE_SIZES:
    logger.warning(f"⚠️ Invalid DEFAULT_IMAGE_SIZE '{DEFAULT_IMAGE_SIZE}', using '1024x1024'")
    DEFAULT_IMAGE_SIZE = "1024x1024"

logger.info(f"🎨 Using default image size: {DEFAULT_IMAGE_SIZE}")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai_sync_client = OpenAI(api_key=OPENAI_API_KEY)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET_NAME = "generated-images-bucket"

# Initialize Supabase client if available
try:
    from supabase import create_client, Client
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        # Use service key for server-side operations (bypasses RLS)
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        SUPABASE_AVAILABLE = True
        logger.info("✅ Supabase client initialized successfully with service key")
    else:
        supabase_client = None
        SUPABASE_AVAILABLE = False
        logger.warning("⚠️ Supabase credentials not found, wallet features disabled")
except ImportError:
    supabase_client = None
    SUPABASE_AVAILABLE = False
    logger.warning("⚠️ Supabase not available, wallet features disabled")

# Credit management functions
def get_user_from_token():
    """Extract and verify user from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, "Authorization header required"
    
    token = auth_header.split(' ')[1]
    
    if not SUPABASE_AVAILABLE:
        return None, "Database not available"
    
    try:
        user_response = supabase_client.auth.get_user(token)
        user = user_response.user
        
        if not user:
            return None, "Invalid token"
        
        return user, None
        
    except Exception as e:
        logger.error(f"❌ Token verification failed: {str(e)}")
        return None, "Invalid token"

def check_user_balance(user_id, required_credits):
    """Check if user has enough credits for an operation"""
    try:
        result = supabase_client.table('user_wallets').select('balance').eq('user_id', user_id).execute()
        
        if result.data:
            balance = float(result.data[0]['balance'])
        else:
            # Create wallet if it doesn't exist with welcome bonus
            balance = create_new_user_wallet(user_id)
        
        return balance >= required_credits, balance
        
    except Exception as e:
        logger.error(f"❌ Error checking user balance: {str(e)}")
        return False, 0.0

def deduct_credits(user_id, amount, description):
    """Deduct credits from user's wallet and record transaction"""
    try:
        # Get current balance
        result = supabase_client.table('user_wallets').select('balance').eq('user_id', user_id).execute()
        
        if result.data:
            current_balance = float(result.data[0]['balance'])
            new_balance = current_balance - amount
            
            # Update wallet balance
            supabase_client.table('user_wallets').update({
                'balance': new_balance,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).execute()
        else:
            # Create wallet if it doesn't exist
            new_balance = -amount
            supabase_client.table('user_wallets').insert({
                'user_id': user_id,
                'balance': new_balance,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).execute()
        
        # Record transaction
        supabase_client.table('wallet_transactions').insert({
            'user_id': user_id,
            'type': 'usage',
            'amount': amount,
            'status': 'completed',
            'description': description,
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        
        logger.info(f"✅ Deducted {amount} credits from user {user_id} for: {description}")
        return True, new_balance
        
    except Exception as e:
        logger.error(f"❌ Error deducting credits: {str(e)}")
        return False, 0.0

# Initialize Supabase client if available (fallback)
if not SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        SUPABASE_AVAILABLE = True
        logger.info("✅ Supabase client initialized with anon key (RLS restrictions may apply)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize Supabase with anon key: {e}")
        supabase_client = None
        SUPABASE_AVAILABLE = False

def create_new_user_wallet(user_id: str, initial_balance: float = 3.0) -> float:
    """Create a new wallet for a user with welcome bonus"""
    try:
        # Create wallet with welcome bonus
        supabase_client.table('user_wallets').insert({
            'user_id': user_id,
            'balance': initial_balance,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        
        # Record welcome bonus transaction
        supabase_client.table('wallet_transactions').insert({
            'user_id': user_id,
            'type': 'funding',
            'amount': 3.0,
            'payment_intent_id': 'welcome_bonus',
            'status': 'completed',
            'description': 'Welcome bonus - $3 credit for new users',
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        
        logger.info(f"✅ New user wallet created with $3 welcome bonus for user: {user_id}")
        return initial_balance
        
    except Exception as e:
        logger.error(f"❌ Error creating new user wallet: {str(e)}")
        raise e

def ensure_database_schema():
    """Ensure the database table has the required columns for status tracking"""
    if not SUPABASE_AVAILABLE or not supabase_client:
        logger.warning("⚠️ Supabase not available, skipping schema check")
        return
    
    try:
        # Try to query the table to see if it exists and has the required columns
        result = supabase_client.table('generated_images').select('id, status, task_id, created_at, updated_at, error_message').limit(1).execute()
        logger.info("✅ Database schema check passed - required columns exist")
    except Exception as e:
        logger.warning(f"⚠️ Database schema may need updating: {e}")
        logger.info("ℹ️ Please ensure your generated_images table has these columns:")
        logger.info("  - status (text): pending, processing, completed, failed, cancelled, timeout")
        logger.info("  - task_id (text): Tripo API task ID")
        logger.info("  - created_at (timestamp): record creation time")
        logger.info("  - updated_at (timestamp): last update time")
        logger.info("  - error_message (text): error details for failed jobs")

# Run schema check on startup
ensure_database_schema()

# Stripe configuration for webhooks
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_3bceebeb9601dcd93ea64c8ab247a3b466f1e8d7ceaa5fd74809213d1debf9cc")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
    logger.info("✅ Stripe configured for webhook processing")
else:
    logger.warning("⚠️ STRIPE_SECRET_KEY not found - webhooks will not work")

# Payment link configuration
PAYMENT_LINK_URL = "https://buy.stripe.com/9B68wP6qJ0in2wrfJzg3600"
logger.info("✅ Payment link method configured")

async def download_image_to_pil(image_url: str) -> Optional[Image.Image]:
    """Download image from URL and convert to PIL Image"""
    try:
        # Handle HTTP URL
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    return Image.open(io.BytesIO(image_data))
                else:
                    logger.error(f"Failed to download image from {image_url}: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error loading image from {image_url}: {e}")
        return None

def upload_image_to_supabase(image_data: bytes, filename: str, content_type: str = "image/png", bucket_name: str = None) -> Optional[str]:
    """Upload file to Supabase storage bucket using service key"""
    if not SUPABASE_AVAILABLE or not supabase_client:
        logger.warning("⚠️ Supabase not available, skipping upload")
        return None
    
    # Use provided bucket name or default to images bucket
    target_bucket = bucket_name or SUPABASE_BUCKET_NAME
    
    try:
        # Upload to Supabase storage using service key
        response = supabase_client.storage.from_(target_bucket).upload(
            path=filename,
            file=image_data,
            file_options={"content-type": content_type}
        )
        
        if response:
            # Generate public URL
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{target_bucket}/{filename}"
            logger.info(f"✅ Uploaded file to Supabase bucket '{target_bucket}': {public_url}")
            return public_url
        else:
            logger.error("❌ Failed to upload file to Supabase")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error uploading file to Supabase: {e}")
        return None

def clean_glb_asset_properties(glb_data: bytes) -> bytes:
    """Comprehensive GLB cleanup - removes tripo tags, hex IDs, and cleans asset properties"""
    try:
        from pygltflib import GLTF2
        import io
        
        # Load GLB data from bytes
        gltf = GLTF2().load_from_bytes(glb_data)
        
        logger.info(f"🔧 Starting comprehensive GLB cleanup (nodes: {len(gltf.nodes) if gltf.nodes else 0})")
        
        # Clean node names
        if gltf.nodes:
            for node in gltf.nodes:
                if hasattr(node, 'name') and node.name:
                    original_name = node.name
                    cleaned_name = _clean_node_name(node.name)
                    if cleaned_name != original_name:
                        logger.info(f"🧹 Cleaned node: '{original_name}' -> '{cleaned_name}'")
                        node.name = cleaned_name
        
        # Clean mesh names
        if gltf.meshes:
            for i, mesh in enumerate(gltf.meshes):
                if hasattr(mesh, 'name') and mesh.name:
                    original_name = mesh.name
                    cleaned_name = _clean_mesh_name(mesh.name, i)
                    if cleaned_name != original_name:
                        logger.info(f"🧹 Cleaned mesh: '{original_name}' -> '{cleaned_name}'")
                        mesh.name = cleaned_name
        
        # Clean material names
        if gltf.materials:
            for i, material in enumerate(gltf.materials):
                if hasattr(material, 'name') and material.name:
                    original_name = material.name
                    cleaned_name = _clean_material_name(material.name, i)
                    if cleaned_name != original_name:
                        logger.info(f"🧹 Cleaned material: '{original_name}' -> '{cleaned_name}'")
                        material.name = cleaned_name
        
        # Clean texture and image names
        if gltf.textures:
            for i, texture in enumerate(gltf.textures):
                if hasattr(texture, 'name') and texture.name:
                    original_name = texture.name
                    cleaned_name = _clean_generic_name(texture.name, f'texture_{i}')
                    if cleaned_name != original_name:
                        logger.info(f"🧹 Cleaned texture: '{original_name}' -> '{cleaned_name}'")
                        texture.name = cleaned_name
        
        if gltf.images:
            for i, image in enumerate(gltf.images):
                if hasattr(image, 'name') and image.name:
                    original_name = image.name
                    cleaned_name = _clean_generic_name(image.name, f'image_{i}')
                    if cleaned_name != original_name:
                        logger.info(f"🧹 Cleaned image: '{original_name}' -> '{cleaned_name}'")
                        image.name = cleaned_name
        
        # Clean scene names
        if gltf.scenes:
            for scene in gltf.scenes:
                if hasattr(scene, 'name') and scene.name:
                    original_name = scene.name
                    cleaned_name = _clean_generic_name(scene.name, 'scene')
                    if cleaned_name != original_name:
                        logger.info(f"🧹 Cleaned scene: '{original_name}' -> '{cleaned_name}'")
                        scene.name = cleaned_name
        
        # Clean asset metadata
        if hasattr(gltf, 'asset') and gltf.asset:
            if hasattr(gltf.asset, 'generator') and gltf.asset.generator:
                if 'tripo' in gltf.asset.generator.lower():
                    logger.info(f"🧹 Cleaned generator: '{gltf.asset.generator}' -> 'GLB Cleaner'")
                    gltf.asset.generator = 'Vicino AI'
            
            if hasattr(gltf.asset, 'copyright') and gltf.asset.copyright:
                if 'tripo' in gltf.asset.copyright.lower():
                    logger.info(f"🧹 Cleaned copyright: '{gltf.asset.copyright}' -> ''")
                    gltf.asset.copyright = ''
        
        # Save back to bytes
        cleaned_data = gltf.save_to_bytes()
        
        # Ensure we have bytes data
        if not isinstance(cleaned_data, bytes):
            logger.warning(f"⚠️ save_to_bytes() returned {type(cleaned_data)}, converting to bytes")
            try:
                if isinstance(cleaned_data, list):
                    # Handle list of bytes objects or integers
                    if cleaned_data and isinstance(cleaned_data[0], bytes):
                        # List of bytes objects - concatenate them
                        cleaned_data = b''.join(cleaned_data)
                    else:
                        # List of integers - convert to bytes
                        cleaned_data = bytes(cleaned_data)
                elif isinstance(cleaned_data, str):
                    cleaned_data = cleaned_data.encode('utf-8')
                else:
                    logger.error(f"❌ Unexpected data type from save_to_bytes(): {type(cleaned_data)}")
                    return glb_data  # Return original data
            except Exception as conversion_error:
                logger.error(f"❌ Error converting to bytes: {conversion_error}")
                return glb_data  # Return original data
        
        logger.info("✅ Completed comprehensive GLB cleanup")
        return cleaned_data
        
    except ImportError:
        logger.warning("⚠️ pygltflib not installed. Install with: pip install pygltflib")
        logger.info("📝 Returning original GLB data without cleaning")
        return glb_data
    except Exception as e:
        logger.error(f"❌ Error cleaning GLB: {e}")
        logger.info("📝 Returning original GLB data due to error")
        return glb_data

def _clean_node_name(name: str) -> str:
    """Clean node names by removing tripo tags and hex identifiers"""
    if not name:
        return 'object'
    
    # Remove tripo prefixes
    cleaned_name = name
    if cleaned_name.startswith('tripo_'):
        cleaned_name = cleaned_name[6:]
    
    # Remove hex/UUID suffixes
    if '_' in cleaned_name:
        parts = cleaned_name.split('_')
        cleaned_parts = []
        for part in parts:
            # Check for hex patterns (8+ characters, all hex)
            if len(part) >= 8 and all(c in '0123456789abcdef' for c in part.lower()):
                continue
            # Also check for UUID patterns (8-4-4-4-12 format)
            if len(part) >= 8 and '-' in part and all(c in '0123456789abcdef-' for c in part.lower()):
                continue
            cleaned_parts.append(part)
        cleaned_name = '_'.join(cleaned_parts)
    
    # Remove common unwanted suffixes
    unwanted_suffixes = ['_node', '_mesh', '_object', '_model']
    for suffix in unwanted_suffixes:
        if cleaned_name.endswith(suffix):
            cleaned_name = cleaned_name[:-len(suffix)]
    
    # Clean up multiple underscores
    while '__' in cleaned_name:
        cleaned_name = cleaned_name.replace('__', '_')
    
    # Remove leading/trailing underscores
    cleaned_name = cleaned_name.strip('_')
    
    # If name is empty after cleaning, use a default
    if not cleaned_name:
        cleaned_name = 'object'
    
    return cleaned_name

def _clean_mesh_name(name: str, index: int) -> str:
    """Clean mesh names by removing tripo tags and hex identifiers"""
    if not name:
        return f'mesh_{index}'
    
    # Remove tripo prefixes
    cleaned_name = name
    if cleaned_name.startswith('tripo_'):
        cleaned_name = cleaned_name[6:]
    
    # Remove hex/UUID suffixes
    if '_' in cleaned_name:
        parts = cleaned_name.split('_')
        cleaned_parts = []
        for part in parts:
            # Check for hex patterns (8+ characters, all hex)
            if len(part) >= 8 and all(c in '0123456789abcdef' for c in part.lower()):
                continue
            # Also check for UUID patterns (8-4-4-4-12 format)
            if len(part) >= 8 and '-' in part and all(c in '0123456789abcdef-' for c in part.lower()):
                continue
            cleaned_parts.append(part)
        cleaned_name = '_'.join(cleaned_parts)
    
    # Remove unwanted suffixes
    unwanted_suffixes = ['_mesh', '_geometry', '_object']
    for suffix in unwanted_suffixes:
        if cleaned_name.endswith(suffix):
            cleaned_name = cleaned_name[:-len(suffix)]
    
    # Clean up and set default if empty
    cleaned_name = cleaned_name.strip('_')
    if not cleaned_name:
        cleaned_name = f'mesh_{index}'
    
    return cleaned_name

def _clean_material_name(name: str, index: int) -> str:
    """Clean material names by removing tripo tags and hex identifiers"""
    if not name:
        return f'material_{index}'
    
    # Remove tripo prefixes
    cleaned_name = name
    if cleaned_name.startswith('tripo_'):
        cleaned_name = cleaned_name[6:]
    
    # Remove hex/UUID suffixes
    if '_' in cleaned_name:
        parts = cleaned_name.split('_')
        cleaned_parts = []
        for part in parts:
            # Check for hex patterns (8+ characters, all hex)
            if len(part) >= 8 and all(c in '0123456789abcdef' for c in part.lower()):
                continue
            # Also check for UUID patterns (8-4-4-4-12 format)
            if len(part) >= 8 and '-' in part and all(c in '0123456789abcdef-' for c in part.lower()):
                continue
            cleaned_parts.append(part)
        cleaned_name = '_'.join(cleaned_parts)
    
    # Remove unwanted suffixes
    unwanted_suffixes = ['_material', '_mat', '_shader']
    for suffix in unwanted_suffixes:
        if cleaned_name.endswith(suffix):
            cleaned_name = cleaned_name[:-len(suffix)]
    
    # Clean up and set default if empty
    cleaned_name = cleaned_name.strip('_')
    if not cleaned_name:
        cleaned_name = f'material_{index}'
    
    return cleaned_name

def _clean_generic_name(name: str, default: str) -> str:
    """Generic name cleaning function for textures, images, and scenes"""
    if not name:
        return default
    
    # Remove tripo prefixes
    cleaned_name = name
    if cleaned_name.startswith('tripo_'):
        cleaned_name = cleaned_name[6:]
    
    # Remove hex/UUID suffixes
    if '_' in cleaned_name:
        parts = cleaned_name.split('_')
        cleaned_parts = []
        for part in parts:
            # Check for hex patterns (8+ characters, all hex)
            if len(part) >= 8 and all(c in '0123456789abcdef' for c in part.lower()):
                continue
            # Also check for UUID patterns (8-4-4-4-12 format)
            if len(part) >= 8 and '-' in part and all(c in '0123456789abcdef-' for c in part.lower()):
                continue
            cleaned_parts.append(part)
        cleaned_name = '_'.join(cleaned_parts)
    
    # Clean up
    cleaned_name = cleaned_name.strip('_')
    while '__' in cleaned_name:
        cleaned_name = cleaned_name.replace('__', '_')
    
    return cleaned_name if cleaned_name else default

def insert_image_record(target_object: str, image_url: str, iteration: int = None, model_3d_url: str = None) -> Optional[int]:
    """Insert image record into generated_images table"""
    if not SUPABASE_AVAILABLE or not supabase_client:
        logger.warning("⚠️ Supabase not available, skipping database insert")
        return None
    
    try:
        # Prepare data for insertion
        data = {
            "target_object": target_object,
            "image_url": image_url,
            "iteration": iteration,
            "status": "running",  # Add initial status
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Add 3D model URL if provided
        if model_3d_url:
            data["3d_url"] = model_3d_url
        
        # Insert the record
        response = supabase_client.table('generated_images').insert(data).execute()
        
        if response.data and len(response.data) > 0:
            inserted_id = response.data[0].get('id')
            logger.info(f"✅ Inserted image record with ID: {inserted_id}")
            return inserted_id
        else:
            logger.error("❌ No data returned from insert operation")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error inserting image record: {e}")
        return None

def download_image_to_pil_sync(image_url: str) -> Optional[Image.Image]:
    """Download image from URL or load from file and convert to PIL Image (synchronous version)"""
    try:
        if image_url.startswith("file://"):
            # Handle local file
            file_path = image_url.replace("file://", "")
            return Image.open(file_path)
        else:
            # Handle HTTP URL
            import requests
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
            else:
                logger.error(f"Failed to download image from {image_url}: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error loading image from {image_url}: {e}")
        return None

def generate_multiview_with_gpt_image1(target_object: str, iteration: int = 1, previous_feedback: List[str] = None, previous_image_url: str = None, user_feedback: str = None, image_size: str = DEFAULT_IMAGE_SIZE) -> str:
    """Generate 2x2 multiview image using GPT-Image-1 with image-to-image capability"""
    
    # Create the generation instructions
    instructions = f"""Your task is to generate a 2x2 grid with 4 specific views of the same object for 3D reconstruction: {target_object}. 

GRID LAYOUT (2x2):
- Top Left: FRONT view
- Top Right: RIGHT view  
- Bottom Left: LEFT view
- Bottom Right: BACK view

CRITICAL OBJECT CONSISTENCY REQUIREMENTS (MOST IMPORTANT):
- EXACT same object type across ALL 4 views (e.g., if it's a Golden Retriever, ALL 4 views must show Golden Retrievers)
- EXACT same color, texture, and material across ALL 4 views
- EXACT same size and proportions across ALL 4 views
- EXACT same pose/position of the object across ALL 4 views
- NO variations in object appearance, shape, or characteristics
- NO different objects in different grid positions
- NO mixed object types (e.g., some Golden Retrievers, some other dog breeds)

BACKGROUND AND LIGHTING REQUIREMENTS:
- PURE WHITE background (#FFFFFF) across ALL 4 views
- NO shadows cast by the object on the background
- NO background textures, patterns, or gradients
- NO environmental lighting effects
- Clean, studio-like lighting that evenly illuminates the object
- Object should appear to float on pure white background

VIEW REQUIREMENTS:
- FRONT view: Object facing directly toward the camera
- RIGHT view: Object rotated 90 degrees to show right side
- LEFT view: Object rotated 90 degrees to show left side  
- BACK view: Object rotated 180 degrees to show back/rear

OBJECT CONSISTENCY IS THE MOST CRITICAL FACTOR FOR 3D RECONSTRUCTION. FAILURE TO MAINTAIN CONSISTENCY WILL RESULT IN POOR RECONSTRUCTION QUALITY."""

    # Add feedback from previous iterations with user feedback having highest priority
    ai_feedback_text = " ".join(previous_feedback) if previous_feedback else "No specific AI feedback available"
    
    if user_feedback:
        # User feedback has highest priority
        instructions += f"""

HIGHEST PRIORITY - USER FEEDBACK (MUST ADDRESS):
{user_feedback}

This user feedback MUST be addressed and implemented in the next iteration. It takes precedence over all other considerations.

ADDITIONAL AI SUGGESTIONS (if any):
{ai_feedback_text if previous_feedback else "No additional AI suggestions"}

CRITICAL: The user's specific request above MUST be prioritized and implemented."""
    elif previous_feedback:
        # Only AI feedback available
        if iteration > 1:
            instructions += f" IMPORTANT: Based on the previous image, address these specific issues: {ai_feedback_text}. Maintain the good aspects while fixing the problems identified."
        else:
            instructions += f" IMPORTANT: Address these specific issues from previous iteration: {ai_feedback_text}"
    
    try:
        # Debug logging
        logger.info(f"🔍 Debug: iteration={iteration}, previous_image_url={'None' if previous_image_url is None else 'exists'}")
        
        # For first iteration - text to image
        if iteration == 1 or not previous_image_url:
            logger.info(f"🎨 Generating initial image for '{target_object}' (iteration {iteration})...")
            response = openai_sync_client.images.generate(
                model="gpt-image-1",
                prompt=instructions,
                size=image_size,
            )
        else:
            # For subsequent iterations - image edit with feedback
            logger.info(f"🎨 Editing previous image with feedback for '{target_object}' (iteration {iteration})...")
            
            # Download previous image
            previous_image = download_image_to_pil_sync(previous_image_url)
            if not previous_image:
                logger.warning(f"⚠️  Could not load previous image for iteration {iteration}, using text-to-image generation instead")
                response = openai_sync_client.images.generate(
                    model="gpt-image-1",
                    prompt=instructions,
                    size=image_size,
                )
            else:
                # Create edit instructions based on feedback with user feedback priority
                if user_feedback:
                    edit_instructions = f"""Improve this 2x2 multiview image of {target_object} by addressing these specific issues:

HIGHEST PRIORITY - USER FEEDBACK (MUST ADDRESS):
{user_feedback}

This user feedback MUST be addressed and implemented. It takes precedence over all other considerations.

ADDITIONAL AI SUGGESTIONS (if any):
{ai_feedback_text if previous_feedback else "No additional AI suggestions"}

BACKGROUND AND LIGHTING REQUIREMENTS:
- PURE WHITE background (#FFFFFF) across ALL 4 views
- NO shadows cast by the object on the background
- NO background textures, patterns, or gradients
- NO environmental lighting effects
- Clean, studio-like lighting that evenly illuminates the object
- Object should appear to float on pure white background

CRITICAL: The user's specific request above MUST be prioritized and implemented. Maintain the overall structure and good aspects while addressing the user's feedback."""
                else:
                    edit_instructions = f"""Improve this 2x2 multiview image of {target_object} by addressing these specific issues: {ai_feedback_text}. Maintain the overall structure and good aspects while fixing the identified problems.

GRID LAYOUT (2x2):
- Top Left: FRONT view
- Top Right: RIGHT view  
- Bottom Left: LEFT view
- Bottom Right: BACK view

CRITICAL: Ensure EXACT object consistency across ALL 4 views:
- Same object type, color, texture, size, and proportions
- NO variations in object appearance or characteristics
- NO mixed object types or different objects

VIEW REQUIREMENTS:
- FRONT view: Object facing directly toward the camera
- RIGHT view: Object rotated 90 degrees to show right side
- LEFT view: Object rotated 90 degrees to show left side  
- BACK view: Object rotated 180 degrees to show back/rear

BACKGROUND AND LIGHTING REQUIREMENTS:
- PURE WHITE background (#FFFFFF) across ALL 4 views
- NO shadows cast by the object on the background
- NO background textures, patterns, or gradients
- NO environmental lighting effects
- Clean, studio-like lighting that evenly illuminates the object
- Object should appear to float on pure white background

OBJECT CONSISTENCY IS THE MOST CRITICAL FACTOR FOR 3D RECONSTRUCTION."""
                
                # Save PIL image to temporary file
                import tempfile
                temp_image_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                previous_image.save(temp_image_file, format='PNG')
                temp_image_file.close()
                
                # Create a proper mask with alpha channel for editing
                # Create a white mask with transparency to allow full editing
                mask_image = Image.new('RGBA', previous_image.size, (255, 255, 255, 255))
                temp_mask_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                mask_image.save(temp_mask_file, format='PNG')
                temp_mask_file.close()
                
                # Open files in binary mode for the API
                with open(temp_image_file.name, "rb") as image_file, open(temp_mask_file.name, "rb") as mask_file:
                    response = openai_sync_client.images.edit(
                        model="gpt-image-1",
                        image=image_file,
                        mask=mask_file,
                        prompt=edit_instructions,
                        n=1,
                        size=image_size
                    )
        
        if hasattr(response, 'data') and response.data:
            # Check if it's a URL or base64 data
            first_item = response.data[0]
            if hasattr(first_item, 'url') and first_item.url:
                image_url = first_item.url
                
                image_url = first_item.url
                return image_url
                    
            elif hasattr(first_item, 'b64_json') and first_item.b64_json:
                # Handle base64 data - save to PNG file and upload to Supabase
                try:
                    # Decode base64 data
                    image_data = base64.b64decode(first_item.b64_json)
                    
                    # Generate filename for Supabase
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    sanitized_object_name = sanitize_filename(target_object)
                    filename = f"{sanitized_object_name}_{iteration}_{timestamp}.png"
                    
                    # Create temporary file
                    import tempfile
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_file.write(image_data)
                    temp_file.close()
                    
                    return f"file://{temp_file.name}"
                        
                except Exception as e:
                    logger.error(f"❌ Error handling base64 data: {e}")
                    return None
            else:
                logger.error(f"❌ Unexpected response format")
                return None
        else:
            logger.error(f"❌ No image data in response")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error generating with GPT-4 Vision: {e}")
        return None

def run_hybrid_multiview_generation(session_id: str, target_object: str, mode: str = "quick", image_size: str = DEFAULT_IMAGE_SIZE) -> Dict:
    """Run iterative hybrid multiview generation with different modes"""
    
    session_id = session_id
    previous_feedback = []
    previous_image_url = None
    all_results = []
    iteration = 0
    
    # Set iteration limits based on mode
    if mode.lower() == "deep":
        max_iterations = 10
        mode_display = "Deep Think Mode"
    else:  # quick mode (default)
        max_iterations = 3
        mode_display = "Quick Mode"
    
    logger.info(f"🚀 Starting {mode_display} for '{target_object}' (max {max_iterations} iterations)")
    
    # Initialize session
    active_sessions[session_id] = {
        "status": "running",
        "target_object": target_object,
        "mode": mode,
        "image_size": image_size,
        "max_iterations": max_iterations,
        "current_iteration": 0,
        "iterations": [],
    }
    
    while True:
        iteration += 1
        
        # Check iteration limit based on mode
        if iteration > max_iterations:
            active_sessions[session_id]["status"] = "completed"
            active_sessions[session_id]["message"] = f"Reached maximum iterations ({max_iterations}) for {mode_display} - generation completed"
            break
        
        # Update session status
        active_sessions[session_id]["current_iteration"] = iteration
        
        # Get user feedback for this iteration
        user_feedback_for_this_iteration = active_sessions[session_id].get("user_feedback_for_next", "")
        
        if user_feedback_for_this_iteration:
            logger.info(f"🎯 Using user feedback for iteration {iteration}: {user_feedback_for_this_iteration}")
        
        # Generate image with GPT-Image-1 (image-to-image for iterations > 1)
        image_url = generate_multiview_with_gpt_image1(target_object, iteration, previous_feedback, previous_image_url, user_feedback_for_this_iteration, image_size)
        
        if not image_url:
            active_sessions[session_id]["status"] = "failed"
            active_sessions[session_id]["error"] = "Failed to generate image"
            break
        
        # Add the image to session
        iteration_result = {
            "iteration": iteration,
            "image_url": image_url
        }
        all_results.append(iteration_result)
        
        # Update session with iteration data
        active_sessions[session_id]["iterations"].append(iteration_result)
        
        # Store current image URL for next iteration
        previous_image_url = image_url
        
        # Clear user feedback after it's been used
        if "user_feedback_for_next" in active_sessions[session_id]:
            del active_sessions[session_id]["user_feedback_for_next"]
        
        # Print image URL info without cluttering the console
        if image_url.startswith('data:image/'):
            logger.info(f"📸 Stored base64 image for iteration {iteration}")
        elif image_url.startswith('http'):
            logger.info(f"📸 Stored remote image URL for iteration {iteration}: {image_url[:50]}...")
        else:
            logger.info(f"📸 Stored image for iteration {iteration}")
        
        # Pause for user feedback (except for the last iteration)
        if iteration < max_iterations:
            logger.info(f"⏸️ Pausing for user feedback after iteration {iteration}")
            active_sessions[session_id]["status"] = "waiting_for_feedback"
            active_sessions[session_id]["current_iteration"] = iteration
            active_sessions[session_id]["feedback_prompt"] = f"Generation complete for iteration {iteration}. Any suggestions for improvement?"
            
            # Wait for user feedback (no timeout)
            import time
            
            while active_sessions[session_id]["status"] == "waiting_for_feedback":
                time.sleep(1)
            
            # Get user feedback if provided
            user_feedback = active_sessions[session_id].get("user_feedback", "")
            if user_feedback:
                logger.info(f"💬 User feedback received: {user_feedback}")
                # Store user feedback separately for high priority handling
                active_sessions[session_id]["user_feedback_for_next"] = user_feedback
            else:
                logger.info(f"⏭️ No user feedback provided, continuing with next iteration")
                active_sessions[session_id]["user_feedback_for_next"] = ""
        
        # Add a minimal delay between iterations to prevent overwhelming the API
        import time
        time.sleep(0.5)
    
    return {
        "session_id": session_id,
        "target_object": target_object,
        "mode": mode,
        "max_iterations": max_iterations,
        "iterations": all_results
    }

@app.route('/')
def home():
    """Main page with input form"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    """Start iterative generation process - costs 0.1 credits"""
    try:
        # Check user authentication and balance
        user, error = get_user_from_token()
        if error:
            return jsonify({"error": error}), 401
        
        # Check if user has enough credits (0.1 USD)
        has_balance, current_balance = check_user_balance(user.id, 0.1)
        if not has_balance:
            return jsonify({
                "error": "Insufficient credits",
                "required": 0.1,
                "current_balance": current_balance,
                "message": "You need 0.1 credits to start generation. Please add funds to your wallet."
            }), 402
        
        data = request.get_json()
        target_object = data.get('target_object', '').strip()
        mode = data.get('mode', 'quick') # Default to 'quick' if not provided
        image_size = data.get('image_size', DEFAULT_IMAGE_SIZE) # Get image size from request
        
        # Validate image size
        if image_size not in SUPPORTED_IMAGE_SIZES:
            return jsonify({"error": f"Invalid image_size. Supported sizes: {', '.join(SUPPORTED_IMAGE_SIZES)}"}), 400
        
        if not target_object:
            return jsonify({"error": "Target object is required"}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Start generation in background
        def run_generation():
            try:
                run_hybrid_multiview_generation(session_id, target_object, mode, image_size)
            except Exception as e:
                logger.error(f"Error in generation thread for session {session_id}: {e}")
                if session_id in active_sessions:
                    active_sessions[session_id]["status"] = "failed"
                    active_sessions[session_id]["error"] = str(e)
        
        # Run in background thread
        thread = threading.Thread(target=run_generation)
        thread.daemon = True  # Make thread daemon so it doesn't block app shutdown
        thread.start()
        
        # Deduct credits after successful generation start
        success, new_balance = deduct_credits(user.id, 0.1, f"Iterative generation: {target_object} ({mode} mode)")
        if not success:
            logger.error(f"Failed to deduct credits for user {user.id}")
        
        logger.info(f"Started generation session {session_id} for '{target_object}' in {mode} mode")
        
        return jsonify({
            "session_id": session_id,
            "status": "started",
            "message": f"Started iterative generation for: {target_object} in {mode} mode",
            "credits_deducted": 0.1,
            "remaining_balance": new_balance
        })
        
    except Exception as e:
        logger.error(f"Error starting generation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/<session_id>')
def get_status(session_id):
    """Get current status and results for a session"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        session = active_sessions[session_id]
        
        return jsonify({
            "session_id": session_id,
            "status": session["status"],
            "target_object": session["target_object"],
            "mode": session["mode"],
            "image_size": session.get("image_size", DEFAULT_IMAGE_SIZE),
            "max_iterations": session["max_iterations"],
            "current_iteration": session["current_iteration"],
            "iterations": session["iterations"],
            "error": session.get("error", None),
            "feedback_prompt": session.get("feedback_prompt", None),
            "user_feedback": session.get("user_feedback", None)
        })
        
    except Exception as e:
        logger.error(f"Error getting status for session {session_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stop/<session_id>', methods=['POST'])
def stop_generation(session_id):
    """Stop a running generation session"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        session = active_sessions[session_id]
        
        if session["status"] not in ["running", "waiting_for_feedback"]:
            return jsonify({"error": "Session is not running or waiting for feedback"}), 400
        
        # Mark session as stopped
        session["status"] = "stopped"
        session["error"] = "Generation stopped by user"
        
        logger.info(f"Stopped generation session {session_id}")
        
        return jsonify({
            "session_id": session_id,
            "status": "stopped",
            "message": "Generation stopped successfully"
        })
        
    except Exception as e:
        logger.error(f"Error stopping generation session {session_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/feedback/<session_id>', methods=['POST'])
def submit_feedback(session_id):
    """Submit user feedback for the next iteration - costs 0.1 credits"""
    try:
        # Check user authentication and balance
        user, error = get_user_from_token()
        if error:
            return jsonify({"error": error}), 401
        
        # Check if user has enough credits (0.1 USD)
        has_balance, current_balance = check_user_balance(user.id, 0.1)
        if not has_balance:
            return jsonify({
                "error": "Insufficient credits",
                "required": 0.1,
                "current_balance": current_balance,
                "message": "You need 0.1 credits to submit feedback. Please add funds to your wallet."
            }), 402
        
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        session = active_sessions[session_id]
        
        if session["status"] != "waiting_for_feedback":
            return jsonify({"error": "Session is not waiting for feedback"}), 400
        
        data = request.get_json()
        user_feedback = data.get('feedback', '').strip()
        
        # Store user feedback in session
        session["user_feedback"] = user_feedback
        session["status"] = "running"  # Resume generation
        
        # Deduct credits after successful feedback submission
        success, new_balance = deduct_credits(user.id, 0.1, f"Feedback submission: {session.get('target_object', 'Unknown object')} (session {session_id})")
        if not success:
            logger.error(f"Failed to deduct credits for user {user.id}")
        
        logger.info(f"Received user feedback for session {session_id}: {user_feedback}")
        
        return jsonify({
            "session_id": session_id,
            "status": "running",
            "message": "Feedback received, resuming generation",
            "credits_deducted": 0.1,
            "remaining_balance": new_balance
        })
        
    except Exception as e:
        logger.error(f"Error submitting feedback for session {session_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/image/<session_id>/<int:iteration>')
def get_iteration_image(session_id, iteration):
    """Get image for a specific iteration"""
    try:
        
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        session = active_sessions[session_id]
        if iteration > len(session["iterations"]):
            return jsonify({"error": "Iteration not found"}), 404
        
        iteration_data = session["iterations"][iteration - 1]
        image_url = iteration_data["image_url"]
        target_object = session.get("target_object", "Unknown object")
        
        # Handle file URLs
        if image_url.startswith('file://'):
            file_path = image_url.replace('file://', '')
            return send_file(file_path, mimetype='image/png')
        
        # Handle base64 data URLs
        elif image_url.startswith('data:image/'):
            # Extract the base64 data
            header, encoded = image_url.split(",", 1)
            image_data = base64.b64decode(encoded)
            
            # Determine content type from the data URL
            content_type = header.split(":")[1].split(";")[0]
            
            # Return the image data directly
            return Response(image_data, mimetype=content_type)
        
        # Handle OpenAI URLs - download and serve the image
        elif image_url.startswith('http'):
            # Use requests to download the image
            try:
                import requests
                response = requests.get(image_url, timeout=30)
                if response.status_code == 200:
                    # Determine content type from response headers or URL
                    content_type = response.headers.get('content-type', 'image/png')
                    return Response(response.content, mimetype=content_type)
                else:
                    return jsonify({"error": "Failed to fetch image from URL"}), 500
            except Exception as e:
                logger.error(f"Failed to download image: {e}")
                return jsonify({"error": f"Failed to download image: {str(e)}"}), 500
        
        else:
            return jsonify({"error": "Invalid image URL format"}), 400
            
    except Exception as e:
        logger.error(f"Error serving image for session {session_id}, iteration {iteration}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions')
def list_sessions():
    """List all active sessions"""
    try:
        sessions = []
        for session_id, session_data in active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "status": session_data["status"],
                "target_object": session_data["target_object"],
                "mode": session_data["mode"],
                "max_iterations": session_data["max_iterations"],
                "current_iteration": session_data["current_iteration"]
            })
        
        return jsonify({"sessions": sessions})
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-3d', methods=['POST'])
def generate_3d():
    """Submit 3D generation job and return immediately - costs 0.5 credits"""
    try:
        # Check user authentication and balance
        user, error = get_user_from_token()
        if error:
            return jsonify({"error": error}), 401
        
        # Check if user has enough credits (0.5 USD)
        has_balance, current_balance = check_user_balance(user.id, 0.5)
        if not has_balance:
            return jsonify({
                "error": "Insufficient credits",
                "required": 0.5,
                "current_balance": current_balance,
                "message": "You need 0.5 credits to generate 3D model. Please add funds to your wallet."
            }), 402
        
        data = request.get_json()
        session_id = data.get('sessionId')
        iteration = data.get('iteration')
        target_object = data.get('targetObject')
        image_url = data.get('imageUrl')
        
        if not all([session_id, iteration, target_object, image_url]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Check if session exists
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        # Get image data (handle both local files and URLs)
        try:
            if image_url.startswith("file://"):
                # Handle local file
                file_path = image_url.replace("file://", "")
                with open(file_path, 'rb') as f:
                    image_data = f.read()
            else:
                # Handle HTTP URL
                import requests
                response = requests.get(image_url, timeout=30)
                if response.status_code != 200:
                    return jsonify({"error": "Failed to download image"}), 400
                image_data = response.content
        except Exception as e:
            logger.error(f"Error reading image: {e}")
            return jsonify({"error": "Failed to read image"}), 400
        
        # Upload to Supabase
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_object_name = sanitize_filename(target_object)
        filename = f"{sanitized_object_name}_{iteration}_{timestamp}.png"
        
        supabase_url = upload_image_to_supabase(image_data, filename)
        if not supabase_url:
            return jsonify({"error": "Failed to upload image to Supabase"}), 500
        
        # Insert record into database with pending status
        record_id = insert_image_record(target_object, supabase_url, iteration)
        if not record_id:
            return jsonify({"error": "Failed to insert database record"}), 500
        
        # Update record with pending status
        if SUPABASE_AVAILABLE and supabase_client:
            supabase_client.table('generated_images').update({
                "status": "running",
                "task_id": None,  # Will be set when task is created
                "updated_at": datetime.now().isoformat()
            }).eq('id', record_id).execute()
        
        # Start background processing
        thread = threading.Thread(
            target=process_3d_generation_background,
            args=(session_id, iteration, target_object, image_data, record_id, timestamp)
        )
        thread.daemon = True
        thread.start()
        
        # Deduct credits after successful job submission
        success, new_balance = deduct_credits(user.id, 0.5, f"3D generation: {target_object} (iteration {iteration})")
        if not success:
            logger.error(f"Failed to deduct credits for user {user.id}")
        
        return jsonify({
            "success": True,
            "record_id": record_id,
            "status": "running",
            "status_url": f"/api/generation-status/{record_id}",
            "message": "3D generation job submitted successfully",
            "credits_deducted": 0.5,
            "remaining_balance": new_balance
        })
        
    except Exception as e:
        logger.error(f"Error in generate-3d endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/upload-multiview', methods=['POST'])
def upload_multiview():
    """Handle multi-view image upload and direct 3D generation - costs 0.5 credits"""
    try:
        # Check user authentication and balance
        user, error = get_user_from_token()
        if error:
            return jsonify({"error": error}), 401
        
        # Check if user has enough credits (0.5 USD)
        has_balance, current_balance = check_user_balance(user.id, 0.5)
        if not has_balance:
            return jsonify({
                "error": "Insufficient credits",
                "required": 0.5,
                "current_balance": current_balance,
                "message": "You need 0.5 credits to generate 3D model from multi-view upload. Please add funds to your wallet."
            }), 402
        
        # Check if files are present
        if 'front' not in request.files or 'left' not in request.files or 'back' not in request.files or 'right' not in request.files:
            return jsonify({"error": "All four views (front, left, back, right) are required"}), 400
        
        # Get uploaded files
        front_file = request.files['front']
        left_file = request.files['left']
        back_file = request.files['back']
        right_file = request.files['right']
        
        # Validate files
        files = [front_file, left_file, back_file, right_file]
        for file in files:
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            if not file.content_type.startswith('image/'):
                return jsonify({"error": "All files must be images"}), 400
        
        # Generate unique session ID and timestamp
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Only upload front image to Supabase for database record
        front_file_data = front_file.read()
        front_file.seek(0)  # Reset file pointer
        
        front_filename = f"front_view_{session_id}_{timestamp}.png"
        front_supabase_url = upload_image_to_supabase(front_file_data, front_filename)
        if not front_supabase_url:
            return jsonify({"error": "Failed to upload front view"}), 500
        
        # Store all file data for direct processing (no need to upload to Supabase)
        file_data = {
            'front': front_file.read(),
            'left': left_file.read(),
            'back': back_file.read(),
            'right': right_file.read()
        }
        
        # Reset file pointers for background processing
        front_file.seek(0)
        left_file.seek(0)
        back_file.seek(0)
        right_file.seek(0)
        
        # Create a target object name based on timestamp
        target_object = f"multiview_upload_{timestamp}"
        
        # Insert record into database with pending status
        record_id = insert_image_record(target_object, front_supabase_url, 1)  # Use front view as main image
        if not record_id:
            return jsonify({"error": "Failed to insert database record"}), 500
        
        # Update record with pending status
        if SUPABASE_AVAILABLE and supabase_client:
            supabase_client.table('generated_images').update({
                "status": "running",
                "task_id": None,  # Will be set when task is created
                "updated_at": datetime.now().isoformat()
            }).eq('id', record_id).execute()
        
        # Start background processing
        thread = threading.Thread(
            target=process_multiview_upload_background,
            args=(session_id, target_object, file_data, record_id, timestamp)
        )
        thread.daemon = True
        thread.start()
        
        # Deduct credits after successful job submission
        success, new_balance = deduct_credits(user.id, 0.5, f"Multi-view 3D generation: {target_object}")
        if not success:
            logger.error(f"Failed to deduct credits for user {user.id}")
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "record_id": record_id,
            "status": "running",
            "status_url": f"/api/generation-status/{record_id}",
            "message": "Multi-view upload and 3D generation started successfully",
            "credits_deducted": 0.5,
            "remaining_balance": new_balance
        })
        
    except Exception as e:
        logger.error(f"Error in upload-multiview endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

def process_multiview_upload_background(session_id, target_object, file_data, record_id, timestamp):
    """Background function to process multi-view upload and 3D generation"""
    try:
        # Import the Tripo functions
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        from test_tripo_multiview_to_3d import create_multiview_task, get_task, download
        
        # Convert file data directly to PIL Images
        from PIL import Image
        import io
        
        views = {}
        for view_name, data in file_data.items():
            try:
                image = Image.open(io.BytesIO(data))
                views[view_name] = image
            except Exception as e:
                error_msg = f"Failed to process {view_name} view: {str(e)}"
                logger.error(f"❌ {error_msg}")
                update_job_status(record_id, "failed", error_msg)
                return
        
        # Submit to Tripo API
        task_id = create_multiview_task(views)
        
        # Update record with task_id and processing status
        if SUPABASE_AVAILABLE and supabase_client:
            supabase_client.table('generated_images').update({
                "status": "running",
                "task_id": task_id,
                "updated_at": datetime.now().isoformat()
            }).eq('id', record_id).execute()
        
        logger.info(f"✅ Submitted Tripo task {task_id} for multi-view upload record {record_id}")
        
        # Poll for completion
        max_attempts = 60  # 10 minutes with 10-second intervals
        for attempt in range(max_attempts):
            try:
                info = get_task(task_id)
                if info.get("code") != 0:
                    # Log the full error for debugging
                    logger.error(f"❌ Tripo API error: {info}")
                    
                    # Provide user-friendly error message based on error code
                    error_code = info.get("code")
                    if error_code == 2010:
                        user_error_msg = "Generation failed due to insufficient credits. Please try again later or contact support."
                    elif error_code in [400, 401, 403]:
                        user_error_msg = "Generation service temporarily unavailable. Please try again later."
                    elif error_code in [500, 502, 503]:
                        user_error_msg = "Generation service is experiencing issues. Please try again later."
                    else:
                        user_error_msg = "Generation failed. Please try again or contact support if the problem persists."
                    
                    update_job_status(record_id, "failed", user_error_msg)
                    return
                
                status = info["data"]["status"]
                logger.info(f"Task {task_id} status: {status} (attempt {attempt + 1}/{max_attempts})")
                
                # Handle finalized statuses
                if status == "success":
                    # Process successful completion
                    process_successful_job(info, task_id, session_id, 1, target_object, record_id, timestamp)
                    return
                elif status == "failed":
                    # Log the full error for debugging
                    logger.error(f"❌ Tripo task failed: {info}")
                    user_error_msg = "Generation failed. Please try again or contact support if the problem persists."
                    update_job_status(record_id, "failed", user_error_msg)
                    return
                elif status == "cancelled":
                    user_error_msg = "Generation was cancelled. Please try again."
                    logger.warning(f"⚠️ Tripo task was cancelled")
                    update_job_status(record_id, "cancelled", user_error_msg)
                    return
                elif status == "unknown":
                    user_error_msg = "Generation service is experiencing issues. Please try again later."
                    logger.error(f"❌ Tripo task status unknown - system level issue")
                    update_job_status(record_id, "failed", user_error_msg)
                    return
                
                # Handle ongoing statuses
                elif status in ("queued", "running"):
                    # Continue polling
                    pass
                else:
                    # Unknown status, log and continue
                    logger.warning(f"⚠️ Unknown status '{status}' for task {task_id}")
                
                import time
                time.sleep(10)  # Wait 10 seconds before next poll
                
            except Exception as e:
                logger.error(f"Error polling task {task_id}: {e}")
                time.sleep(10)
        
        # Handle timeout
        logger.error(f"❌ Timeout waiting for 3D generation after {max_attempts * 10} seconds")
        user_error_msg = "Generation timed out. Please try again with smaller images or contact support."
        update_job_status(record_id, "timeout", user_error_msg)
        
    except Exception as e:
        # Log the full error for debugging
        logger.error(f"❌ Error in background multi-view processing: {str(e)}")
        
        # Provide user-friendly error message
        if "403" in str(e) and "credit" in str(e).lower():
            user_error_msg = "Generation failed due to insufficient credits. Please try again later or contact support."
        elif "403" in str(e):
            user_error_msg = "Generation service temporarily unavailable. Please try again later."
        elif "timeout" in str(e).lower():
            user_error_msg = "Generation timed out. Please try again with smaller images or contact support."
        elif "connection" in str(e).lower():
            user_error_msg = "Connection error. Please check your internet connection and try again."
        else:
            user_error_msg = "Generation failed. Please try again or contact support if the problem persists."
        
        update_job_status(record_id, "failed", user_error_msg)

def process_3d_generation_background(session_id, iteration, target_object, image_data, record_id, timestamp):
    """Background function to process 3D generation"""
    try:
        # Import the Tripo functions
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        from test_tripo_multiview_to_3d import create_multiview_task, get_task, download, crop_multiview_image
        
        # Load the image and crop it into 4 views
        from PIL import Image
        import io
        
        # Load the image
        image = Image.open(io.BytesIO(image_data))
        
        # Crop the image into 4 views (front, right, left, back)
        views = crop_multiview_image(image)
        
        # Submit to Tripo API
        task_id = create_multiview_task(views)
        
        # Update record with task_id and processing status
        if SUPABASE_AVAILABLE and supabase_client:
            supabase_client.table('generated_images').update({
                "status": "running",
                "task_id": task_id,
                "updated_at": datetime.now().isoformat()
            }).eq('id', record_id).execute()
        
        logger.info(f"✅ Submitted Tripo task {task_id} for record {record_id}")
        
        # Poll for completion
        max_attempts = 60  # 10 minutes with 10-second intervals
        for attempt in range(max_attempts):
            try:
                info = get_task(task_id)
                if info.get("code") != 0:
                    # Log the full error for debugging
                    logger.error(f"❌ Tripo API error: {info}")
                    
                    # Provide user-friendly error message based on error code
                    error_code = info.get("code")
                    if error_code == 2010:
                        user_error_msg = "Generation failed due to insufficient credits. Please try again later or contact support."
                    elif error_code in [400, 401, 403]:
                        user_error_msg = "Generation service temporarily unavailable. Please try again later."
                    elif error_code in [500, 502, 503]:
                        user_error_msg = "Generation service is experiencing issues. Please try again later."
                    else:
                        user_error_msg = "Generation failed. Please try again or contact support if the problem persists."
                    
                    update_job_status(record_id, "failed", user_error_msg)
                    return
                
                status = info["data"]["status"]
                logger.info(f"Task {task_id} status: {status} (attempt {attempt + 1}/{max_attempts})")
                
                # Handle finalized statuses
                if status == "success":
                    # Process successful completion
                    process_successful_job(info, task_id, session_id, iteration, target_object, record_id, timestamp)
                    return
                elif status == "failed":
                    # Log the full error for debugging
                    logger.error(f"❌ Tripo task failed: {info}")
                    user_error_msg = "Generation failed. Please try again or contact support if the problem persists."
                    update_job_status(record_id, "failed", user_error_msg)
                    return
                elif status == "cancelled":
                    user_error_msg = "Generation was cancelled. Please try again."
                    logger.warning(f"⚠️ Tripo task was cancelled")
                    update_job_status(record_id, "cancelled", user_error_msg)
                    return
                elif status == "unknown":
                    user_error_msg = "Generation service is experiencing issues. Please try again later."
                    logger.error(f"❌ Tripo task status unknown - system level issue")
                    update_job_status(record_id, "failed", user_error_msg)
                    return
                
                # Handle ongoing statuses
                elif status in ("queued", "running"):
                    # Continue polling
                    pass
                else:
                    # Unknown status, log and continue
                    logger.warning(f"⚠️ Unknown status '{status}' for task {task_id}")
                
                import time
                time.sleep(10)  # Wait 10 seconds before next poll
                
            except Exception as e:
                logger.error(f"Error polling task {task_id}: {e}")
                time.sleep(10)
        
        # Handle timeout
        logger.error(f"❌ Timeout waiting for 3D generation after {max_attempts * 10} seconds")
        user_error_msg = "Generation timed out. Please try again with smaller images or contact support."
        update_job_status(record_id, "timeout", user_error_msg)
        
    except Exception as e:
        # Log the full error for debugging
        logger.error(f"❌ Error in background 3D generation: {str(e)}")
        
        # Provide user-friendly error message
        if "403" in str(e) and "credit" in str(e).lower():
            user_error_msg = "Generation failed due to insufficient credits. Please try again later or contact support."
        elif "403" in str(e):
            user_error_msg = "Generation service temporarily unavailable. Please try again later."
        elif "timeout" in str(e).lower():
            user_error_msg = "Generation timed out. Please try again with smaller images or contact support."
        elif "connection" in str(e).lower():
            user_error_msg = "Connection error. Please check your internet connection and try again."
        else:
            user_error_msg = "Generation failed. Please try again or contact support if the problem persists."
        
        update_job_status(record_id, "failed", user_error_msg)

def process_successful_job(info, task_id, session_id, iteration, target_object, record_id, timestamp):
    """Process a successfully completed 3D generation job"""
    try:
        # Import required functions
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        from test_tripo_multiview_to_3d import download
        
        out = info["data"]["output"]
        model_url = out.get("pbr_model") or out.get("model")
        
        if not model_url:
            error_msg = "No model URL in Tripo response"
            logger.error(f"❌ {error_msg}")
            update_job_status(record_id, "failed", error_msg)
            return
        
        # Download the model
        model_filename = f"tripo_model_{session_id}_{iteration}.glb"
        model_path = download(model_url, model_filename)
        
        # Upload GLB file to Supabase 3D files bucket
        glb_supabase_url = None
        if SUPABASE_AVAILABLE and supabase_client:
            try:
                # Read the downloaded GLB file
                with open(model_path, 'rb') as f:
                    glb_data = f.read()
                
                # Clean asset properties from GLB before upload
                cleaned_glb_data = clean_glb_asset_properties(glb_data)
                
                # Debug: Check data type
                logger.info(f"📝 GLB data type: {type(cleaned_glb_data)}, length: {len(cleaned_glb_data) if hasattr(cleaned_glb_data, '__len__') else 'unknown'}")
                
                # Ensure we have valid bytes data for upload
                if not isinstance(cleaned_glb_data, bytes):
                    logger.warning("⚠️ Using original GLB data due to cleaning issues")
                    cleaned_glb_data = glb_data
                
                # Validate that the cleaned GLB data is still a valid GLB file
                if not cleaned_glb_data.startswith(b'glTF'):
                    logger.warning("⚠️ Cleaned GLB data is not valid, using original data")
                    cleaned_glb_data = glb_data
                
                # Upload to Supabase 3D files bucket
                sanitized_object_name = sanitize_filename(target_object)
                glb_filename = f"{sanitized_object_name}_{iteration}_{timestamp}.glb"
                glb_supabase_url = upload_glb_to_supabase(
                    cleaned_glb_data, 
                    glb_filename
                )
                
                if glb_supabase_url:
                    # Update the database record with completed status and 3D model URL
                    supabase_client.table('generated_images').update({
                        "status": "completed",
                        "3d_url": glb_supabase_url,
                        "updated_at": datetime.now().isoformat()
                    }).eq('id', record_id).execute()
                    logger.info(f"✅ Uploaded GLB to Supabase: {glb_supabase_url}")
                else:
                    logger.error("❌ Failed to upload GLB to Supabase")
                    update_job_status(record_id, "failed", "Failed to upload GLB to Supabase")
                    return
                    
            except Exception as e:
                logger.error(f"Error uploading GLB to Supabase: {e}")
                update_job_status(record_id, "failed", f"Error uploading GLB: {str(e)}")
                return
        
        # Clean up local file
        try:
            os.remove(model_path)
        except:
            pass
        
        logger.info(f"✅ Successfully completed 3D generation for record {record_id}")
        
    except Exception as e:
        error_msg = f"Error processing successful job: {str(e)}"
        logger.error(f"❌ {error_msg}")
        update_job_status(record_id, "failed", error_msg)

@app.route('/api/upload-single-image', methods=['POST'])
def upload_single_image():
    """Handle single image upload and direct 3D generation - costs 0.5 credits"""
    try:
        # Check user authentication and balance
        user, error = get_user_from_token()
        if error:
            return jsonify({"error": error}), 401
        
        # Check if user has enough credits (0.5 USD)
        has_balance, current_balance = check_user_balance(user.id, 0.5)
        if not has_balance:
            return jsonify({
                "error": "Insufficient credits",
                "required": 0.5,
                "current_balance": current_balance,
                "message": "You need 0.5 credits to generate 3D model from single image. Please add funds to your wallet."
            }), 402
        
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({"error": "Image file is required"}), 400
        
        # Get uploaded file
        image_file = request.files['image']
        
        # Validate file
        if image_file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        if not image_file.content_type.startswith('image/'):
            return jsonify({"error": "File must be an image"}), 400
        
        # Generate unique session ID and timestamp
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Read image data for Supabase upload
        image_file_data = image_file.read()
        image_file.seek(0)  # Reset file pointer
        
        # Upload image to Supabase for database record
        image_filename = f"single_image_{session_id}_{timestamp}.png"
        image_supabase_url = upload_image_to_supabase(image_file_data, image_filename)
        if not image_supabase_url:
            return jsonify({"error": "Failed to upload image"}), 500
        
        # Store file data for direct processing
        file_data = image_file.read()
        image_file.seek(0)  # Reset file pointer
        
        # Create a target object name based on timestamp
        target_object = f"single_image_upload_{timestamp}"
        
        # Insert record into database with pending status
        record_id = insert_image_record(target_object, image_supabase_url, 1)
        if not record_id:
            return jsonify({"error": "Failed to insert database record"}), 500
        
        # Update record with pending status
        if SUPABASE_AVAILABLE and supabase_client:
            supabase_client.table('generated_images').update({
                "status": "running",
                "task_id": None,  # Will be set when task is created
                "updated_at": datetime.now().isoformat()
            }).eq('id', record_id).execute()
        
        # Start background processing
        thread = threading.Thread(
            target=process_single_image_upload_background,
            args=(session_id, target_object, file_data, record_id, timestamp)
        )
        thread.daemon = True
        thread.start()
        
        # Deduct credits after successful job submission
        success, new_balance = deduct_credits(user.id, 0.5, f"Single image 3D generation: {target_object}")
        if not success:
            logger.error(f"Failed to deduct credits for user {user.id}")
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "record_id": record_id,
            "status": "running",
            "status_url": f"/api/generation-status/{record_id}",
            "message": "Single image upload and 3D generation started successfully",
            "credits_deducted": 0.5,
            "remaining_balance": new_balance
        })
        
    except Exception as e:
        logger.error(f"Error in upload-single-image endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

def process_single_image_upload_background(session_id, target_object, file_data, record_id, timestamp):
    """Background function to process single image upload and 3D generation"""
    try:
        # Import the Tripo functions
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        from test_tripo_single_image_to_3d import create_single_image_task, get_task, download
        
        # Convert file data directly to PIL Image
        from PIL import Image
        import io
        
        try:
            image = Image.open(io.BytesIO(file_data))
        except Exception as e:
            error_msg = f"Failed to process image: {str(e)}"
            logger.error(f"❌ {error_msg}")
            update_job_status(record_id, "failed", error_msg)
            return
        
        # Submit to Tripo API
        task_id = create_single_image_task(image, model_version="v3.0-20250812")
        
        # Update record with task_id and processing status
        if SUPABASE_AVAILABLE and supabase_client:
            supabase_client.table('generated_images').update({
                "status": "running",
                "task_id": task_id,
                "updated_at": datetime.now().isoformat()
            }).eq('id', record_id).execute()
        
        logger.info(f"✅ Submitted Tripo task {task_id} for single image upload record {record_id}")
        
        # Poll for completion
        max_attempts = 60  # 10 minutes with 10-second intervals
        for attempt in range(max_attempts):
            try:
                info = get_task(task_id)
                if info.get("code") != 0:
                    # Log the full error for debugging
                    logger.error(f"❌ Tripo API error: {info}")
                    
                    # Provide user-friendly error message based on error code
                    error_code = info.get("code")
                    if error_code == 2010:
                        user_error_msg = "Generation failed due to insufficient credits. Please try again later or contact support."
                    elif error_code in [400, 401, 403]:
                        user_error_msg = "Generation service temporarily unavailable. Please try again later."
                    elif error_code in [500, 502, 503]:
                        user_error_msg = "Generation service is experiencing issues. Please try again later."
                    else:
                        user_error_msg = "Generation failed. Please try again or contact support if the problem persists."
                    
                    update_job_status(record_id, "failed", user_error_msg)
                    return
                
                status = info["data"]["status"]
                logger.info(f"Task {task_id} status: {status} (attempt {attempt + 1}/{max_attempts})")
                
                # Handle finalized statuses
                if status == "success":
                    # Process successful completion
                    process_successful_job(info, task_id, session_id, 1, target_object, record_id, timestamp)
                    return
                elif status == "failed":
                    # Log the full error for debugging
                    logger.error(f"❌ Tripo task failed: {info}")
                    user_error_msg = "Generation failed. Please try again or contact support if the problem persists."
                    update_job_status(record_id, "failed", user_error_msg)
                    return
                elif status == "cancelled":
                    user_error_msg = "Generation was cancelled. Please try again."
                    logger.warning(f"⚠️ Tripo task was cancelled")
                    update_job_status(record_id, "cancelled", user_error_msg)
                    return
                elif status == "unknown":
                    user_error_msg = "Generation service is experiencing issues. Please try again later."
                    logger.error(f"❌ Tripo task status unknown - system level issue")
                    update_job_status(record_id, "failed", user_error_msg)
                    return
                
                # Handle ongoing statuses
                elif status in ("queued", "running"):
                    # Continue polling
                    pass
                else:
                    # Unknown status, log and continue
                    logger.warning(f"⚠️ Unknown status '{status}' for task {task_id}")
                
                import time
                time.sleep(10)  # Wait 10 seconds before next poll
                
            except Exception as e:
                logger.error(f"Error polling task {task_id}: {e}")
                if attempt == max_attempts - 1:
                    update_job_status(record_id, "failed", "Generation timed out. Please try again.")
                    return
                time.sleep(10)
        
        # If we get here, we've exceeded max attempts
        update_job_status(record_id, "failed", "Generation timed out. Please try again.")
        
    except Exception as e:
        error_msg = f"Error in single image background processing: {str(e)}"
        logger.error(f"❌ {error_msg}")
        update_job_status(record_id, "failed", error_msg)

def update_job_status(record_id, status, error_message=None):
    """Update job status in database"""
    try:
        if SUPABASE_AVAILABLE and supabase_client:
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            if error_message:
                update_data["error_message"] = error_message
            
            supabase_client.table('generated_images').update(update_data).eq('id', record_id).execute()
            logger.info(f"✅ Updated record {record_id} status to: {status}")
    except Exception as e:
        logger.error(f"Error updating job status: {e}")

@app.route('/api/generation-status/<record_id>')
def get_generation_status(record_id):
    """Check status of a 3D generation job"""
    try:
        if not SUPABASE_AVAILABLE or not supabase_client:
            return jsonify({"error": "Database not available"}), 500
        
        # Add retry logic for database connection issues
        max_retries = 5
        for attempt in range(max_retries):
            try:
                result = supabase_client.table('generated_images').select('*').eq('id', record_id).execute()
                break
            except Exception as db_error:
                if attempt == max_retries - 1:
                    logger.error(f"Database connection failed after {max_retries} attempts: {db_error}")
                    return jsonify({"error": "Database connection failed"}), 500
                logger.warning(f"Database connection attempt {attempt + 1} failed, retrying...")
                import time
                time.sleep(0.5)  # Short delay before retry
        
        if not result.data:
            return jsonify({"error": "Record not found"}), 404
        
        record = result.data[0]
        
        # Return status information
        response = {
            "record_id": record_id,
            "status": record.get("status", "unknown"),
            "task_id": record.get("task_id"),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "target_object": record.get("target_object"),
            "iteration": record.get("iteration")
        }
        
        # Add result data if completed
        if record.get("status") == "completed":
            response["3d_url"] = record.get("3d_url")
            response["image_url"] = record.get("image_url")
        
        # Add error information if failed
        if record.get("status") in ["failed", "cancelled", "timeout"]:
            response["error_message"] = record.get("error_message")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting generation status: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_sessions)
    })

@app.route('/api/image-sizes')
def get_image_sizes():
    """Get supported image sizes for GPT-Image-1"""
    return jsonify({
        "supported_sizes": SUPPORTED_IMAGE_SIZES,
        "default_size": DEFAULT_IMAGE_SIZE,
        "descriptions": {
            "1024x1024": "Square format - good for objects with similar width and height",
            "1024x1536": "Portrait format - better for tall objects (e.g., people, buildings, trees)",
            "1536x1024": "Landscape format - better for wide objects (e.g., cars, furniture, animals)"
        }
    })

# Studio API Routes (Supabase only)

@app.route('/api/studio/supabase/images')
def list_supabase_studio_images():
    """List images from Supabase storage using the generated_images table"""
    try:
        if not SUPABASE_STUDIO_AVAILABLE:
            return jsonify({"error": "Supabase Studio functionality not available"}), 503
        
        # Get query parameters
        max_results = int(request.args.get('max_results', 100))
        search_query = request.args.get('search', '')
        
        # Create Supabase studio manager
        supabase_manager = create_supabase_studio_manager()
        
        # Initialize the manager
        init_result = supabase_manager.initialize()
        if not init_result["success"]:
            return jsonify({"error": f"Supabase initialization failed: {init_result['error']}"}), 503
        
        # Search or list images
        if search_query:
            result = supabase_manager.search_images(search_query, max_results)
        else:
            result = supabase_manager.list_public_images(max_results=max_results)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "images": result["images"],
                "total_count": result["total_count"],
                "search_query": search_query if search_query else None
            })
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        logger.error(f"Error listing Supabase studio images: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/studio/supabase/images/<int:image_id>')
def get_supabase_studio_image_metadata(image_id):
    """Get metadata for a specific Supabase studio image by ID"""
    try:
        if not SUPABASE_STUDIO_AVAILABLE:
            return jsonify({"error": "Supabase Studio functionality not available"}), 503
        
        # Create Supabase studio manager
        supabase_manager = create_supabase_studio_manager()
        
        # Initialize the manager
        init_result = supabase_manager.initialize()
        if not init_result["success"]:
            return jsonify({"error": f"Supabase initialization failed: {init_result['error']}"}), 503
        
        # Get image metadata
        result = supabase_manager.get_image_metadata(image_id=image_id)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "metadata": result["metadata"]
            })
        else:
            return jsonify({"error": result["error"]}), 404
            
    except Exception as e:
        logger.error(f"Error getting Supabase studio image metadata: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/studio/supabase/images/insert', methods=['POST'])
def insert_supabase_studio_image():
    """Insert a new image record into the generated_images table"""
    try:
        if not SUPABASE_STUDIO_AVAILABLE:
            return jsonify({"error": "Supabase Studio functionality not available"}), 503
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        target_object = data.get('target_object')
        image_url = data.get('image_url')
        model_3d_url = data.get('model_3d_url')
        iteration = data.get('iteration')
        
        if not target_object or not image_url:
            return jsonify({"error": "target_object and image_url are required"}), 400
        
        # Create Supabase studio manager
        supabase_manager = create_supabase_studio_manager()
        
        # Initialize the manager
        init_result = supabase_manager.initialize()
        if not init_result["success"]:
            return jsonify({"error": f"Supabase initialization failed: {init_result['error']}"}), 503
        
        # Insert image
        result = supabase_manager.insert_image(
            target_object=target_object,
            image_url=image_url,
            model_3d_url=model_3d_url,
            iteration=iteration
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "inserted_id": result["inserted_id"],
                "record": result["record"]
            })
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        logger.error(f"Error inserting Supabase studio image: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/studio/supabase/images/<int:image_id>', methods=['DELETE'])
def delete_supabase_studio_image(image_id):
    """Delete an image and its associated 3D model from storage and database"""
    try:
        if not SUPABASE_STUDIO_AVAILABLE:
            return jsonify({"error": "Supabase Studio functionality not available"}), 503
        
        if not image_id:
            return jsonify({"error": "Image ID is required"}), 400
        
        # Create Supabase studio manager
        supabase_manager = create_supabase_studio_manager()
        
        # Initialize the manager
        init_result = supabase_manager.initialize()
        if not init_result["success"]:
            return jsonify({"error": f"Supabase initialization failed: {init_result['error']}"}), 503
        
        # Delete image
        result = supabase_manager.delete_image(image_id=image_id)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "deleted_record_id": result["deleted_record_id"],
                "deleted_files": result["deleted_files"],
                "message": f"Successfully deleted image ID {image_id}"
            })
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        logger.error(f"Error deleting Supabase studio image: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/api/studio/proxy-file')
def proxy_file():
    """Proxy any file download to bypass CORS restrictions"""
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({"error": "URL parameter is required"}), 400
        
        logger.info(f"🔗 Proxying file from: {url}")
        
        # Import requests for making HTTP requests
        import requests
        
        # Download the file
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Determine content type based on file extension
        content_type = 'application/octet-stream'  # Default
        if url.lower().endswith('.glb'):
            content_type = 'model/gltf-binary'
        elif url.lower().endswith('.gltf'):
            content_type = 'model/gltf+json'
        elif url.lower().endswith('.zip'):
            content_type = 'application/zip'
        elif url.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif url.lower().endswith('.png'):
            content_type = 'image/png'
        
        # Return the file content with appropriate headers
        return Response(
            response.content,
            mimetype=content_type,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                'Content-Length': str(len(response.content))
            }
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading file from {url}: {e}")
        return jsonify({"error": f"Failed to download file: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error proxying file: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/waitlist', methods=['POST'])
def join_waitlist():
    """Add email to waitlist"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Database not available'}), 500
        
        # Check if email already exists
        existing = supabase_client.table('waitlist_signups').select('email').eq('email', email).execute()
        
        if existing.data:
            return jsonify({'message': 'Email already registered', 'status': 'exists'}), 200
        
        # Insert new email
        result = supabase_client.table('waitlist_signups').insert({
            'email': email,
            'source': 'website',
            'metadata': {
                'user_agent': request.headers.get('User-Agent', ''),
                'referrer': request.headers.get('Referer', ''),
                'ip_address': request.remote_addr
            }
        }).execute()
        
        logger.info(f"✅ New waitlist signup: {email}")
        
        return jsonify({
            'message': 'Successfully joined waitlist',
            'status': 'success',
            'email': email
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Waitlist signup error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/waitlist/stats', methods=['GET'])
def waitlist_stats():
    """Get waitlist statistics (admin only)"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Database not available'}), 500
        
        # Get total count
        total = supabase_client.table('waitlist_signups').select('id', count='exact').execute()
        
        # Get recent signups (last 7 days)
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent = supabase_client.table('waitlist_signups').select('id', count='exact').gte('created_at', week_ago).execute()
        
        return jsonify({
            'total_signups': total.count,
            'recent_signups': recent.count,
            'last_updated': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Waitlist stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Wallet/Account Funding Endpoints (properly integrated with Supabase auth)
@app.route('/api/wallet/balance', methods=['GET'])
def get_wallet_balance():
    """Get user's wallet balance using Supabase auth"""
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Database not available'}), 500
        
        # Verify the JWT token and get user info
        try:
            # Use Supabase client to verify the token
            user_response = supabase_client.auth.get_user(token)
            user = user_response.user
            
            if not user:
                return jsonify({'error': 'Invalid token'}), 401
            
            user_id = user.id  # This is the UID from Supabase Users table
            
        except Exception as e:
            logger.error(f"❌ Token verification failed: {str(e)}")
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get user's wallet balance from Supabase
        result = supabase_client.table('user_wallets').select('balance').eq('user_id', user_id).execute()
        
        if result.data:
            balance = result.data[0]['balance']
        else:
            # Create wallet if it doesn't exist with $3 welcome bonus
            balance = create_new_user_wallet(user_id)
        
        return jsonify({
            'balance': balance,
            'currency': 'USD',
            'user_id': user_id,
            'email': user.email
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting wallet balance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/wallet/transactions', methods=['GET'])
def get_transaction_history():
    """Get user's transaction history using Supabase auth"""
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Database not available'}), 500
        
        # Verify the JWT token and get user info
        try:
            user_response = supabase_client.auth.get_user(token)
            user = user_response.user
            
            if not user:
                return jsonify({'error': 'Invalid token'}), 401
            
            user_id = user.id  # Supabase Users.uid
            
        except Exception as e:
            logger.error(f"❌ Token verification failed: {str(e)}")
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get transaction history from Supabase
        result = supabase_client.table('wallet_transactions').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(50).execute()
        
        return jsonify({
            'transactions': result.data or []
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting transaction history: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/wallet/credit', methods=['POST'])
def credit_wallet():
    """Manually credit user's wallet (for payment link payments)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        amount = data.get('amount')
        payment_reference = data.get('payment_reference', 'manual_credit')
        
        if not user_id or not amount:
            return jsonify({'error': 'User ID and amount required'}), 400
        
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Database not available'}), 500
        
        # Get current balance
        result = supabase_client.table('user_wallets').select('balance').eq('user_id', user_id).execute()
        
        if result.data:
            current_balance = result.data[0]['balance']
            new_balance = current_balance + float(amount)
            
            # Update balance
            supabase_client.table('user_wallets').update({
                'balance': new_balance,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).execute()
        else:
            # Create wallet if it doesn't exist with welcome bonus + payment
            new_balance = create_new_user_wallet(user_id) + float(amount)
        
        # Record transaction
        supabase_client.table('wallet_transactions').insert({
            'user_id': user_id,  # Links to Supabase Users.uid
            'type': 'funding',
            'amount': float(amount),
            'payment_intent_id': payment_reference,
            'status': 'completed',
            'description': f'Wallet funded with ${amount}',
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        
        logger.info(f"✅ Wallet credited for user: {user_id}, new balance: ${new_balance}")
        
        return jsonify({
            'success': True,
            'new_balance': new_balance,
            'message': 'Wallet credited successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Error crediting wallet: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/wallet/credit-by-email', methods=['POST'])
def credit_wallet_by_email():
    """Credit user's wallet by email (admin function)"""
    try:
        data = request.get_json()
        user_email = data.get('email')
        amount = data.get('amount')
        payment_reference = data.get('payment_reference', 'manual_credit')
        
        if not user_email or not amount:
            return jsonify({'error': 'Email and amount required'}), 400
        
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Database not available'}), 500
        
        # Find user by email
        try:
            # This requires admin privileges to query auth.users
            # You might need to adjust this based on your Supabase setup
            user_response = supabase_client.auth.admin.list_users()
            user = None
            for u in user_response:
                if u.email == user_email:
                    user = u
                    break
            
            if not user:
                return jsonify({'error': f'User with email {user_email} not found'}), 404
            
            user_id = user.id
            
        except Exception as e:
            logger.error(f"❌ Error finding user by email: {str(e)}")
            return jsonify({'error': 'Could not find user by email'}), 500
        
        # Get current balance
        result = supabase_client.table('user_wallets').select('balance').eq('user_id', user_id).execute()
        
        if result.data:
            current_balance = result.data[0]['balance']
            new_balance = current_balance + float(amount)
            
            # Update balance
            supabase_client.table('user_wallets').update({
                'balance': new_balance,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).execute()
        else:
            # Create wallet if it doesn't exist with welcome bonus + payment
            new_balance = create_new_user_wallet(user_id) + float(amount)
        
        # Record transaction
        supabase_client.table('wallet_transactions').insert({
            'user_id': user_id,
            'type': 'funding',
            'amount': float(amount),
            'payment_intent_id': payment_reference,
            'status': 'completed',
            'description': f'Wallet funded with ${amount}',
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        
        logger.info(f"✅ Wallet credited for user {user_email}, new balance: ${new_balance}")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'email': user_email,
            'new_balance': new_balance,
            'message': 'Wallet credited successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Error crediting wallet by email: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/wallet/credit-by-user-id', methods=['POST'])
def credit_wallet_by_user_id_endpoint():
    """Credit wallet directly by user_id (admin method)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        amount = data.get('amount')
        payment_reference = data.get('payment_reference')
        
        if not user_id or not amount:
            return jsonify({'error': 'user_id and amount are required'}), 400
        
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        success = credit_wallet_by_user_id(user_id, amount, payment_reference)
        
        if success:
            # Get updated balance
            result = supabase_client.table('user_wallets').select('balance').eq('user_id', user_id).execute()
            new_balance = result.data[0]['balance'] if result.data else amount
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'new_balance': new_balance,
                'message': 'Wallet credited successfully'
            })
        else:
            return jsonify({'error': 'Failed to credit wallet'}), 500
            
    except Exception as e:
        logger.error(f"❌ Error crediting wallet by user_id: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def credit_wallet_by_user_id(user_id: str, amount: float, payment_intent_id: str = None) -> bool:
    """Credit wallet directly by user_id (most efficient method)"""
    try:
        logger.info(f"💰 Crediting wallet for user_id: {user_id}, amount: ${amount}")
        
        # Get current balance
        result = supabase_client.table('user_wallets').select('balance').eq('user_id', user_id).execute()
        
        if result.data:
            current_balance = result.data[0]['balance']
            new_balance = current_balance + amount
            
            # Update balance
            supabase_client.table('user_wallets').update({
                'balance': new_balance,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).execute()
        else:
            # Create wallet if it doesn't exist with welcome bonus + payment
            new_balance = create_new_user_wallet(user_id) + amount
        
        # Record transaction
        supabase_client.table('wallet_transactions').insert({
            'user_id': user_id,
            'type': 'funding',
            'amount': amount,
            'payment_intent_id': payment_intent_id,
            'status': 'completed',
            'description': f'Wallet funded with ${amount}',
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        
        logger.info(f"✅ Wallet credited for user_id {user_id}: ${amount} -> ${new_balance}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error crediting wallet for user_id {user_id}: {str(e)}")
        return False

def credit_wallet_by_email(email: str, amount: float, payment_intent_id: str = None) -> bool:
    """Credit wallet by email (fallback method)"""
    try:
        logger.info(f"💰 Crediting wallet for email: {email}, amount: ${amount}")
        
        # Find user by email
        user_response = supabase_client.auth.admin.list_users()
        user = None
        for u in user_response:  # user_response is a list
            if u.email == email:
                user = u
                break
        
        if not user:
            logger.warning(f"⚠️ User not found for email: {email}")
            return False
        
        # Use the helper function to credit by user_id
        return credit_wallet_by_user_id(user.id, amount, payment_intent_id)
        
    except Exception as e:
        logger.error(f"❌ Error crediting wallet for email {email}: {str(e)}")
        return False

@app.route('/api/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events for automatic wallet crediting"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    if not STRIPE_WEBHOOK_SECRET:
        logger.warning("⚠️ STRIPE_WEBHOOK_SECRET not configured")
        return jsonify({'error': 'Webhook secret not configured'}), 400
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"❌ Invalid payload: {str(e)}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"❌ Invalid signature: {str(e)}")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        logger.info(f"✅ Payment completed: {session['id']}")
        
        # Extract payment details
        customer_email = session.get('customer_details', {}).get('email')
        amount_total = session.get('amount_total', 0) / 100  # Convert from cents to dollars
        payment_intent_id = session.get('payment_intent')
        
        # Email-based wallet crediting
        if not customer_email:
            logger.warning(f"⚠️ No customer email found in session: {session['id']}")
            return jsonify({'error': 'No customer email'}), 400
        
        logger.info(f"💰 Processing payment: ${amount_total} for {customer_email}")
        success = credit_wallet_by_email(customer_email, amount_total, payment_intent_id)
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Failed to credit wallet by email'}), 500
    
    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        logger.info(f"⚠️ Payment session expired: {session['id']}")
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        logger.warning(f"⚠️ Payment failed: {payment_intent['id']}")
        
        # Record failed transaction if we can identify the user
        customer_email = payment_intent.get('receipt_email')
        if customer_email and SUPABASE_AVAILABLE:
            try:
                user_response = supabase_client.auth.admin.list_users()
                user = None
                for u in user_response:  # user_response is already a list
                    if u.email == customer_email:
                        user = u
                        break
                
                if user:
                    amount_total = payment_intent.get('amount', 0) / 100
                    supabase_client.table('wallet_transactions').insert({
                        'user_id': user.id,
                        'type': 'funding',
                        'amount': amount_total,
                        'payment_intent_id': payment_intent['id'],
                        'status': 'failed',
                        'description': f'Payment failed - ${amount_total}',
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }).execute()
            except Exception as e:
                logger.error(f"❌ Error recording failed transaction: {str(e)}")
    
    return jsonify({'status': 'success'})

# ============================================================================
# NANO BANANA AI IMAGE EDITING ROUTES
# ============================================================================

# Try to import Google Generative AI for Nano Banana
try:
    import google.generativeai as genai
    NANO_GEMINI_AVAILABLE = True
    logger.info("✅ Google Generative AI imported for Nano Banana")
except ImportError as e:
    logger.warning(f"⚠️ Google Generative AI not available for Nano Banana: {e}")
    NANO_GEMINI_AVAILABLE = False

def setup_nano_gemini():
    """Setup Gemini API configuration for Nano Banana."""
    if not NANO_GEMINI_AVAILABLE:
        return False, "Google Generative AI not available"
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False, "GEMINI_API_KEY environment variable not found"
    
    try:
        genai.configure(api_key=api_key)
        logger.info("✅ Nano Banana Gemini API configured successfully")
        return True, "Gemini API configured successfully"
    except Exception as e:
        logger.error(f"❌ Nano Banana Gemini API configuration failed: {e}")
        return False, f"Gemini API configuration failed: {e}"

def process_nano_image_with_gemini(main_image_bytes, reference_images_bytes=None, edit_instruction=""):
    """
    Process image using Gemini AI for Nano Banana with support for multiple reference images.
    
    Args:
        main_image_bytes: Raw image bytes of the main image to edit
        reference_images_bytes: List of raw image bytes for reference images (optional)
        edit_instruction: Text instruction for editing
        
    Returns:
        tuple: (success, result_data, error_message)
    """
    try:
        # Create the model
        model = genai.GenerativeModel("gemini-2.5-flash-image-preview")
        
        # Create main image part
        main_image_part = {
            "inline_data": {
                "data": main_image_bytes,
                "mime_type": "image/jpeg"
            }
        }
        
        # Start with main image
        contents = [main_image_part]
        
        # Add reference images if provided
        if reference_images_bytes:
            for i, ref_image_bytes in enumerate(reference_images_bytes):
                ref_image_part = {
                    "inline_data": {
                        "data": ref_image_bytes,
                        "mime_type": "image/jpeg"
                    }
                }
                contents.append(ref_image_part)
        
        # Add instruction
        if edit_instruction:
            contents.append(edit_instruction)
        
        logger.info(f"Nano Banana: Processing image with {len(contents)-1} reference images and instruction: {edit_instruction}")
        
        # Generate response
        response = model.generate_content(contents)
        
        # Check for generated image
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Convert base64 to image
                image_data = part.inline_data.data
                edited_image = Image.open(io.BytesIO(image_data))
                
                # Save to bytes
                output_buffer = io.BytesIO()
                edited_image.save(output_buffer, format='PNG')
                output_buffer.seek(0)
                
                logger.info(f"✅ Nano Banana: Image generated successfully: {edited_image.size}")
                return True, output_buffer.getvalue(), None
                
            elif hasattr(part, 'text') and part.text:
                logger.info(f"Nano Banana: Model text response: {part.text}")
        
        return False, None, "No image was generated by the model"
        
    except Exception as e:
        logger.error(f"❌ Nano Banana: Gemini processing failed: {e}")
        return False, None, f"Processing failed: {e}"

@app.route('/api/nano/health', methods=['GET'])
def nano_health_check():
    """Health check endpoint for Nano Banana."""
    gemini_status, gemini_message = setup_nano_gemini()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'nano-banana',
        'gemini_available': NANO_GEMINI_AVAILABLE,
        'gemini_status': gemini_status,
        'gemini_message': gemini_message
    })

@app.route('/api/nano/edit', methods=['POST'])
def nano_edit_image():
    """
    Main endpoint for Nano Banana AI image editing with support for multiple reference images.
    
    Expected JSON payload:
    {
        "image": "base64_encoded_image",
        "reference_images": ["base64_encoded_image1", "base64_encoded_image2", ...],  // optional
        "instruction": "Make this image look like a painting by Van Gogh"
    }
    
    Requires Authorization header with Bearer token
    """
    try:
        # Check if Gemini is available
        if not NANO_GEMINI_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Google Generative AI service not available'
            }), 503
        
        # Setup Gemini
        gemini_ok, gemini_message = setup_nano_gemini()
        if not gemini_ok:
            return jsonify({
                'success': False,
                'error': gemini_message
            }), 500
        
        # Check user authentication
        user, auth_error = get_user_from_token()
        if not user:
            return jsonify({
                'success': False,
                'error': auth_error or 'Authentication required'
            }), 401
        
        # Check user balance (Nano Banana costs $0.10)
        required_credits = 0.1
        has_balance, current_balance = check_user_balance(user.id, required_credits)
        
        if not has_balance:
            return jsonify({
                'success': False,
                'error': f'Insufficient credits. Required: ${required_credits}, Available: ${current_balance:.2f}',
                'current_balance': current_balance,
                'required_credits': required_credits
            }), 402
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        if 'image' not in data or 'instruction' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: image and instruction'
            }), 400
        
        # Decode base64 main image
        try:
            main_image_data = base64.b64decode(data['image'])
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Invalid main image data: {e}'
            }), 400
        
        # Validate main image
        try:
            image = Image.open(io.BytesIO(main_image_data))
            image.verify()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Invalid main image format: {e}'
            }), 400
        
        # Process reference images if provided
        reference_images_data = []
        if 'reference_images' in data and data['reference_images']:
            if not isinstance(data['reference_images'], list):
                return jsonify({
                    'success': False,
                    'error': 'Reference images must be an array'
                }), 400
            
            # Limit to 5 reference images to avoid overwhelming the model
            if len(data['reference_images']) > 5:
                return jsonify({
                    'success': False,
                    'error': 'Maximum 5 reference images allowed'
                }), 400
            
            for i, ref_image_b64 in enumerate(data['reference_images']):
                try:
                    ref_image_data = base64.b64decode(ref_image_b64)
                    # Validate reference image
                    ref_image = Image.open(io.BytesIO(ref_image_data))
                    ref_image.verify()
                    reference_images_data.append(ref_image_data)
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid reference image {i+1}: {e}'
                    }), 400
        
        # Process image with Gemini
        success, result_data, error_message = process_nano_image_with_gemini(
            main_image_data, 
            reference_images_data if reference_images_data else None,
            data['instruction']
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': error_message
            }), 500
        
        # Deduct credits for successful processing
        deduction_success, new_balance = deduct_credits(
            user.id, 
            required_credits, 
            f"Nano Banana image edit: {data['instruction'][:50]}..."
        )
        
        if not deduction_success:
            logger.error(f"❌ Nano Banana: Failed to deduct credits for user {user.id}")
            # Note: We still return the result since the processing was successful
            # The credit deduction failure will be logged for manual review
        
        # Convert result to base64
        result_base64 = base64.b64encode(result_data).decode('utf-8')
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"nano_banana_{timestamp}_{unique_id}.png"
        
        logger.info(f"✅ Nano Banana: Image edited successfully for user {user.id}: {filename}")
        
        return jsonify({
            'success': True,
            'message': 'Image edited successfully',
            'image': result_base64,
            'filename': filename,
            'timestamp': timestamp,
            'size': len(result_data),
            'credits_deducted': required_credits,
            'new_balance': new_balance
        })
        
    except Exception as e:
        logger.error(f"❌ Nano Banana: Unexpected error in edit_image: {e}")
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {e}'
        }), 500

@app.route('/api/auth/check-user', methods=['POST'])
def check_user_exists():
    """Check if a user exists by email"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Database not available'}), 500
        
        # Check if user exists in Supabase auth
        try:
            user_response = supabase_client.auth.admin.list_users()
            user_exists = False
            
            # user_response is a list, not an object with .users property
            for user in user_response:
                if user.email == email:
                    user_exists = True
                    break
            
            return jsonify({
                'exists': user_exists,
                'email': email
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Error checking user existence: {str(e)}")
            return jsonify({'error': 'Could not check user existence'}), 500
        
    except Exception as e:
        logger.error(f"❌ Check user error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def upload_glb_to_supabase(glb_data: bytes, filename: str, bucket_name: str = "generated-3d-files") -> Optional[str]:
    """Upload GLB file to Supabase storage bucket using service key"""
    if not SUPABASE_AVAILABLE or not supabase_client:
        logger.warning("⚠️ Supabase not available, skipping GLB upload")
        return None
    
    try:
        # Validate GLB data
        if not glb_data or len(glb_data) == 0:
            logger.error("❌ Empty GLB data provided")
            return None
        
        # Validate GLB format (GLB files start with 'glTF' magic number)
        if len(glb_data) < 12 or not glb_data.startswith(b'glTF'):
            logger.error("❌ Invalid GLB format: File does not start with 'glTF' magic number")
            logger.error(f"   - First 4 bytes: {glb_data[:4] if len(glb_data) >= 4 else 'insufficient data'}")
            logger.error(f"   - File size: {len(glb_data)} bytes")
            return None
        
        # Check minimum GLB size (should be at least 12 bytes for header)
        if len(glb_data) < 12:
            logger.error("❌ GLB file too small: Must be at least 12 bytes")
            return None
        
        # Log upload attempt
        logger.info(f"📤 Attempting to upload {len(glb_data)} bytes to Supabase bucket '{bucket_name}' as {filename}")
        logger.info(f"   - GLB header: {glb_data[:12].hex()}")
        
        # For large files, try chunked upload or smaller chunks
        max_retries = 5
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Upload attempt {attempt + 1}/{max_retries}")
                
                # Upload to Supabase storage using service key
                response = supabase_client.storage.from_(bucket_name).upload(
                    path=filename,
                    file=glb_data,
                    file_options={"content-type": "model/gltf-binary"}
                )
                
                if response:
                    # Generate public URL
                    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
                    logger.info(f"✅ Uploaded GLB to Supabase bucket '{bucket_name}': {public_url}")
                    return public_url
                else:
                    logger.error("❌ Failed to upload GLB to Supabase - no response")
                    if attempt < max_retries - 1:
                        logger.info("🔄 Retrying upload...")
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Error uploading GLB to Supabase (attempt {attempt + 1}): {e}")
                
                # Handle specific SSL errors
                if "SSL" in str(e) or "protocol" in str(e).lower() or "EOF" in str(e):
                    logger.error("🔒 SSL/Protocol error detected. This may be due to:")
                    logger.error("   - Large file size causing connection issues")
                    logger.error("   - Network connectivity issues")
                    logger.error("   - Supabase service issues")
                    
                    # Try to validate the GLB data
                    try:
                        if glb_data.startswith(b'glTF'):
                            logger.info("✅ GLB validation successful: Valid GLB header detected")
                            logger.info(f"   - GLB size: {len(glb_data)} bytes")
                            logger.info(f"   - GLB header: {glb_data[:12].hex()}")
                        else:
                            logger.error("❌ GLB validation failed: Invalid GLB header")
                            logger.error(f"   - First 4 bytes: {glb_data[:4]}")
                    except Exception as glb_error:
                        logger.error(f"❌ GLB validation failed: {glb_error}")
                    
                    # If this is the last attempt, try alternative upload method
                    if attempt == max_retries - 1:
                        logger.info("🔄 Trying alternative upload method...")
                        return _try_alternative_glb_upload(glb_data, filename, bucket_name)
                    
                    # Wait before retry with exponential backoff
                    import time
                    time.sleep(2 ** attempt)
                    continue
                
                # For other errors, retry if possible
                if attempt < max_retries - 1:
                    logger.info("🔄 Retrying upload...")
                    import time
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return None
        
        return None
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in upload_glb_to_supabase: {e}")
        return None

def _try_alternative_glb_upload(glb_data: bytes, filename: str, bucket_name: str) -> Optional[str]:
    """Alternative GLB upload method using different approach"""
    try:
        logger.info("🔄 Attempting alternative GLB upload method...")
        
        # Try using a different upload approach - maybe the issue is with the file size
        # For very large files, we might need to handle them differently
        
        # Method 1: Try with different file options
        try:
            response = supabase_client.storage.from_(bucket_name).upload(
                path=filename,
                file=glb_data,
                file_options={
                    "content-type": "model/gltf-binary",
                    "upsert": True  # Try upsert mode
                }
            )
            
            if response:
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
                logger.info(f"✅ Alternative upload method successful: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"⚠️ Alternative method 1 failed: {e}")
        
        # Method 2: Try with different content type
        try:
            response = supabase_client.storage.from_(bucket_name).upload(
                path=filename,
                file=glb_data,
                file_options={"content-type": "application/octet-stream"}
            )
            
            if response:
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
                logger.info(f"✅ Alternative upload method 2 successful: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"⚠️ Alternative method 2 failed: {e}")
        
        # Method 3: Try without file options
        try:
            response = supabase_client.storage.from_(bucket_name).upload(
                path=filename,
                file=glb_data
            )
            
            if response:
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
                logger.info(f"✅ Alternative upload method 3 successful: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"⚠️ Alternative method 3 failed: {e}")
        
        logger.error("❌ All alternative upload methods failed")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error in alternative upload method: {e}")
        return None

if __name__ == '__main__':
    # For production deployment on EC2
    app.run(debug=False, host='0.0.0.0', port=8001) 