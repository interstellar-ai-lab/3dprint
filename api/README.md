# 3D Generation Multi-Agent Flask App

This is a Flask-based web application that provides a modern UI/UX for the 3D Generation Multi-Agent system. The app has been migrated from the original FastAPI implementation to Flask for better compatibility and deployment options.

## Features

- 🎨 **Modern UI/UX**: Beautiful gradient design with responsive layout
- 🚀 **Real-time Status Updates**: Live polling of generation progress
- 🖼️ **Image Display**: Grid layout for viewing generated images
- 🔲 **3D Mesh Support**: Download generated 3D mesh files
- 📊 **Progress Tracking**: Visual progress bar and status indicators
- 📱 **Mobile Responsive**: Works on desktop and mobile devices
- ⚡ **Dual Generation Modes**: Quick Mode (3 iterations) and Deep Think Mode (10 iterations)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask app:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:8080
```

## Deployment

The Flask app can be deployed to various platforms:

### Local Development
```bash
python app.py
```

### Production Deployment
For production deployment, use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### Cloud Platforms
The app is compatible with various cloud platforms:
- **Heroku**: Use Procfile with `web: gunicorn app:app`
- **AWS**: Deploy to EC2 or use AWS Lambda with API Gateway
- **Google Cloud**: Deploy to App Engine or Cloud Run
- **Azure**: Deploy to App Service or Container Instances

## API Endpoints

### Core Endpoints
- `GET /` - Main application page
- `POST /api/generate` - Start a new generation session (supports `mode` parameter: "quick" or "deep")
- `GET /api/status/<session_id>` - Get status of a generation session
- `GET /api/health` - Health check endpoint

### File Download Endpoints
- `GET /api/mesh/<session_id>` - Download generated mesh file
- `GET /api/mesh/<session_id>/<iteration>` - Download mesh for specific iteration
- `GET /api/mesh-visualization/<session_id>/<iteration>` - Download mesh visualization PNG

### Session Management
- `GET /api/sessions` - List all active sessions

## Project Structure

```
api/
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main HTML template
├── static/               # Static assets (CSS, JS, images)
└── README.md            # This file
```

**Note**: The main Flask application (`app.py`) has been removed as it was specific to Vercel deployment. The web application functionality is now available in the `webapp/` directory.

## UI/UX Features

### Design Elements
- **Gradient Background**: Modern purple-blue gradient
- **Card-based Layout**: Clean, organized content sections
- **Hover Effects**: Interactive elements with smooth transitions
- **Loading States**: Spinner animations and progress indicators
- **Status Indicators**: Color-coded status dots with animations

### Responsive Design
- **Grid Layout**: Adaptive grid system for different screen sizes
- **Mobile Optimization**: Touch-friendly interface elements
- **Flexible Images**: Responsive image grid with proper scaling

### Interactive Features
- **Real-time Updates**: Automatic status polling every 2 seconds
- **Dynamic Content**: Sections appear/disappear based on generation state
- **Error Handling**: User-friendly error messages with auto-dismiss
- **Download Integration**: Direct file downloads for generated content

## Generation Modes

The application supports two different generation modes to suit different use cases:

### 🚀 Quick Mode (3 iterations)
- **Best for**: Initial testing and rapid prototyping
- **Iterations**: Maximum 3 iterations
- **Use case**: When you want to quickly see results and iterate on the concept
- **Time**: Faster generation, typically 2-3 minutes

### 🧠 Deep Think Mode (10 iterations)
- **Best for**: Production-quality results and final outputs
- **Iterations**: Maximum 10 iterations
- **Use case**: When you need the highest quality results for 3D reconstruction
- **Time**: More comprehensive generation, typically 5-8 minutes

## Integration with Multi-Agent System

The Flask app is designed to integrate with the existing multi-agent system:

1. **Session Management**: Each generation request creates a unique session
2. **Status Tracking**: Real-time updates on generation progress
3. **File Handling**: Support for downloading generated meshes and visualizations
4. **Iteration Support**: Track multiple iterations of the generation process
5. **Mode Selection**: Choose between Quick and Deep Think modes based on requirements

## Development

### Adding New Features
1. Update the Flask routes in `app.py`
2. Modify the HTML template in `templates/index.html`
3. Add any new static assets to the `static/` directory

### Styling
The app uses modern CSS with:
- CSS Grid and Flexbox for layout
- CSS animations and transitions
- Responsive design principles
- Modern color schemes and typography

### JavaScript
The frontend JavaScript handles:
- Form submission and validation
- Real-time status polling
- Dynamic content updates
- Error handling and user feedback

## Deployment

This Flask app is designed to be easily deployable on various platforms:

- **Local Development**: Run with `python app.py` (when available)
- **Production**: Use a WSGI server like Gunicorn
- **Cloud Platforms**: Compatible with Heroku, AWS, Google Cloud, Azure, etc.

## Future Enhancements

- [ ] Integration with actual multi-agent backend
- [ ] 3D model viewer with Three.js
- [ ] User authentication and session management
- [ ] Database integration for persistent storage
- [ ] Real-time WebSocket updates
- [ ] Advanced mesh visualization features 