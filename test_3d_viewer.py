#!/usr/bin/env python3
"""
3D Mesh Viewer for testing generated OBJ files
Uses PyVista for high-quality 3D visualization
"""

import sys
import os
import pathlib
import argparse

def test_mesh_viewer(obj_file_path: str):
    """Test viewing an OBJ mesh file with PyVista"""
    
    print(f"🔍 Testing 3D Mesh Viewer for: {obj_file_path}")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(obj_file_path):
        print(f"❌ OBJ file not found: {obj_file_path}")
        return False
    
    try:
        # Import PyVista
        import pyvista as pv
        print("✅ PyVista imported successfully")
        
        # Read the OBJ file
        print(f"📖 Reading OBJ file: {obj_file_path}")
        mesh = pv.read(obj_file_path)
        
        print(f"✅ Mesh loaded successfully!")
        print(f"📊 Mesh statistics:")
        print(f"   - Number of points: {mesh.n_points}")
        print(f"   - Number of cells: {mesh.n_cells}")
        print(f"   - Bounds: {mesh.bounds}")
        
        # Create a plotter
        plotter = pv.Plotter()
        
        # Add the mesh to the plotter
        plotter.add_mesh(mesh, color='lightblue', show_edges=True, edge_color='black')
        
        # Add some nice features
        plotter.add_axes()
        plotter.add_bounding_box()
        
        # Set a nice background
        plotter.set_background('white')
        
        # Set camera position for better view
        plotter.camera_position = 'iso'
        
        print("🎮 Opening 3D viewer...")
        print("💡 Controls:")
        print("   - Mouse: Rotate, zoom, pan")
        print("   - R: Reset camera")
        print("   - Q: Quit")
        
        # Show the plot
        plotter.show()
        
        return True
        
    except ImportError:
        print("❌ PyVista not installed. Installing...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyvista"])
            print("✅ PyVista installed successfully!")
            print("🔄 Please run the script again.")
            return False
        except Exception as e:
            print(f"❌ Failed to install PyVista: {e}")
            print("💡 You can install it manually with: pip install pyvista")
            return False
            
    except Exception as e:
        print(f"❌ Error viewing mesh: {e}")
        return False

def list_available_meshes():
    """List all available mesh files in mesh_outputs directory"""
    
    mesh_dir = pathlib.Path("mesh_outputs")
    if not mesh_dir.exists():
        print("❌ mesh_outputs directory not found")
        return
    
    print("📁 Available mesh files:")
    print("=" * 40)
    
    obj_files = list(mesh_dir.glob("*.obj"))
    if not obj_files:
        print("❌ No OBJ files found")
        return
    
    for i, obj_file in enumerate(sorted(obj_files)):
        file_size = obj_file.stat().st_size
        print(f"{i+1:2d}. {obj_file.name} ({file_size} bytes)")
        
        # Try to read and show basic info
        try:
            import pyvista as pv
            mesh = pv.read(str(obj_file))
            print(f"     └─ Points: {mesh.n_points}, Cells: {mesh.n_cells}")
        except:
            print(f"     └─ (Could not read mesh info)")

def main():
    parser = argparse.ArgumentParser(description="3D Mesh Viewer for OBJ files")
    parser.add_argument("obj_file", nargs="?", help="Path to OBJ file to view")
    parser.add_argument("--list", action="store_true", help="List available mesh files")
    
    args = parser.parse_args()
    
    if args.list:
        list_available_meshes()
        return
    
    if args.obj_file:
        obj_path = args.obj_file
    else:
        # Default to the latest dog mesh
        mesh_dir = pathlib.Path("mesh_outputs")
        obj_files = list(mesh_dir.glob("mesh_llm_*.obj"))
        if obj_files:
            # Get the most recent file
            latest_file = max(obj_files, key=lambda f: f.stat().st_mtime)
            obj_path = str(latest_file)
            print(f"🎯 Using latest mesh file: {latest_file.name}")
        else:
            print("❌ No mesh files found. Use --list to see available files.")
            return
    
    success = test_mesh_viewer(obj_path)
    
    if success:
        print("✅ 3D viewer test completed successfully!")
    else:
        print("❌ 3D viewer test failed!")

if __name__ == "__main__":
    main() 