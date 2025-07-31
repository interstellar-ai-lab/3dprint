# 3D Generation Multi-Agent Web App

A modern web interface for the 3D CAD generation multi-agent system. This web app provides a beautiful, responsive UI that allows users to generate 3D models through an iterative AI agent workflow.

## Features

- 🎨 **Modern UI**: Beautiful, responsive design with real-time status updates
- 🤖 **Multi-Agent Workflow**: Uses generation and evaluation agents for iterative improvement
- 📊 **Real-time Progress**: Live status updates and progress tracking
- 🖼️ **Image Display**: Shows generated images as they're created
- 📋 **Metadata Viewing**: Displays generated metadata for 3D CAD reconstruction
- 📈 **Evaluation Reports**: Shows detailed evaluation reports for each iteration
- 🔄 **Background Processing**: Long-running generation tasks run in the background

## Installation

1. **Activate your virtual environment:**
   ```bash
   source ../env/Scripts/activate  # On macOS/Linux
   # or
   ../env/Scripts/activate.bat     # On Windows
   ```

2. **Install web app dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the main project:**
   ```bash
   pip install -e ..
   ```

## Running the Web App

1. **Start the web server:**
   ```bash
   python main.py
   ```

2. **Open your browser and navigate to:**
   ```
   http://localhost:8000
   ```

## Usage

1. **Enter your query**: Describe what you want to generate (e.g., "a detailed dog model", "a modern chair")

2. **Click "Generate 3D Model"**: The system will start the multi-agent workflow

3. **Monitor progress**: Watch the real-time status updates as the agents work

4. **View results**: See the generated image, metadata, and evaluation reports

## API Endpoints

- `GET /` - Main web interface
- `POST /api/generate` - Start a new generation session
- `GET /api/status/{session_id}` - Get status of a generation session
- `GET /api/image/{session_id}` - Get the generated image
- `GET /api/sessions` - List all active sessions

## Architecture

The web app consists of:

- **FastAPI Backend**: Handles API requests and background processing
- **Modern Frontend**: Responsive HTML/CSS/JavaScript interface
- **Background Tasks**: Long-running generation processes
- **Session Management**: Tracks multiple generation sessions
- **Real-time Updates**: Polling-based status updates

## Development

To modify the web app:

1. **Backend changes**: Edit `main.py`
2. **Frontend changes**: Edit `static/index.html`
3. **Restart the server** after making changes

## Troubleshooting

- **Port already in use**: Change the port in `main.py` (line 200)
- **Import errors**: Make sure you're in the virtual environment and have installed all dependencies
- **API errors**: Check the console output for detailed error messages 