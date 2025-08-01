import sys
import os

# Add the current directory and parent directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Import the FastAPI app from the local webapp directory
from webapp.main import app

# Export the app for Vercel
handler = app 