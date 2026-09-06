"""
Vercel serverless entrypoint. Vercel's Python runtime looks for an
ASGI/WSGI `app` object in files under /api — this just re-exports the
real FastAPI app so nothing in app/ needs to know it's running on
Vercel specifically.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app  # noqa: E402
