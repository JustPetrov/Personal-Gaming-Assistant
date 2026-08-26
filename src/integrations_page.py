from __future__ import annotations

import email.utils
import json
import os
import re
import secrets
import time
from email.header import decode_header
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CHECKLIST = DATA / "integration_checklist.json"
GMAIL_TOKEN = DATA / "gmail_oauth_token.json"
OAUTH_STATE = DATA / "gmail_oauth_state.json"

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
SCOPES = "https://www.googleapis.com/auth/gmail.readonly"


class CheckRequest(BaseModel):
    id: str = Field(min_length=1)
    checked: bool


def _read(path: Path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, value) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _decode(value: str | None) -> str:
    if not value:
        return ""
    out = []
    for text, enc in decode_header(value):
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _oauth_config() -> tuple[str | None, str | None, str]:
    return os.getenv("GOOGLE_CLIENT_ID"), os.getenv("GOOGLE_CLIENT_SECRET"), os.getenv(
        "GOOGLE_REDIRECT_URI", "https://dashboard.justpetrov.com/api/integrations/gmail/callback"
    )


def gmail_connected() -> bool:
    token = _read(GMAIL_TOKEN, {})
    return bool(token.get("access_token") or token.get("refresh_token"))


def gmail_authorize_url() -> str:
    client_id, secret, redirect = _oauth_config()
    if not client_id or not secret:
        raise RuntimeError("GOOGLE_CLIENT_ID en GOOGLE_CLIENT_SECRET ontbreken")
    state = secrets.token_urlsafe(32)
    _write(OAUTH_STATE, {"state": state, "expires": int(time.time()) + 600})
    return GOOGLE_AUTH + "?" + urlencode({
        "client_id": client_id,
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    })


def _token_request(data: dict) -> dict:
    client_id, secret, redirect = _oauth_config()
    if not client_id or not secret:
        raise RuntimeError("Google OAuth is niet geconfigureerd")
    response = httpx.post(GOOGLE_TOKEN, data={**data, "client_id": client_id, "client_secret": secret}, timeout=20)
    response.raise_for_status()
    return response.json()


def gmail_callback(code: str, state: str) -> None:
    saved = _read(OAUTH_STATE, {})
    if not saved or saved.get("state") != state or int(saved.get("expires", 0)) < int(time.time()):
        raise ValueError("Ongeldige of verlopen OAuth state")
    _, _, redirect = _oauth_config()
    token = _token_request({"code": code, "redirect_uri": redirect, "grant_type": "authorization_code"})
    token["obtained_at"] = int(time.time())
    _write(GMAIL_TOKEN, token)
    try:
        OAUTH_STATE.unlink()
    except OSError:
        pass


def _gmail_access_token() -> str:
    token = _read(GMAIL_TOKEN, {})
    if not token:
        raise RuntimeError("Gmail is nog niet gekoppeld")
    expires_at = int(token.get("obtained_at", 0)) + int(token.get("expires_in", 3600)) - 60
    if token.get("access_token") and expires_at > int(time.time()):
        return token["access_token"]
    refresh = token.get("refresh_token")
    if not refresh:
        raise RuntimeError("Gmail refresh token ontbreekt; verbind Gmail opnieuw")
    new_token = _token_request({"refresh_token": refresh, "grant_type": "refresh_token"})
    new_token["refresh_token"] = refresh
    new_token["obtained_at"] = int(time.time())
    _write(GMAIL_TOKEN, new_token)
    return new_token["access_token"]


