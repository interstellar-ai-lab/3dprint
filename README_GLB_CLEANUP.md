# GLB Cleanup Script

A Python script to clean up GLB (GL Binary) files by removing unwanted tags, labels, and metadata, particularly those from Tripo and other 3D generation services.

## Features

- **Remove Tripo Tags**: Cleans up node, mesh, material, and texture names that contain "tripo" prefixes
- **Remove Hex IDs**: Removes hexadecimal identifiers commonly added by 3D generation services
- **Clean Metadata**: Removes or updates generator and copyright information
- **Optional Camera/Light Removal**: Can remove camera and light nodes if not needed
- **Preserve Structure**: Maintains the 3D model's geometry and materials while cleaning names
- **Detailed Logging**: Provides verbose output of all changes made

## Installation

1. Install the required dependency:
```bash
pip install pygltflib
```

2. Download the script:
```bash
# The script is already in your project directory
```

## Usage

### Basic Usage

```bash
python glb_cleanup.py "path/to/your/file.glb"
```

This will create a cleaned version with `_cleaned` suffix in the same directory.

### Advanced Usage

```bash
# Specify output file
python glb_cleanup.py "input.glb" -o "output.glb"

# Remove cameras and lights
python glb_cleanup.py "input.glb" --remove-cameras-lights

# Verbose logging
python glb_cleanup.py "input.glb" --verbose

# Show cleanup summary
python glb_cleanup.py "input.glb" --summary

# Combine options
python glb_cleanup.py "input.glb" -o "clean_output.glb" --remove-cameras-lights --verbose --summary
```

### Command Line Options

- `input_file`: Path to the input GLB file (required)
- `-o, --output`: Path to output GLB file (default: input_cleaned.glb)
- `--remove-cameras-lights`: Remove camera and light nodes from the GLB
- `--verbose, -v`: Enable verbose logging
- `--summary`: Show detailed cleanup summary

## What Gets Cleaned

### Node Names
- Removes `tripo_` prefixes
- Removes hexadecimal suffixes (e.g., `b8e7a55f-271c-46`)
- Removes common suffixes like `_node`, `_mesh`, `_object`, `_model`
- Cleans up multiple underscores
- Provides default names if cleaning results in empty names

### Mesh Names
- Same cleaning as node names
- Removes `_mesh`, `_geometry`, `_object` suffixes
- Provides numbered defaults (e.g., `mesh_0`, `mesh_1`)

### Material Names
- Removes `tripo_` prefixes
- Removes `_material`, `_mat`, `_shader` suffixes
- Provides numbered defaults (e.g., `material_0`, `material_1`)

### Texture and Image Names
- Cleans texture names
- Cleans image names
- Removes hex identifiers
- Provides numbered defaults

### Scene Names
- Cleans scene names
- Removes unnecessary collections
- Keeps only the first scene if multiple exist

### Metadata
- Updates generator information if it contains "tripo"
- Clears copyright information if it contains "tripo"

## Example Transformations

### Before (with Tripo tags):
```
Node: tripo_node_b8e7a55f-271c-46
Mesh: tripo_mesh_b8e7a55f-271c-46
Material: tripo_material_b8e7a55f-271c-46
Texture: tripo_texture_b8e7a55f-271c-46
Scene: tripo_scene_b8e7a55f-271c-46
```

### After (cleaned):
```
Node: object
Mesh: mesh_0
Material: material_0
Texture: texture_0
Scene: scene
```

## Testing

Use the test script to verify cleanup results:

```bash
python test_glb_cleanup.py
```

This will compare the original and cleaned files and show all changes made.

## Example Output

```
2025-08-19 15:08:43,696 - INFO - Loading GLB file: /path/to/file.glb
2025-08-19 15:08:43,797 - INFO - Successfully loaded GLB with 1 nodes
2025-08-19 15:08:43,797 - INFO - Starting GLB cleanup process...
2025-08-19 15:08:43,797 - INFO - Cleaned node name: 'tripo_node_b8e7a55f-271c-46' -> 'object'
2025-08-19 15:08:43,797 - INFO - Cleaned mesh name: 'tripo_mesh_b8e7a55f-271c-46' -> 'mesh_0'
2025-08-19 15:08:43,797 - INFO - Cleaned material name: 'tripo_material_b8e7a55f-271c-46' -> 'material_0'
2025-08-19 15:08:43,797 - INFO - Saving cleaned GLB to: /path/to/file_cleaned.glb
2025-08-19 15:08:43,849 - INFO - Successfully saved cleaned GLB file
2025-08-19 15:08:43,849 - INFO - GLB cleanup completed successfully!

==================================================
CLEANUP SUMMARY
==================================================
input_file: /path/to/file.glb
output_file: /path/to/file_cleaned.glb
file_size_input: 41.86 MB
nodes_count: 1
meshes_count: 1
materials_count: 1
textures_count: 3
images_count: 3
scenes_count: 1
file_size_output: 41.86 MB
==================================================
```

## Use Cases

1. **3D Model Preparation**: Clean up models before importing into game engines
2. **Asset Library Management**: Standardize naming conventions across your 3D assets
3. **Web3D Applications**: Prepare models for web-based 3D viewers
4. **3D Printing**: Clean up models before slicing for 3D printing
5. **Content Creation**: Remove service-specific tags from generated 3D content

## Limitations

- The script preserves the 3D geometry and materials
- File size typically remains the same (cleaning only affects metadata)
- Some complex naming patterns might require manual adjustment
- The script is designed for GLB format (binary glTF)

## Troubleshooting

### Common Issues

1. **"pygltflib not found"**: Install with `pip install pygltflib`
2. **"Input file not found"**: Check the file path is correct
3. **"Failed to load GLB file"**: Ensure the file is a valid GLB format
4. **No changes detected**: The file might not contain the patterns the script looks for

### Getting Help

If you encounter issues:
1. Run with `--verbose` flag for detailed logging
2. Check that the input file is a valid GLB format
3. Verify the file has the expected naming patterns

## Contributing

Feel free to extend the script with additional cleaning patterns or features. The modular design makes it easy to add new cleaning functions.
