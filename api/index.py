"""Vercel Python entrypoint for the existing XParallel HTTP handler."""
from xparallel.server import Handler

# Vercel detects a lowercase top-level WSGI/HTTP handler export.
handler = Handler

__all__ = ["handler"]
