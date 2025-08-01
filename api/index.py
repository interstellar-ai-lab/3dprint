import sys
import os

# Add the parent directory to the path so we can import from webapp
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from webapp/main.py
from webapp.main import app

# Update the static files mount to point to the api/static directory
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="api/static"), name="static")

# Export the app for Vercel
handler = app 