from __future__ import annotations

# Compatibility web entrypoint: import the FastAPI app from dashboard.py without
# colliding with the src/dashboard/ package directory.
from .dashboard import app

__all__ = ["app"]
