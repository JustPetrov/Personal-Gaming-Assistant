from __future__ import annotations

import importlib.util
from pathlib import Path

# dashboard.py is intentionally a sibling of the dashboard/ package. Load it
# explicitly so Python never resolves the package instead of the ASGI app.
_MODULE_PATH = Path(__file__).with_name("dashboard.py")
_SPEC = importlib.util.spec_from_file_location("pga_dashboard_module", _MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load dashboard module from {_MODULE_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app

# Register the dedicated GamesCom Center and global Watcher Center on the same
# FastAPI application used by the existing dashboard.
from dashboard_pages import register  # noqa: E402
register(app)

__all__ = ["app"]
