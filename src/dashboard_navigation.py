from __future__ import annotations

from fastapi import Request
from fastapi.responses import Response

NAV = '''<div style="position:sticky;top:0;z-index:999;background:rgba(0,5,1,.98);border-bottom:1px solid rgba(32,255,59,.28);padding:8px 12px;display:flex;gap:7px;overflow-x:auto;white-space:nowrap;font-family:system-ui,sans-serif"><a href="/" style="color:#20ff3b;background:#061608;border:1px solid rgba(32,255,59,.28);border-radius:8px;padding:7px 10px;text-decoration:none">🏠 Home</a><a href="/gamescom" style="color:#20ff3b;background:#061608;border:1px solid rgba(32,255,59,.28);border-radius:8px;padding:7px 10px;text-decoration:none">🎮 GamesCom</a><a href="/watchers" style="color:#20ff3b;background:#061608;border:1px solid rgba(32,255,59,.28);border-radius:8px;padding:7px 10px;text-decoration:none">👁 Watchers</a><a href="/wishlist" style="color:#20ff3b;background:#061608;border:1px solid rgba(32,255,59,.28);border-radius:8px;padding:7px 10px;text-decoration:none">❤️ Wishlist</a><a href="/calendar" style="color:#20ff3b;background:#061608;border:1px solid rgba(32,255,59,.28);border-radius:8px;padding:7px 10px;text-decoration:none">📅 Calendar</a><a href="/steam-stats" style="color:#20ff3b;background:#061608;border:1px solid rgba(32,255,59,.28);border-radius:8px;padding:7px 10px;text-decoration:none">🎮 Steam Stats</a><a href="/integrations" style="color:#20ff3b;background:#0b2b10;border:1px solid rgba(32,255,59,.28);border-radius:8px;padding:7px 10px;text-decoration:none">🔌 Integrations</a></div>'''


def register(app):
    @app.middleware("http")
    async def dashboard_tabs(request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return response
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        text = body.decode("utf-8", errors="replace")
        if "<body" in text:
            text = text.replace("<body>", "<body>" + NAV, 1)
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(content=text, status_code=response.status_code, headers=headers, media_type="text/html")
