from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from auth import USERNAME, SESSION_COOKIE, create_session, verify_password

LOGIN_HTML = '''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Login · Personal Gaming Assistant</title><style>body{margin:0;background:#020503;color:#e9f8ea;font-family:system-ui;display:grid;place-items:center;min-height:100vh}.box{width:min(390px,90vw);padding:28px;background:rgba(3,12,5,.94);border:1px solid #20ff3b;border-radius:14px;box-shadow:0 0 35px #062d0c}h1{color:#20ff3b}input{width:100%;box-sizing:border-box;margin:7px 0;padding:12px;background:#020703;color:#fff;border:1px solid #20ff3b;border-radius:8px}button{width:100%;padding:12px;margin-top:12px;background:#061608;color:#20ff3b;border:1px solid #20ff3b;border-radius:8px;font-weight:700}.err{color:#ff6b6b}</style></head><body><form class="box" method="post"><h1>▣ PGA Login</h1><p>Personal Gaming Assistant</p><input name="username" placeholder="Gebruikersnaam" autocomplete="username" required><input name="password" type="password" placeholder="Wachtwoord" autocomplete="current-password" required>{error}<button>Inloggen</button></form></body></html>'''


def login_page(error: str = "") -> HTMLResponse:
    return HTMLResponse(LOGIN_HTML.replace("{error}", f'<p class="err">{error}</p>' if error else ""))


def do_login(username: str, password: str):
    if username != USERNAME or not verify_password(password):
        return None
    token = create_session()
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, secure=True, samesite="lax", max_age=43200)
    return response
