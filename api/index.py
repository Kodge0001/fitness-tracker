import os
import sys

# Add the project root directory to the python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# Create the WSGI application instance for Vercel Serverless Function handler
app = create_app(os.getenv("FLASK_ENV", "production"))
