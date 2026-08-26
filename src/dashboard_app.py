from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.responses import HTMLResponse, RedirectResponse

_MODULE_PATH = Path(__file__).with_name("dashboard.py")
_SPEC = importlib.util.spec_from_file_location("pga_dashboard_module", _MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load dashboard module from {_MODULE_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app

from dashboard_pages import register  # noqa: E402
register(app)
from calendar_page import register as register_calendar  # noqa: E402
register_calendar(app)
from steam_stats_page import register as register_steam_stats  # noqa: E402
register_steam_stats(app)
from integrations_page import register as register_integrations  # noqa: E402
register_integrations(app)
from dashboard_navigation import register as register_navigation  # noqa: E402
register_navigation(app)
from watchers_live_prices import register as register_watchers_live_prices  # noqa: E402
register_watchers_live_prices(app)


@app.middleware("http")
async def watchers_live_prices_redirect(request, call_next):
    if request.url.path == "/watchers":
        return RedirectResponse(url="/watchers-live-prices", status_code=307)
    return await call_next(request)
