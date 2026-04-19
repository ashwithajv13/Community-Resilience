import os
import sys

# Add the backend directory to Python path so imports inside backend/app.py resolve correctly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app import app

# Vercel expects the WSGI application to be exposed as `app`.
__all__ = ["app"]