from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.responses import HTMLResponse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _read(name: str, default: Any):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _observations() -> list[dict]:
    state = _read("watcher_state.json", [])
    if isinstance(state, dict):
        state = state.get("observations", [])
    return state if isinstance(state, list) else []


def _page(title: str, body: str) -> str:
    return f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Personal Gaming Assistant</title><style>
:root{{--g:#20ff3b;--bg:#020503;--card:rgba(3,12,5,.94);--line:rgba(32,255,59,.28);--muted:#8aa58d}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:#e9f8ea;font-family:Inter,system-ui,sans-serif}}header{{position:sticky;top:0;z-index:5;background:rgba(0,5,1,.97);border-bottom:1px solid var(--line);padding:14px 22px;display:flex;gap:18px;align-items:center}}header h1{{margin:0;color:var(--g);font-size:20px}}nav{{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}}nav a,button{{color:var(--g);background:#061608;border:1px solid var(--line);border-radius:8px;padding:9px 12px;text-decoration:none;cursor:pointer}}nav a:hover,button:hover,nav a.active{{background:#0b2b10}}main{{max-width:1600px;margin:auto;padding:22px;display:grid;grid-template-columns:repeat(12,1fr);gap:16px}}section{{grid-column:span 4;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:0 0 25px rgba(0,255,40,.05)}}section.wide{{grid-column:span 8}}section.full{{grid-column:1/-1}}h2{{margin:0 0 12px;color:var(--g);font-size:15px;text-transform:uppercase}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:8px;border-bottom:1px solid rgba(32,255,59,.12);text-align:left}}a{{color:var(--g)}}.pill{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 8px;margin:2px;color:var(--g);font-size:11px}}.ok{{color:var(--g)}}.muted{{color:var(--muted)}}.item{{padding:10px 0;border-bottom:1px solid rgba(32,255,59,.12)}}.form{{display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px;margin-bottom:14px}}input,select{{background:#020703;color:#fff;border:1px solid var(--line);border-radius:8px;padding:10px;min-width:0}}.widefield{{grid-column:span 2}}.wishrow{{padding:10px 0;border-bottom:1px solid rgba(32,255,59,.12);display:flex;gap:8px;align-items:center;flex-wrap:wrap}}.wishname{{font-weight:700;min-width:220px}}.empty{{color:var(--muted);padding:12px 0}}@media(max-width:900px){{section,section.wide{{grid-column:1/-1}}nav{{margin-left:0;overflow-x:auto;white-space:nowrap}}header{{flex-wrap:wrap}}.form{{grid-template-columns:1fr}}.widefield{{grid-column:auto}}}}
</style></head><body><header><h1>▣ {title}</h1><nav><a href="/">🏠 Home</a><a href="/gamescom">🎮 GamesCom</a><a href="/watchers">👁 Watchers</a><a class="active" href="/wishlist">❤️ Wishlist</a></nav></header><main>{body}</main></body></html>'''


def register(app):
    @app.get("/gamescom", response_class=HTMLResponse)
    def gamescom_page():
        g = _read("gamescom.json", {})
        events = g.get("events", []) if isinstance(g, dict) else []
        observations = _observations()
        hotels = [x for x in observations if x.get("type") == "gamescom_hotel_offer"]
        tickets = [x for x in observations if x.get("type") in {"gamescom_ticket_status", "gamescom_stock_alert"}]
        epix = [x for x in observations if "epix" in str(x.get("type", "")).lower() or "epix" in str(x.get("source", "")).lower()]
        announcements = [x for x in observations if "announcement" in str(x.get("type", "")).lower()]
        travel_state = _read("state/gamescom_travel_list.json", {})
        travel = travel_state.get("tasks", []) if isinstance(travel_state, dict) else []
        history = _read("state/hotel_history.json", [])
        if not isinstance(history, list): history = []
        rows = ''.join(f'<tr><td>{e.get("day", e.get("date", "—"))}</td><td>{e.get("stock", e.get("status", "—"))}</td><td><a href="{e.get("url", "#")}" target="_blank">Bron</a></td></tr>' for e in tickets[-30:])
        hotel_rows = ''.join(f'<tr><td>{h.get("product", "—")}</td><td>{h.get("price_per_night", "—")} {h.get("currency", "EUR")}</td><td>{h.get("total_price", "—")}</td><td>{h.get("availability", "—")}</td><td>{h.get("source", "—")}</td></tr>' for h in hotels[-50:])
        travel_html = ''.join(f'<div class="item"><b>{x.get("title", "Reispunt")}</b> <span class="pill">{"Klaar" if x.get("completed") else "Open"}</span><br><span class="muted">{x.get("day", "")} {x.get("location", "")} {x.get("note", "")}</span></div>' for x in travel[-50:]) or '<span class="muted">Geen travel-list data gevonden.</span>'
        event_html = ''.join(f'<div class="item"><b>{e.get("title", e.get("name", "GamesCom event"))}</b><br><span class="muted">{e.get("date", e.get("time", e.get("start", "")))}</span></div>' for e in events[-50:]) or '<span class="muted">Geen events beschikbaar.</span>'
        body = f'''<section class="wide"><h2>GamesCom 2026 overzicht</h2><div class="pill">Jaar: {g.get("year", "—")}</div><div class="pill">Status: {g.get("status", "—")}</div><p>Opening Night Live: <b>{g.get("opening_night_live", "—")}</b> <span class="pill">telt mee als live dag</span></p><p>Live dagen: <b>{g.get("counted_live_days", "—")}</b></p><p>Live periode: <b>{g.get("live_start", g.get("start", "—"))} → {g.get("end", "—")}</b></p><p><a href="{g.get("official_url", "https://www.gamescom.global/")}" target="_blank">Officiële GamesCom website →</a></p></section>
<section><h2>Travel List</h2>{travel_html}</section>
<section class="full"><h2>Hotel Watcher</h2><table><tr><th>Hotel</th><th>Per nacht</th><th>Totaal</th><th>Beschikbaarheid</th><th>Bron</th></tr>{hotel_rows or '<tr><td colspan="5">Geen hoteloffers beschikbaar</td></tr>'}</table><p class="muted">Historische hotelobservaties: {len(history)}</p></section>
<section class="wide"><h2>Ticket Watcher</h2><table><tr><th>Dag</th><th>Status</th><th>Bron</th></tr>{rows or '<tr><td colspan="3">Geen ticketdata</td></tr>'}</table></section>
<section><h2>EPIX</h2>{''.join(f'<div class="item">{x.get("product", x.get("title", "EPIX item"))}</div>' for x in epix[-30:]) or '<span class="muted">Geen EPIX data</span>'}</section>
<section><h2>Announcements</h2>{''.join(f'<div class="item">{x.get("title", x.get("message", "Announcement"))}</div>' for x in announcements[-30:]) or '<span class="muted">Geen aankondigingen</span>'}</section>
<section class="wide"><h2>GamesCom Events</h2>{event_html}</section>'''
        return _page("GamesCom Center", body)

    @app.get("/watchers", response_class=HTMLResponse)
    def watchers_page():
        state = _observations()
        groups = {"Games": ["SteamDB", "Steam", "PS Store", "Wishlist", "Game Price", "EPIX", "GamesCom Tickets"], "Hardware": ["Hardware", "GPU", "RAM", "CPU", "Tweakers", "Retailers"], "Discord": ["Discord Price", "Discord News", "Discord Alerts"], "GamesCom": ["Hotel Watcher", "Ticket Watcher", "Announcements", "EPIX", "Travel List"], "System": ["Monitoring Cycle", "Change Detection", "Price History", "Notifications", "Watcher Registry"]}
        cards = ''.join('<section><h2>'+k+'</h2>'+''.join(f'<div class="item"><b>{v}</b><br><span class="ok">● Watcher geregistreerd</span></div>' for v in vals)+'</section>' for k, vals in groups.items())
        recent = ''.join(f'<tr><td>{x.get("type", "—")}</td><td>{x.get("source", "—")}</td><td>{x.get("checked_at", "—")}</td><td>{x.get("error", "OK") or "OK"}</td></tr>' for x in state[-100:])
        body = cards + f'<section class="full"><h2>Watcher Observations</h2><table><tr><th>Type</th><th>Source</th><th>Checked</th><th>Status</th></tr>{recent or "<tr><td colspan=4>Geen observaties</td></tr>"}</table></section>'
        return _page("Watcher Center", body)

    @app.get("/wishlist", response_class=HTMLResponse)
    def wishlist_page():
        body = '''<section class="wide"><h2>❤️ Wishlist</h2>
<div class="form"><input id="title" class="widefield" placeholder="Naam, bijvoorbeeld GTA VI / RTX 5070 Ti / Arctis Nova 7"><select id="category"><option value="game">🎮 Game</option><option value="hardware">🖥️ Hardware</option><option value="gear">🎧 Gear</option></select><input id="platform" placeholder="Platform (optioneel)"><input id="url" class="widefield" placeholder="Link (optioneel)"><input id="notes" placeholder="Notitie (optioneel)"><button onclick="addWish()">＋ Toevoegen</button></div><div id="wishlist">Laden...</div></section>
<section class="full"><h2>💰 Live prijzen</h2><div id="prices">Laden...</div></section>
<script>
const get=async u=>(await fetch(u)).json();
function esc(s){return String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
const labels={game:'🎮 Game',hardware:'🖥️ Hardware',gear:'🎧 Gear'};
async function load(){const [w,p]=await Promise.all([get('/api/wishlist'),get('/api/prices')]);document.querySelector('#wishlist').innerHTML=w.length?w.map(x=>`<div class="wishrow"><span class="wishname">${esc(x.title)}</span><span class="pill">${labels[x.category]||'🎮 Game'}</span>${x.platform?`<span class="pill">${esc(x.platform)}</span>`:''}${x.notes?`<span class="muted">${esc(x.notes)}</span>`:''}${x.url?`<a href="${esc(x.url)}" target="_blank">Link</a>`:''}<button onclick='editWish(${JSON.stringify(x)})'>Bewerken</button><button onclick='deleteWish("${esc(x.id)}")'>Verwijderen</button></div>`).join(''):'<div class="empty">Wishlist is leeg.</div>';document.querySelector('#prices').innerHTML=p.length?'<table><tr><th>Product</th><th>Platform</th><th>Prijs</th><th>Stock</th><th>Bron</th></tr>'+p.map(x=>`<tr><td>${esc(x.product)}</td><td>${esc(x.platform)}</td><td>${esc(x.price)} ${esc(x.currency)}</td><td>${esc(x.stock)}</td><td>${x.url?`<a href="${esc(x.url)}" target="_blank">${esc(x.source)}</a>`:esc(x.source)}</td></tr>`).join('')+'</table>':'<div class="empty">Geen live prijsdata beschikbaar.</div>'}
function clearForm(){['title','platform','url','notes'].forEach(id=>document.querySelector('#'+id).value='');document.querySelector('#category').value='game'}
async function addWish(){const title=document.querySelector('#title').value.trim();if(!title)return alert('Vul een naam in.');const item={id:crypto.randomUUID(),title,category:document.querySelector('#category').value,platform:document.querySelector('#platform').value.trim()||null,app_id:null,url:document.querySelector('#url').value.trim()||null,notes:document.querySelector('#notes').value.trim()||null};const r=await fetch('/api/wishlist',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(item)});if(r.ok){clearForm();load()}else alert((await r.json()).detail||'Wishlist toevoegen mislukt')}
async function editWish(x){const title=prompt('Naam',x.title);if(!title)return;const category=prompt('Categorie: game, hardware of gear',x.category)||x.category;const platform=prompt('Platform (optioneel)',x.platform||'');await fetch('/api/wishlist/'+encodeURIComponent(x.id),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({...x,title,category,platform:platform||null})});load()}
async function deleteWish(id){if(!confirm('Wishlist item verwijderen?'))return;await fetch('/api/wishlist/'+encodeURIComponent(id),{method:'DELETE'});load()}
load();setInterval(load,30000);
</script>'''
        return _page("Wishlist & Live Prijzen", body)
