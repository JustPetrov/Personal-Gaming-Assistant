from __future__ import annotations

import importlib.util
from pathlib import Path

# Load the sibling dashboard.py file explicitly. A src/dashboard/ package also
# exists, so a normal `import dashboard` would resolve to the wrong module.
_MODULE_PATH = Path(__file__).with_name("dashboard.py")
_SPEC = importlib.util.spec_from_file_location("pga_dashboard_module", _MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load dashboard module from {_MODULE_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app

__all__ = ["app"]
