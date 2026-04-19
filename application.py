import os
import sys

# Ensure the backend package is importable when Elastic Beanstalk runs from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app import app as application

# Disable debug mode in deployment.
application.debug = False
