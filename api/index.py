"""Vercel Python entrypoint for the existing XParallel HTTP handler."""
from xparallel.server import Handler

handler = Handler

__all__ = ["handler"]
