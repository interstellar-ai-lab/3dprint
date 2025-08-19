#!/usr/bin/env python3
"""
GLB Cleanup Script
Removes tripo tags and other unwanted labels from GLB files.
"""

import json
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

try:
    from pygltflib import GLTF2, Node, Mesh, Scene, Accessor, BufferView, Buffer, Material, Image, Texture, Sampler
except ImportError:
    print("Error: pygltflib not found. Please install it with: pip install pygltflib")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GLBCleaner:
    """Clean GLB files by removing unwanted tags and simplifying structure."""
    
    def __init__(self, input_path: str, output_path: Optional[str] = None):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else self._generate_output_path()
        self.gltf = None
        
    def _generate_output_path(self) -> Path:
        """Generate output path with '_cleaned' suffix."""
        stem = self.input_path.stem
        suffix = self.input_path.suffix
        return self.input_path.parent / f"{stem}_cleaned{suffix}"
    
    def load_glb(self) -> bool:
        """Load GLB file."""
        try:
            logger.info(f"Loading GLB file: {self.input_path}")
            self.gltf = GLTF2().load(str(self.input_path))
            logger.info(f"Successfully loaded GLB with {len(self.gltf.nodes)} nodes")
            return True
        except Exception as e:
            logger.error(f"Failed to load GLB file: {e}")
            return False
    
    def clean_node_names(self, node: Node) -> None:
        """Clean node names by removing tripo tags and other unwanted labels."""
        if hasattr(node, 'name') and node.name:
            original_name = node.name
            
            # Remove tripo-related prefixes and suffixes
            cleaned_name = node.name
            
            # Remove tripo prefixes
            if cleaned_name.startswith('tripo_'):
                cleaned_name = cleaned_name[6:]  # Remove 'tripo_'
            
            # Remove tripo suffixes (hexadecimal patterns)
            if '_' in cleaned_name:
                parts = cleaned_name.split('_')
                # Remove parts that look like hex IDs
                cleaned_parts = []
                for part in parts:
                    # Check for hex patterns (8+ characters, all hex)
                    if len(part) >= 8 and all(c in '0123456789abcdef' for c in part.lower()):
                        # Skip hex-like parts
                        continue
                    # Also check for UUID patterns (8-4-4-4-12 format)
                    if len(part) >= 8 and '-' in part and all(c in '0123456789abcdef-' for c in part.lower()):
                        # Skip UUID-like parts
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
            
            if cleaned_name != original_name:
                logger.info(f"Cleaned node name: '{original_name}' -> '{cleaned_name}'")
                node.name = cleaned_name
    
    def clean_mesh_names(self) -> None:
        """Clean mesh names."""
        if not self.gltf.meshes:
            return
            
        for i, mesh in enumerate(self.gltf.meshes):
            if hasattr(mesh, 'name') and mesh.name:
                original_name = mesh.name
                
                # Remove tripo prefixes
                cleaned_name = mesh.name
                if cleaned_name.startswith('tripo_'):
                    cleaned_name = cleaned_name[6:]
                
                # Remove hex suffixes
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
                    cleaned_name = f'mesh_{i}'
                
                if cleaned_name != original_name:
                    logger.info(f"Cleaned mesh name: '{original_name}' -> '{cleaned_name}'")
                    mesh.name = cleaned_name
    
    def clean_material_names(self) -> None:
        """Clean material names."""
        if not self.gltf.materials:
            return
            
        for i, material in enumerate(self.gltf.materials):
            if hasattr(material, 'name') and material.name:
                original_name = material.name
                
                # Remove tripo prefixes
                cleaned_name = material.name
                if cleaned_name.startswith('tripo_'):
                    cleaned_name = cleaned_name[6:]
                
                # Remove hex suffixes
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
                    cleaned_name = f'material_{i}'
                
                if cleaned_name != original_name:
                    logger.info(f"Cleaned material name: '{original_name}' -> '{cleaned_name}'")
                    material.name = cleaned_name
    
    def clean_texture_names(self) -> None:
        """Clean texture and image names."""
        # Clean textures
        if self.gltf.textures:
            for i, texture in enumerate(self.gltf.textures):
                if hasattr(texture, 'name') and texture.name:
                    original_name = texture.name
                    cleaned_name = self._clean_name(texture.name, f'texture_{i}')
                    if cleaned_name != original_name:
                        logger.info(f"Cleaned texture name: '{original_name}' -> '{cleaned_name}'")
                        texture.name = cleaned_name
        
        # Clean images
        if self.gltf.images:
            for i, image in enumerate(self.gltf.images):
                if hasattr(image, 'name') and image.name:
                    original_name = image.name
                    cleaned_name = self._clean_name(image.name, f'image_{i}')
                    if cleaned_name != original_name:
                        logger.info(f"Cleaned image name: '{original_name}' -> '{cleaned_name}'")
                        image.name = cleaned_name
    
    def _clean_name(self, name: str, default: str) -> str:
        """Generic name cleaning function."""
        if not name:
            return default
        
        # Remove tripo prefixes
        cleaned_name = name
        if cleaned_name.startswith('tripo_'):
            cleaned_name = cleaned_name[6:]
        
        # Remove hex suffixes
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
    
    def remove_unwanted_nodes(self) -> None:
        """Remove unwanted nodes like cameras and lights if they're not essential."""
        if not self.gltf.nodes:
            return
        
        nodes_to_remove = []
        for i, node in enumerate(self.gltf.nodes):
            if hasattr(node, 'name') and node.name:
                # Check if it's a camera or light node
                if (node.name.lower().startswith('camera') or 
                    node.name.lower().startswith('light') or
                    node.name.lower().startswith('lamp')):
                    nodes_to_remove.append(i)
                    logger.info(f"Marked for removal: {node.name}")
        
        # Remove nodes in reverse order to maintain indices
        for i in reversed(nodes_to_remove):
            del self.gltf.nodes[i]
            logger.info(f"Removed node at index {i}")
    
    def clean_scene_structure(self) -> None:
        """Clean up scene structure and remove unnecessary collections."""
        if not self.gltf.scenes:
            return
        
        # If there are multiple scenes, keep only the first one
        if len(self.gltf.scenes) > 1:
            logger.info(f"Found {len(self.gltf.scenes)} scenes, keeping only the first one")
            self.gltf.scenes = [self.gltf.scenes[0]]
        
        # Clean scene names
        for scene in self.gltf.scenes:
            if hasattr(scene, 'name') and scene.name:
                original_name = scene.name
                cleaned_name = self._clean_name(scene.name, 'scene')
                if cleaned_name != original_name:
                    logger.info(f"Cleaned scene name: '{original_name}' -> '{cleaned_name}'")
                    scene.name = cleaned_name
    
    def clean_metadata(self) -> None:
        """Clean up metadata and asset information."""
        if hasattr(self.gltf, 'asset') and self.gltf.asset:
            # Remove or clean up generator information
            if hasattr(self.gltf.asset, 'generator') and self.gltf.asset.generator:
                if 'tripo' in self.gltf.asset.generator.lower():
                    self.gltf.asset.generator = 'GLB Cleaner'
                    logger.info("Cleaned generator metadata")
            
            # Clean up copyright information
            if hasattr(self.gltf.asset, 'copyright') and self.gltf.asset.copyright:
                if 'tripo' in self.gltf.asset.copyright.lower():
                    self.gltf.asset.copyright = ''
                    logger.info("Cleaned copyright metadata")
    
    def clean(self, remove_cameras_lights: bool = False) -> bool:
        """Perform complete GLB cleanup."""
        if not self.load_glb():
            return False
        
        logger.info("Starting GLB cleanup process...")
        
        # Clean node names
        for node in self.gltf.nodes:
            self.clean_node_names(node)
        
        # Clean mesh names
        self.clean_mesh_names()
        
        # Clean material names
        self.clean_material_names()
        
        # Clean texture and image names
        self.clean_texture_names()
        
        # Clean scene structure
        self.clean_scene_structure()
        
        # Clean metadata
        self.clean_metadata()
        
        # Optionally remove cameras and lights
        if remove_cameras_lights:
            self.remove_unwanted_nodes()
        
        return True
    
    def save(self) -> bool:
        """Save the cleaned GLB file."""
        try:
            logger.info(f"Saving cleaned GLB to: {self.output_path}")
            self.gltf.save(str(self.output_path))
            logger.info(f"Successfully saved cleaned GLB file")
            return True
        except Exception as e:
            logger.error(f"Failed to save GLB file: {e}")
            return False
    
    def get_cleanup_summary(self) -> Dict[str, Any]:
        """Get a summary of the cleanup process."""
        if not self.gltf:
            return {"error": "No GLB loaded"}
        
        summary = {
            "input_file": str(self.input_path),
            "output_file": str(self.output_path),
            "file_size_input": self.input_path.stat().st_size if self.input_path.exists() else 0,
            "nodes_count": len(self.gltf.nodes) if self.gltf.nodes else 0,
            "meshes_count": len(self.gltf.meshes) if self.gltf.meshes else 0,
            "materials_count": len(self.gltf.materials) if self.gltf.materials else 0,
            "textures_count": len(self.gltf.textures) if self.gltf.textures else 0,
            "images_count": len(self.gltf.images) if self.gltf.images else 0,
            "scenes_count": len(self.gltf.scenes) if self.gltf.scenes else 0,
        }
        
        if self.output_path.exists():
            summary["file_size_output"] = self.output_path.stat().st_size
        
        return summary

