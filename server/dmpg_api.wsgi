import sys
import os

# Pfad zur Flask-Anwendung hinzufügen
sys.path.insert(0, "/var/www/dmpg_api")

# WSGI Anwendung laden
from app import app as application

