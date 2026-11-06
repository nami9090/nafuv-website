"""
Entry point used by cPanel (Phusion Passenger, "Setup Python App").
The settings come from the .env file placed next to manage.py on the server.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nafuvWebsite.settings")

from nafuvWebsite.wsgi import application  # noqa: E402,F401