def main():
    parser = argparse.ArgumentParser(description="Clean GLB files by removing tripo tags and unwanted labels")
    parser.add_argument("input_file", help="Path to input GLB file")
    parser.add_argument("-o", "--output", help="Path to output GLB file (default: input_cleaned.glb)")
    parser.add_argument("--remove-cameras-lights", action="store_true", 
                       help="Remove camera and light nodes from the GLB")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--summary", action="store_true", help="Show cleanup summary")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Create cleaner and perform cleanup
    cleaner = GLBCleaner(args.input_file, args.output)
    
    if cleaner.clean(remove_cameras_lights=args.remove_cameras_lights):
        if cleaner.save():
            logger.info("GLB cleanup completed successfully!")
            
            if args.summary:
                summary = cleaner.get_cleanup_summary()
                print("\n" + "="*50)
                print("CLEANUP SUMMARY")
                print("="*50)
                for key, value in summary.items():
                    if key == "file_size_input" or key == "file_size_output":
                        size_mb = value / (1024 * 1024)
                        print(f"{key}: {size_mb:.2f} MB")
                    else:
                        print(f"{key}: {value}")
                print("="*50)
        else:
            logger.error("Failed to save cleaned GLB file")
            sys.exit(1)
    else:
        logger.error("Failed to clean GLB file")
        sys.exit(1)

if __name__ == "__main__":
    main()