def _gmail_get(path: str, params: dict | None = None) -> dict:
    token = _gmail_access_token()
    response = httpx.get(f"{GMAIL_API}/{path.lstrip('/')}", params=params, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    if response.status_code == 401:
        token = _gmail_access_token()
        response = httpx.get(f"{GMAIL_API}/{path.lstrip('/')}", params=params, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    response.raise_for_status()
    return response.json()


def _classify(text: str) -> str | None:
    patterns = {
        "ticket": r"ticket|tickets|order confirmation|booking|reservation|eventim|ticketmaster|gamescom",
        "purchase": r"order|purchase|aankoop|bestelling|receipt|factuur|invoice|paypal|steam purchase",
        "preorder": r"pre.?order|pre-order|voorbestelling|pre order",
        "shipping": r"shipped|shipping|verzonden|delivery|geleverd|tracking",
    }
    return next((name for name, pattern in patterns.items() if re.search(pattern, text, re.I)), None)


def scan_gmail() -> list[dict]:
    existing = {x.get("id"): x for x in _read(CHECKLIST, [])}
    result = _gmail_get("messages", {"maxResults": 50, "q": "newer_than:30d"})
    for item in result.get("messages", []):
        message_id = item.get("id")
        try:
            msg = _gmail_get(f"messages/{message_id}", {"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]})
        except Exception as exc:
            print(f"Gmail message read failed: {exc}")
            continue
        headers = {h.get("name", "").lower(): h.get("value", "") for h in msg.get("payload", {}).get("headers", [])}
        subject = _decode(headers.get("subject"))
        sender = _decode(headers.get("from"))
        text = f"{subject} {sender} {msg.get('snippet', '')}"
        category = _classify(text)
        if not category:
            continue
        stable = f"gmail:{message_id}"
        old = existing.get(stable, {})
        existing[stable] = {
            "id": stable,
            "provider": "gmail",
            "category": category,
            "title": subject or "E-mail zonder onderwerp",
            "from": sender,
            "date": headers.get("date", ""),
            "checked": bool(old.get("checked", False)),
        }
    items = list(existing.values())[-500:]
    _write(CHECKLIST, items)
    return items


def scan_all_mail() -> list[dict]:
    if not gmail_connected():
        return _read(CHECKLIST, [])
    return scan_gmail()


def _page(body: str) -> str:
    return f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Integrations · Personal Gaming Assistant</title><style>
:root{{--g:#20ff3b;--bg:#020503;--card:rgba(3,12,5,.94);--line:rgba(32,255,59,.28);--muted:#8aa58d}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:#e9f8ea;font-family:Inter,system-ui,sans-serif}}header{{position:sticky;top:0;z-index:5;background:rgba(0,5,1,.97);border-bottom:1px solid var(--line);padding:14px 18px;display:flex;gap:18px;align-items:center}}header h1{{margin:0;color:var(--g);font-size:20px}}nav{{margin-left:auto;display:flex;gap:7px;overflow-x:auto;white-space:nowrap}}nav a,button{{color:var(--g);background:#061608;border:1px solid var(--line);border-radius:8px;padding:9px 12px;text-decoration:none;cursor:pointer}}nav a:hover,nav a.active,button:hover{{background:#0b2b10}}main{{max-width:1500px;margin:auto;padding:22px;display:grid;grid-template-columns:repeat(12,1fr);gap:16px}}section{{grid-column:span 6;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px}}section.full{{grid-column:1/-1}}h2{{margin:0 0 12px;color:var(--g);font-size:15px;text-transform:uppercase}}.status{{padding:12px;border:1px solid var(--line);border-radius:10px;margin-bottom:10px}}.ok{{color:var(--g)}}.warn{{color:#ffc857}}.muted{{color:var(--muted);font-size:12px}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:9px;border-bottom:1px solid rgba(32,255,59,.12);text-align:left}}.check{{width:auto}}.danger{{color:#ff7777}}@media(max-width:900px){{section{{grid-column:1/-1}}}}
</style></head><body><header><h1>🔌 Integrations</h1><nav><a href="/">🏠 Home</a><a href="/gamescom">🎮 GamesCom</a><a href="/watchers">👁 Watchers</a><a href="/wishlist">❤️ Wishlist</a><a href="/calendar">📅 Calendar</a><a href="/steam-stats">🎮 Steam Stats</a><a class="active" href="/integrations">🔌 Integrations</a></nav></header><main>{body}</main></body></html>'''


def register(app):
    @app.get("/api/integrations/status")
    def status():
        return {"gmail": gmail_connected(), "gmail_oauth_configured": bool(_oauth_config()[0] and _oauth_config()[1]), "discord": bool(os.getenv("DISCORD_WEBHOOK_URL"))}

    @app.get("/api/integrations/gmail/connect")
    def gmail_connect():
        try:
            return RedirectResponse(gmail_authorize_url())
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc

    @app.get("/api/integrations/gmail/callback")
    def gmail_callback_route(code: str | None = None, state: str | None = None, error: str | None = None):
        if error:
            return RedirectResponse("/integrations?gmail_error=" + error)
        if not code or not state:
            raise HTTPException(400, "Google OAuth callback mist code/state")
        try:
            gmail_callback(code, state)
        except Exception as exc:
            return RedirectResponse("/integrations?gmail_error=" + str(exc))
        return RedirectResponse("/integrations?gmail=connected")

    @app.post("/api/integrations/gmail/disconnect")
    def gmail_disconnect():
        try:
            GMAIL_TOKEN.unlink()
        except OSError:
            pass
        return {"connected": False}

    @app.post("/api/integrations/scan")
    def scan():
        try:
            return scan_all_mail()
        except Exception as exc:
            raise HTTPException(502, f"Gmail scan mislukt: {exc}") from exc

    @app.get("/api/integrations/checklist")
    def checklist():
        return _read(CHECKLIST, [])

    @app.post("/api/integrations/checklist")
    def set_check(request: CheckRequest):
        items = _read(CHECKLIST, [])
        for item in items:
            if item.get("id") == request.id:
                item["checked"] = request.checked
                _write(CHECKLIST, items)
                return item
        raise HTTPException(404, "Checklist item not found")

    @app.post("/api/integrations/discord/test")
    def discord_test():
        url = os.getenv("DISCORD_WEBHOOK_URL")
        if not url:
            raise HTTPException(400, "DISCORD_WEBHOOK_URL ontbreekt")
        response = httpx.post(url, json={"embeds": [{"title": "Personal Gaming Assistant", "description": "Discord Webhook integratie werkt."}]}, timeout=15)
        response.raise_for_status()
        return {"sent": True}

    @app.get("/integrations", response_class=HTMLResponse)
    def integrations_page():
        body = '''<section><h2>📧 Gmail</h2><div id="gmail" class="status">Controleren...</div><p class="muted">Verbind Gmail veilig via Google OAuth. De app vraagt alleen leestoegang tot Gmail en bewaart het refresh-token lokaal op de VPS.</p><button onclick="location.href='/api/integrations/gmail/connect'">🔐 Verbinden met Google</button> <button onclick="disconnectGmail()">Ontkoppelen</button></section>
<section><h2>💬 Discord Webhook</h2><div id="discord" class="status">Controleren...</div><p class="muted">Gebruikt door alerts en reminders. De webhook-URL blijft uitsluitend als VPS environment variable opgeslagen.</p><button onclick="testDiscord()">🔔 Test Discord</button></section>
<section><h2>⚙️ Automatische scan</h2><p>De bestaande monitoring worker controleert Gmail automatisch wanneer het account gekoppeld is.</p><button onclick="scan()">↻ Nu scannen</button><div id="scanResult" class="muted" style="margin-top:10px"></div></section>
<section><h2>🔐 Google OAuth configuratie</h2><p class="muted">Benodigd op de VPS: GOOGLE_CLIENT_ID en GOOGLE_CLIENT_SECRET. De redirect URI moet exact overeenkomen met:</p><code>/api/integrations/gmail/callback</code></section>
<section class="full"><h2>☑️ Automatische checklist</h2><p class="muted">Herkende Gmail-berichten worden verzameld zodat je bijvoorbeeld een ticket, aankoop, pre-order of verzending kunt afvinken.</p><div id="items">Laden...</div></section>
<script>
const get=async u=>(await fetch(u)).json();function esc(s){return String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
async function load(){const s=await get('/api/integrations/status');document.querySelector('#gmail').innerHTML=s.gmail?'<span class="ok">● Gmail verbonden via OAuth</span>':s.gmail_oauth_configured?'<span class="warn">● Google OAuth klaar — nog niet verbonden</span>':'<span class="warn">● Google OAuth Client nog niet geconfigureerd</span>';document.querySelector('#discord').innerHTML=s.discord?'<span class="ok">● Webhook geconfigureerd</span>':'<span class="warn">● Webhook nog niet geconfigureerd</span>';const items=await get('/api/integrations/checklist');document.querySelector('#items').innerHTML=items.length?'<table><tr><th></th><th>Type</th><th>Titel</th><th>Afzender</th><th>Datum</th></tr>'+items.slice().reverse().map(x=>`<tr><td><input class="check" type="checkbox" ${x.checked?'checked':''} onchange="checkItem('${esc(x.id)}',this.checked)"></td><td>${esc(x.category)}</td><td>${esc(x.title)}</td><td>${esc(x.from)}</td><td>${esc(x.date)}</td></tr>`).join('')+'</table>':'<div class="muted">Nog geen herkenbare Gmail-berichten.</div>'}
async function scan(){document.querySelector('#scanResult').textContent='Gmail scannen…';const r=await fetch('/api/integrations/scan',{method:'POST'});const j=await r.json();document.querySelector('#scanResult').textContent=r.ok?'Scan voltooid. '+j.length+' checklist-items.':(j.detail||'Scan mislukt.');load()}
async function checkItem(id,checked){await fetch('/api/integrations/checklist',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,checked})})}
async function disconnectGmail(){if(!confirm('Gmail ontkoppelen?'))return;await fetch('/api/integrations/gmail/disconnect',{method:'POST'});load()}
async function testDiscord(){const r=await fetch('/api/integrations/discord/test',{method:'POST'});alert(r.ok?'Discord test verzonden.':(await r.json()).detail||'Discord test mislukt.')}
load();setInterval(load,30000)
</script>'''
        return _page(body)


__all__ = ["register", "scan_all_mail"]
