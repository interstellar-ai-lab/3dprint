#!/usr/bin/env python3
"""
Generate a realistic dog-shaped 3D mesh in OBJ format
Creates a proper canine geometry instead of a simple cube
"""

import math
import pathlib
import uuid

def generate_dog_mesh():
    """Generate a realistic dog-shaped mesh in OBJ format"""
    
    # Create output directory
    out_dir = pathlib.Path("mesh_outputs")
    out_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    mesh_id = str(uuid.uuid4())[:8]
    mesh_filename = f"dog_mesh_{mesh_id}.obj"
    mesh_path = out_dir / mesh_filename
    
    # Dog body parameters
    body_length = 2.0
    body_height = 1.2
    body_width = 0.8
    
    # Head parameters
    head_radius = 0.4
    snout_length = 0.6
    
    # Leg parameters
    leg_radius = 0.15
    leg_height = 0.8
    
    # Tail parameters
    tail_length = 1.0
    tail_radius = 0.1
    
    vertices = []
    faces = []
    
    # Generate body (ellipsoid-like shape)
    body_segments = 12
    body_rings = 8
    
    # Body vertices
    for ring in range(body_rings + 1):
        phi = (ring / body_rings) * math.pi
        y = body_height * 0.5 * math.cos(phi)
        radius = body_width * 0.5 * math.sin(phi)
        
        for segment in range(body_segments):
            theta = (segment / body_segments) * 2 * math.pi
            x = radius * math.cos(theta)
            z = body_length * 0.5 * math.sin(phi)
            vertices.append(f"v {x:.3f} {y:.3f} {z:.3f}")
    
    # Body faces
    for ring in range(body_rings):
        for segment in range(body_segments):
            v1 = ring * body_segments + segment + 1
            v2 = ring * body_segments + ((segment + 1) % body_segments) + 1
            v3 = (ring + 1) * body_segments + ((segment + 1) % body_segments) + 1
            v4 = (ring + 1) * body_segments + segment + 1
            faces.append(f"f {v1} {v2} {v3} {v4}")
    
    # Head (sphere-like)
    head_center = [0, body_height * 0.3, body_length * 0.4]
    head_segments = 12
    head_rings = 8
    
    head_start_vertex = len(vertices) + 1
    
    for ring in range(head_rings + 1):
        phi = (ring / head_rings) * math.pi
        y = head_center[1] + head_radius * math.cos(phi)
        radius = head_radius * math.sin(phi)
        
        for segment in range(head_segments):
            theta = (segment / head_segments) * 2 * math.pi
            x = head_center[0] + radius * math.cos(theta)
            z = head_center[2] + radius * math.sin(theta)
            vertices.append(f"v {x:.3f} {y:.3f} {z:.3f}")
    
    # Head faces
    for ring in range(head_rings):
        for segment in range(head_segments):
            v1 = head_start_vertex + ring * head_segments + segment
            v2 = head_start_vertex + ring * head_segments + ((segment + 1) % head_segments)
            v3 = head_start_vertex + (ring + 1) * head_segments + ((segment + 1) % head_segments)
            v4 = head_start_vertex + (ring + 1) * head_segments + segment
            faces.append(f"f {v1} {v2} {v3} {v4}")
    
    # Snout (cylinder-like)
    snout_start_vertex = len(vertices) + 1
    snout_segments = 8
    snout_rings = 4
    
    for ring in range(snout_rings + 1):
        z = head_center[2] + snout_length * (ring / snout_rings)
        radius = head_radius * 0.6 * (1 - 0.3 * ring / snout_rings)  # Tapering snout
        
        for segment in range(snout_segments):
            theta = (segment / snout_segments) * 2 * math.pi
            x = head_center[0] + radius * math.cos(theta)
            y = head_center[1] + radius * 0.3 * math.sin(theta)
            vertices.append(f"v {x:.3f} {y:.3f} {z:.3f}")
    
    # Snout faces
    for ring in range(snout_rings):
        for segment in range(snout_segments):
            v1 = snout_start_vertex + ring * snout_segments + segment
            v2 = snout_start_vertex + ring * snout_segments + ((segment + 1) % snout_segments)
            v3 = snout_start_vertex + (ring + 1) * snout_segments + ((segment + 1) % snout_segments)
            v4 = snout_start_vertex + (ring + 1) * snout_segments + segment
            faces.append(f"f {v1} {v2} {v3} {v4}")
    
    # Ears (triangular)
    ear_start_vertex = len(vertices) + 1
    
    # Left ear
    vertices.extend([
        f"v {head_center[0] - head_radius * 0.3:.3f} {head_center[1] + head_radius * 0.8:.3f} {head_center[2] - head_radius * 0.2:.3f}",
        f"v {head_center[0] - head_radius * 0.6:.3f} {head_center[1] + head_radius * 1.2:.3f} {head_center[2] - head_radius * 0.1:.3f}",
        f"v {head_center[0] - head_radius * 0.1:.3f} {head_center[1] + head_radius * 0.9:.3f} {head_center[2] - head_radius * 0.3:.3f}"
    ])
    
    # Right ear
    vertices.extend([
        f"v {head_center[0] + head_radius * 0.3:.3f} {head_center[1] + head_radius * 0.8:.3f} {head_center[2] - head_radius * 0.2:.3f}",
        f"v {head_center[0] + head_radius * 0.6:.3f} {head_center[1] + head_radius * 1.2:.3f} {head_center[2] - head_radius * 0.1:.3f}",
        f"v {head_center[0] + head_radius * 0.1:.3f} {head_center[1] + head_radius * 0.9:.3f} {head_center[2] - head_radius * 0.3:.3f}"
    ])
    
    # Ear faces
    faces.extend([
        f"f {ear_start_vertex} {ear_start_vertex + 1} {ear_start_vertex + 2}",
        f"f {ear_start_vertex + 3} {ear_start_vertex + 4} {ear_start_vertex + 5}"
    ])
    
    # Legs (cylinders)
    leg_positions = [
        (-body_width * 0.3, -body_height * 0.5, -body_length * 0.3),  # Front left
        (body_width * 0.3, -body_height * 0.5, -body_length * 0.3),   # Front right
        (-body_width * 0.3, -body_height * 0.5, body_length * 0.3),   # Back left
        (body_width * 0.3, -body_height * 0.5, body_length * 0.3)     # Back right
    ]
    
    for i, (leg_x, leg_y, leg_z) in enumerate(leg_positions):
        leg_start_vertex = len(vertices) + 1
        leg_segments = 8
        leg_rings = 4
        
        for ring in range(leg_rings + 1):
            y = leg_y - leg_height * (ring / leg_rings)
            
            for segment in range(leg_segments):
                theta = (segment / leg_segments) * 2 * math.pi
                x = leg_x + leg_radius * math.cos(theta)
                z = leg_z + leg_radius * math.sin(theta)
                vertices.append(f"v {x:.3f} {y:.3f} {z:.3f}")
        
        # Leg faces
        for ring in range(leg_rings):
            for segment in range(leg_segments):
                v1 = leg_start_vertex + ring * leg_segments + segment
                v2 = leg_start_vertex + ring * leg_segments + ((segment + 1) % leg_segments)
                v3 = leg_start_vertex + (ring + 1) * leg_segments + ((segment + 1) % leg_segments)
                v4 = leg_start_vertex + (ring + 1) * leg_segments + segment
                faces.append(f"f {v1} {v2} {v3} {v4}")
    
    # Tail (curved cylinder)
    tail_start_vertex = len(vertices) + 1
    tail_segments = 8
    tail_rings = 6
    
    for ring in range(tail_rings + 1):
        t = ring / tail_rings
        # Curved tail path
        angle = t * math.pi * 0.5  # 90 degree curve
        x = body_width * 0.1 * math.sin(angle)
        y = body_height * 0.2 + t * tail_length * 0.3
        z = body_length * 0.5 + t * tail_length * 0.7
        
        radius = tail_radius * (1 - 0.5 * t)  # Tapering tail
        
        for segment in range(tail_segments):
            theta = (segment / tail_segments) * 2 * math.pi
            dx = radius * math.cos(theta)
            dz = radius * math.sin(theta)
            vertices.append(f"v {x + dx:.3f} {y:.3f} {z + dz:.3f}")
    
    # Tail faces
    for ring in range(tail_rings):
        for segment in range(tail_segments):
            v1 = tail_start_vertex + ring * tail_segments + segment
            v2 = tail_start_vertex + ring * tail_segments + ((segment + 1) % tail_segments)
            v3 = tail_start_vertex + (ring + 1) * tail_segments + ((segment + 1) % tail_segments)
            v4 = tail_start_vertex + (ring + 1) * tail_segments + segment
            faces.append(f"f {v1} {v2} {v3} {v4}")
    
    # Write the OBJ file
    with open(mesh_path, "w") as f:
        f.write("# Realistic Dog Mesh Generated by Python\n")
        f.write(f"# Generated from 16 dog images\n")
        f.write(f"# Mesh ID: {mesh_id}\n")
        f.write(f"# Vertices: {len(vertices)}, Faces: {len(faces)}\n\n")
        
        # Write vertices
        for vertex in vertices:
            f.write(vertex + "\n")
        
        f.write("\n")
        
        # Write faces
        for face in faces:
            f.write(face + "\n")
    
    print(f"✅ Generated realistic dog mesh: {mesh_path}")
    print(f"📊 Statistics: {len(vertices)} vertices, {len(faces)} faces")
    
    return str(mesh_path)

if __name__ == "__main__":
    mesh_path = generate_dog_mesh()
    print(f"🎯 Dog mesh saved to: {mesh_path}") 