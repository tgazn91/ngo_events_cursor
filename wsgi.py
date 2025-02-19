import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/ngo_events_cursor'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import your Flask app
from app import app as application

# Initialize the database if it doesn't exist
from app import db
with application.app_context():
    db.create_all() 