from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import json
import os
import sys
import uuid
import pathlib
import base64
from PIL import Image
import io
import tempfile

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)

# Store active sessions (in production, use a proper database)
active_sessions = {}

@app.route('/')
def home():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    """Handle generation requests"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Initialize session data
        active_sessions[session_id] = {
            "status": "starting",
            "query": query,
            "iteration": 0,
            "metadata": None,
            "image_urls": [],
            "b64_images": [],
            "mime_types": [],
            "mesh_file_path": None,
            "mesh_filename": None,
            "iteration_meshes": {},
            "iteration_data": {},
            "evaluations": [],
            "error": None
        }
        
        # For now, simulate the generation process
        # In the future, this would integrate with your multi-agent system
        active_sessions[session_id]["status"] = "generating"
        
        return jsonify({
            'session_id': session_id,
            'status': 'starting',
            'message': 'Generation started successfully',
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<session_id>')
def get_status(session_id):
    """Get status of a generation session"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = active_sessions[session_id]
    
    return jsonify({
        'session_id': session_id,
        'status': session_data['status'],
        'query': session_data['query'],
        'iteration': session_data['iteration'],
        'metadata': session_data['metadata'],
        'image_urls': session_data['image_urls'],
        'b64_images': session_data['b64_images'],
        'mime_types': session_data['mime_types'],
        'mesh_file_path': session_data['mesh_file_path'],
        'mesh_filename': session_data['mesh_filename'],
        'iteration_meshes': session_data['iteration_meshes'],
        'iteration_data': session_data['iteration_data'],
        'evaluations': session_data['evaluations'],
        'error': session_data['error']
    })

@app.route('/api/mesh/<session_id>')
def get_generated_mesh(session_id):
    """Get the generated mesh file for a session"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = active_sessions[session_id]
    if not session_data['mesh_file_path']:
        return jsonify({'error': 'No mesh generated yet'}), 404
    
    mesh_path = pathlib.Path(session_data['mesh_file_path'])
    if not mesh_path.exists():
        return jsonify({'error': 'Mesh file not found'}), 404
    
    filename = session_data['mesh_filename'] or f"mesh_{session_id}.obj"
    return send_file(
        mesh_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/octet-stream'
    )

@app.route('/api/mesh/<session_id>/<int:iteration>')
def get_iteration_mesh(session_id, iteration):
    """Get the generated mesh file for a specific iteration"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = active_sessions[session_id]
    if iteration not in session_data['iteration_meshes']:
        return jsonify({'error': f'No mesh found for iteration {iteration}'}), 404
    
    mesh_path = pathlib.Path(session_data['iteration_meshes'][iteration])
    if not mesh_path.exists():
        return jsonify({'error': 'Mesh file not found'}), 404
    
    filename = f"mesh_{session_id}_iteration_{iteration}.obj"
    return send_file(
        mesh_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/octet-stream'
    )

@app.route('/api/mesh-visualization/<session_id>/<int:iteration>')
def get_mesh_visualization(session_id, iteration):
    """Get PNG mesh visualization for a specific iteration"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = active_sessions[session_id]
    if iteration not in session_data['iteration_meshes']:
        return jsonify({'error': f'No mesh found for iteration {iteration}'}), 404
    
    # Look for PNG file with same base name as the OBJ file
    mesh_path = pathlib.Path(session_data['iteration_meshes'][iteration])
    png_path = mesh_path.with_suffix('.png')
    
    if not png_path.exists():
        return jsonify({'error': 'Mesh visualization not found'}), 404
    
    return send_file(
        png_path,
        as_attachment=True,
        download_name=f"mesh_visualization_{session_id}_iteration_{iteration}.png",
        mimetype='image/png'
    )

@app.route('/api/sessions')
def list_sessions():
    """List all active sessions"""
    return jsonify({
        'sessions': [
            {
                'session_id': session_id,
                'status': data['status'],
                'query': data['query'],
                'iteration': data['iteration']
            }
            for session_id, data in active_sessions.items()
        ]
    })

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Flask app is running'
    })

if __name__ == '__main__':
    app.run(debug=True) 