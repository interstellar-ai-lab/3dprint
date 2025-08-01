import sys
import os

# Add the current directory and parent directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Import the FastAPI app directly
from main import app

# Use mangum for AWS Lambda/Vercel compatibility
from mangum import Mangum

# Create the handler
handler = Mangum(app) 