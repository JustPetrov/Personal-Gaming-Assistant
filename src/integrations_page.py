from __future__ import annotations

import email
import imaplib
import json
import os
import re
from email.header import decode_header
from pathlib import Path

import httpx
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CHECKLIST = DATA / "integration_checklist.json"


class CheckRequest(BaseModel):
    id: str = Field(min_length=1)
    checked: bool


def _read() -> list[dict]:
    try:
        value = json.loads(CHECKLIST.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write(value: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    CHECKLIST.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _decode(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def scan_mail(provider: str) -> list[dict]:
    prefix = provider.upper()
    host = os.getenv(f"{prefix}_IMAP_HOST")
    port = int(os.getenv(f"{prefix}_IMAP_PORT", "993"))
    user = os.getenv(f"{prefix}_EMAIL")
    password = os.getenv(f"{prefix}_APP_PASSWORD")
    if not all((host, user, password)):
        return []
    found = []
    keywords = {
        "ticket": r"ticket|tickets|order confirmation|booking|reservation|eventim|ticketmaster|gamescom",
        "purchase": r"order|purchase|aankoop|bestelling|receipt|factuur|invoice|paypal|steam purchase",
        "preorder": r"pre.?order|pre-order|voorbestelling|pre order",
        "shipping": r"shipped|shipping|verzonden|delivery|geleverd|tracking",
    }
    mail = imaplib.IMAP4_SSL(host, port)
    try:
        mail.login(user, password)
        mail.select("INBOX", readonly=True)
        status, data = mail.search(None, "ALL")
        if status != "OK":
            return []
        ids = data[0].split()[-50:]
        for msg_id in reversed(ids):
            status, raw = mail.fetch(msg_id, "(RFC822)")
            if status != "OK" or not raw or not isinstance(raw[0], tuple):
                continue
            msg = email.message_from_bytes(raw[0][1])
            subject = _decode(msg.get("Subject"))
            sender = _decode(msg.get("From"))
            text = subject + " " + sender
            category = next((name for name, pattern in keywords.items() if re.search(pattern, text, re.I)), None)
            if not category:
                continue
            stable = f"{provider}:{msg.get('Message-ID') or msg_id.decode(errors='ignore')}"
            found.append({"id": stable, "provider": provider, "category": category, "title": subject or "E-mail zonder onderwerp", "from": sender, "checked": False})
    finally:
        try:
            mail.logout()
        except Exception:
            pass
    return found


def scan_all_mail() -> list[dict]:
    existing = {x.get("id"): x for x in _read()}
    for provider in ("gmail", "outlook"):
        try:
            for item in scan_mail(provider):
                if item["id"] in existing:
                    item["checked"] = bool(existing[item["id"]].get("checked"))
                existing[item["id"]] = item
        except Exception as exc:
            print(f"{provider} integration scan failed: {exc}")
    result = list(existing.values())[-500:]
    _write(result)
    return result


def _page(body: str) -> str:
    return f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Integrations · Personal Gaming Assistant</title><style>
:root{{--g:#20ff3b;--bg:#020503;--card:rgba(3,12,5,.94);--line:rgba(32,255,59,.28);--muted:#8aa58d}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:#e9f8ea;font-family:Inter,system-ui,sans-serif}}header{{position:sticky;top:0;z-index:5;background:rgba(0,5,1,.97);border-bottom:1px solid var(--line);padding:14px 18px;display:flex;gap:18px;align-items:center}}header h1{{margin:0;color:var(--g);font-size:20px}}nav{{margin-left:auto;display:flex;gap:7px;overflow-x:auto;white-space:nowrap}}nav a,button{{color:var(--g);background:#061608;border:1px solid var(--line);border-radius:8px;padding:9px 12px;text-decoration:none;cursor:pointer}}nav a:hover,nav a.active,button:hover{{background:#0b2b10}}main{{max-width:1500px;margin:auto;padding:22px;display:grid;grid-template-columns:repeat(12,1fr);gap:16px}}section{{grid-column:span 6;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px}}section.full{{grid-column:1/-1}}h2{{margin:0 0 12px;color:var(--g);font-size:15px;text-transform:uppercase}}.status{{padding:12px;border:1px solid var(--line);border-radius:10px;margin-bottom:10px}}.ok{{color:var(--g)}}.warn{{color:#ffc857}}.muted{{color:var(--muted);font-size:12px}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:9px;border-bottom:1px solid rgba(32,255,59,.12);text-align:left}}input{{background:#020703;color:#fff;border:1px solid var(--line);border-radius:8px;padding:10px;width:100%;margin:6px 0}}.check{{width:auto}}@media(max-width:900px){{section{{grid-column:1/-1}}}}
</style></head><body><header><h1>🔌 Integrations</h1><nav><a href="/">🏠 Home</a><a href="/gamescom">🎮 GamesCom</a><a href="/watchers">👁 Watchers</a><a href="/wishlist">❤️ Wishlist</a><a href="/calendar">📅 Calendar</a><a href="/steam-stats">🎮 Steam Stats</a><a class="active" href="/integrations">🔌 Integrations</a></nav></header><main>{body}</main></body></html>'''


def register(app):
    @app.get("/api/integrations/status")
    def status():
        return {
            "gmail": bool(os.getenv("GMAIL_EMAIL") and os.getenv("GMAIL_APP_PASSWORD")),
            "outlook": bool(os.getenv("OUTLOOK_EMAIL") and os.getenv("OUTLOOK_APP_PASSWORD")),
            "discord": bool(os.getenv("DISCORD_WEBHOOK_URL")),
        }

    @app.post("/api/integrations/scan")
    def scan():
        return scan_all_mail()

    @app.get("/api/integrations/checklist")
    def checklist():
        return _read()

    @app.post("/api/integrations/checklist")
    def set_check(request: CheckRequest):
        items = _read()
        for item in items:
            if item.get("id") == request.id:
                item["checked"] = request.checked
                _write(items)
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
        body = '''<section><h2>📧 Gmail</h2><div id="gmail" class="status">Controleren...</div><p class="muted">De worker kan bevestigingen herkennen voor tickets, aankopen, pre-orders en verzendingen. Gebruik voor Gmail een app-wachtwoord; je normale Gmail-wachtwoord wordt niet opgeslagen in de app.</p><b>VPS configuratie</b><input value="GMAIL_EMAIL" disabled><input value="GMAIL_APP_PASSWORD" disabled></section>
<section><h2>📨 Outlook</h2><div id="outlook" class="status">Controleren...</div><p class="muted">Dezelfde automatische herkenning voor Microsoft/Outlook-mail. Gebruik een app-wachtwoord of een IMAP-credential die je provider toestaat.</p><b>VPS configuratie</b><input value="OUTLOOK_EMAIL" disabled><input value="OUTLOOK_APP_PASSWORD" disabled></section>
<section><h2>💬 Discord Webhook</h2><div id="discord" class="status">Controleren...</div><p class="muted">Gebruikt door alerts en reminders. De webhook-URL blijft uitsluitend als VPS environment variable opgeslagen.</p><input value="DISCORD_WEBHOOK_URL" disabled><button onclick="testDiscord()">🔔 Test Discord</button></section>
<section><h2>⚙️ Automatische scan</h2><p>De bestaande 5-minuten monitoring worker kan de inboxen periodiek scannen zodra Gmail/Outlook zijn geconfigureerd.</p><button onclick="scan()">↻ Nu scannen</button><div id="scanResult" class="muted" style="margin-top:10px"></div></section>
<section class="full"><h2>☑️ Automatische checklist</h2><p class="muted">Herkenbare e-mails worden hier verzameld zodat je bijvoorbeeld een ticket, aankoop, pre-order of verzending kunt afvinken.</p><div id="items">Laden...</div></section>
<script>
const get=async u=>(await fetch(u)).json();function esc(s){return String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
async function load(){const s=await get('/api/integrations/status');for(const k of ['gmail','outlook','discord'])document.querySelector('#'+k).innerHTML=s[k]?'<span class="ok">● Verbonden/geconfigureerd</span>':'<span class="warn">● Nog niet geconfigureerd</span>';const items=await get('/api/integrations/checklist');document.querySelector('#items').innerHTML=items.length?'<table><tr><th></th><th>Type</th><th>Titel</th><th>Afzender</th><th>Provider</th></tr>'+items.slice().reverse().map(x=>`<tr><td><input class="check" type="checkbox" ${x.checked?'checked':''} onchange="checkItem('${esc(x.id)}',this.checked)"></td><td>${esc(x.category)}</td><td>${esc(x.title)}</td><td>${esc(x.from)}</td><td>${esc(x.provider)}</td></tr>`).join('')+'</table>':'<div class="muted">Nog geen herkenbare e-mails. Configureer Gmail/Outlook en voer een scan uit.</div>'}
async function scan(){document.querySelector('#scanResult').textContent='Inboxen scannen…';const r=await fetch('/api/integrations/scan',{method:'POST'});document.querySelector('#scanResult').textContent=r.ok?'Scan voltooid.':'Scan mislukt.';load()}
async function checkItem(id,checked){await fetch('/api/integrations/checklist',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,checked})})}
async function testDiscord(){const r=await fetch('/api/integrations/discord/test',{method:'POST'});alert(r.ok?'Discord test verzonden.':(await r.json()).detail||'Discord test mislukt.')}
load();setInterval(load,30000)
</script>'''
        return _page(body)


__all__ = ["register", "scan_all_mail"]
'''
