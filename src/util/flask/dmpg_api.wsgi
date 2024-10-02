import sys
import os

# add path to flask application
sys.path.insert(0, "/var/www/dmpg_api")

# load wsgi application
from app import app as application

