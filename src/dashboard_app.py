from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse

# Load the sibling dashboard.py file explicitly. A src/dashboard/ package also
# exists, so a normal `import dashboard` would resolve to the wrong module.
_MODULE_PATH = Path(__file__).with_name("dashboard.py")
_SPEC = importlib.util.spec_from_file_location("pga_dashboard_module", _MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load dashboard module from {_MODULE_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _read(name: str, default):
    path = DATA / name
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value
    except (OSError, json.JSONDecodeError):
        return default


@app.get("/api/watchers")
def watcher_data():
    """Return the latest data grouped for the dedicated watcher dashboard."""
    prices = _read("prices.json", [])
    gamescom = _read("gamescom.json", {})
    updates = _read("updates.json", [])
    history = _read("state/hotel_history.json", [])
    if not isinstance(prices, list):
        prices = []
    if not isinstance(history, list):
        history = []
    hotels = [x for x in prices if x.get("platform") == "GamesCom Hotel" or x.get("type") == "gamescom_hotel_offer"]
    tickets = [x for x in prices if x.get("type") == "gamescom_ticket_status" or str(x.get("product", "")).startswith("GamesCom Ticket")]
    epix = [x for x in prices if "EPIX" in str(x.get("source", "")) or "EPIX" in str(x.get("platform", "")) or "EPIX" in str(x.get("product", ""))]
    watcher_errors = [x for x in updates if x.get("type") == "watcher_error"]
    return {
        "gamescom": gamescom,
        "hotels": hotels,
        "hotel_history": history[-100:],
        "tickets": tickets,
        "epix": epix,
        "announcements": [x for x in gamescom.get("events", []) if x.get("type") not in {"gamescom_schedule", "gamescom_opening_night_live"}],
        "updates": updates[-20:][::-1],
        "watcher_errors": watcher_errors[-20:][::-1],
    }


WATCHER_HTML = r'''<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Watcher Center · Personal Gaming Assistant</title>
<style>
:root{--g:#20ff3b;--bg:#020503;--card:rgba(3,12,5,.9);--line:rgba(32,255,59,.28);--muted:#8aa58d;--warn:#ffd34d;--bad:#ff5b5b}*{box-sizing:border-box}body{margin:0;background:#020503;color:#e9f8ea;font-family:Inter,system-ui,sans-serif}header{position:sticky;top:0;z-index:5;background:rgba(0,5,1,.94);border-bottom:1px solid var(--line);padding:14px 22px;display:flex;align-items:center;gap:12px;backdrop-filter:blur(12px)}.logo{font-weight:800;color:var(--g)}.sub{font-size:12px;color:var(--muted)}button,.nav{background:#061608;color:var(--g);border:1px solid var(--line);border-radius:8px;padding:9px 13px;cursor:pointer;text-decoration:none}.back{margin-left:auto}main{max-width:1600px;margin:auto;padding:22px;display:grid;grid-template-columns:repeat(12,1fr);gap:16px}.card{grid-column:span 6;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:0 0 28px rgba(0,255,40,.06)}.full{grid-column:1/-1}.card h2{margin:0 0 12px;color:var(--g);font-size:15px;text-transform:uppercase;letter-spacing:.8px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:9px 7px;text-align:left;border-bottom:1px solid rgba(32,255,59,.12)}a{color:var(--g)}.pill{display:inline-block;border:1px solid var(--line);padding:4px 8px;border-radius:999px;color:var(--g);font-size:11px;margin:2px}.muted{color:var(--muted)}.ok{color:var(--g)}.warn{color:var(--warn)}.bad{color:var(--bad)}.hero{display:flex;justify-content:space-between;gap:16px;align-items:center}.big{font-size:34px;color:var(--g);font-weight:800}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.mini{border:1px solid var(--line);border-radius:9px;padding:12px;background:#031007}.mini b{display:block;color:var(--g);font-size:20px}@media(max-width:900px){.card{grid-column:1/-1}.grid{grid-template-columns:1fr}}
</style></head><body>
<header><div><div class="logo">▣ PERSONAL GAMING ASSISTANT · WATCHER CENTER</div><div class="sub">LIVE MONITORING · GAMESCOM · HOTELS · TICKETS · EPIX · ANNOUNCEMENTS</div></div><a class="nav back" href="/">← Dashboard</a><button onclick="runUpdate()" id="update">↻ Update</button></header>
<main>
<section class="card full"><div class="hero"><div><h2>GamesCom 2026</h2><div id="gc">Laden...</div></div><div id="sync" class="muted"></div></div></section>
<section class="card"><h2>🏨 Hotel Watcher</h2><div id="hotels">Laden...</div></section>
<section class="card"><h2>🎟️ Ticket Watcher</h2><div id="tickets">Laden...</div></section>
<section class="card"><h2>🎮 EPIX Watcher</h2><div id="epix">Laden...</div></section>
<section class="card"><h2>📢 Announcements</h2><div id="announcements">Laden...</div></section>
<section class="card full"><h2>📈 Hotel Price History</h2><div id="history">Laden...</div></section>
<section class="card full"><h2>⚙️ Monitoring Runs</h2><div id="runs">Laden...</div></section>
<section class="card full"><h2>⚠️ Watcher Errors</h2><div id="errors">Laden...</div></section>
</main>
<script>
const get=async u=>(await fetch(u)).json();const esc=s=>String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function rows(items,cols){if(!items?.length)return '<span class="muted">Geen data beschikbaar.</span>';return '<table><tr>'+cols.map(c=>`<th>${c[0]}</th>`).join('')+'</tr>'+items.map(x=>'<tr>'+cols.map(c=>`<td>${c[1](x)}</td>`).join('')+'</tr>').join('')+'</table>'}
async function load(){const d=await get('/api/watchers');const g=d.gamescom||{};document.querySelector('#gc').innerHTML=`<span class="big">${esc(g.year||'—')}</span> <span class="pill">${esc(g.status||'unknown')}</span><br>${esc(g.live_start||g.start||'—')} → ${esc(g.end||'—')}<br>Opening Night Live: <b>${esc(g.opening_night_live||'—')}</b> · Live dagen: <b>${esc(g.counted_live_days||'—')}</b>`;document.querySelector('#sync').textContent='Laatste sync: '+esc(g.last_synced||'—');document.querySelector('#hotels').innerHTML=rows(d.hotels,[['Hotel',x=>esc(x.product)],['Prijs',x=>esc(x.price_per_night||x.price||'—')+' '+esc(x.currency||'EUR')],['Beschikbaarheid',x=>esc(x.availability||x.stock||'—')],['Bron',x=>x.url?`<a href="${esc(x.url)}" target="_blank">${esc(x.source||'bron')}</a>`:esc(x.source||'—')]]);document.querySelector('#tickets').innerHTML=rows(d.tickets,[['Ticket',x=>esc(x.product)],['Stock',x=>esc(x.stock||'—')],['Dag',x=>esc(x.day||'—')],['Bron',x=>x.url?`<a href="${esc(x.url)}" target="_blank">Open</a>`:esc(x.source||'—')]]);document.querySelector('#epix').innerHTML=rows(d.epix,[['Item',x=>esc(x.product)],['Status',x=>esc(x.stock||'—')],['Bron',x=>esc(x.source||x.platform||'—')]]);document.querySelector('#announcements').innerHTML=d.announcements?.length?d.announcements.map(x=>`<div class="mini"><b>${esc(x.name||x.title||x.type||'Announcement')}</b><br><span class="muted">${esc(x.date||x.status||x.message||'')}</span>${x.url?`<br><a href="${esc(x.url)}" target="_blank">Bron</a>`:''}</div>`).join(''):'<span class="muted">Geen nieuwe announcements.</span>';document.querySelector('#history').innerHTML=rows(d.hotel_history,[['Gecontroleerd',x=>esc(x.checked_at)],['Hotel',x=>esc(x.hotel)],['Per nacht',x=>esc(x.price_per_night||'—')+' '+esc(x.currency||'')],['Totaal',x=>esc(x.total_price||'—')],['Datums',x=>esc(x.check_in||'—')+' → '+esc(x.check_out||'—')]]);document.querySelector('#runs').innerHTML=rows(d.updates,[['Tijd',x=>esc(x.timestamp)],['Type',x=>esc(x.type)],['Status',x=>`<span class="ok">${esc(x.status)}</span>`],['Items',x=>esc(x.items_checked||0)],['Prijsitems',x=>esc(x.price_items||0)],['Changes',x=>esc(x.changes||0)]]);document.querySelector('#errors').innerHTML=rows(d.watcher_errors,[['Tijd',x=>esc(x.timestamp||x.checked_at)],['Watcher',x=>esc(x.source)],['Type',x=>`<span class="bad">${esc(x.error_type)}</span>`],['Fout',x=>esc(x.error)]] )}
async function runUpdate(){const b=document.querySelector('#update');b.disabled=true;b.textContent='⟳ Bezig…';try{await fetch('/api/update',{method:'POST'});await load();b.textContent='✓ Klaar'}catch(e){b.textContent='⚠ Fout'}finally{setTimeout(()=>{b.disabled=false;b.textContent='↻ Update'},1400)}}load();setInterval(load,30000);
</script></body></html>'''


@app.get("/watchers", response_class=HTMLResponse)
def watchers_page():
    return WATCHER_HTML


@app.middleware("http")
async def add_watcher_button(request: Request, call_next):
    response = await call_next(request)
    if request.url.path != "/" or response.status_code != 200:
        return response
    if "text/html" not in response.headers.get("content-type", ""):
        return response
    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    marker = b'<button class="manual" onclick="manualUpdate()">'
    button = b'<a href="/watchers" style="background:#061608;color:#20ff3b;border:1px solid rgba(32,255,59,.28);border-radius:8px;padding:9px 13px;text-decoration:none">Watcher Center</a>'
    body = body.replace(marker, button + marker, 1)
    response.headers.pop("content-length", None)
    return HTMLResponse(content=body, status_code=response.status_code, headers=dict(response.headers), media_type="text/html")


__all__ = ["app"]
