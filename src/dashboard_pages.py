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


def _page(title: str, body: str) -> str:
    return f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Personal Gaming Assistant</title><style>
:root{{--g:#20ff3b;--bg:#020503;--card:rgba(3,12,5,.9);--line:rgba(32,255,59,.28);--muted:#8aa58d}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:#e9f8ea;font-family:Inter,system-ui,sans-serif}}header{{position:sticky;top:0;z-index:2;background:rgba(0,5,1,.95);border-bottom:1px solid var(--line);padding:16px 22px;display:flex;gap:10px;align-items:center}}header h1{{margin:0;color:var(--g);font-size:20px}}nav{{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}}nav a,button{{color:var(--g);background:#061608;border:1px solid var(--line);border-radius:8px;padding:9px 12px;text-decoration:none;cursor:pointer}}main{{max-width:1600px;margin:auto;padding:22px;display:grid;grid-template-columns:repeat(12,1fr);gap:16px}}section{{grid-column:span 4;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:0 0 25px rgba(0,255,40,.05)}}section.wide{{grid-column:span 8}}section.full{{grid-column:1/-1}}h2{{margin:0 0 12px;color:var(--g);font-size:15px;text-transform:uppercase}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:8px;border-bottom:1px solid rgba(32,255,59,.12);text-align:left}}.pill{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 8px;margin:2px;color:var(--g);font-size:11px}}.ok{{color:var(--g)}}.muted{{color:var(--muted)}}.item{{padding:10px 0;border-bottom:1px solid rgba(32,255,59,.12)}}@media(max-width:900px){{section,section.wide{{grid-column:1/-1}}nav{{margin-left:0}}header{{flex-wrap:wrap}}}}
</style></head><body><header><h1>▣ {title}</h1><nav><a href="/">Dashboard</a><a href="/gamescom">🎮 GamesCom</a><a href="/watchers">👁 Watchers</a></nav></header><main>{body}</main></body></html>'''


def register(app):
    @app.get("/gamescom", response_class=HTMLResponse)
    def gamescom_page():
        g = _read("gamescom.json", {})
        events = g.get("events", []) if isinstance(g, dict) else []
        hotel = _read("watcher_state.json", [])
        if not isinstance(hotel, list): hotel = []
        hotels = [x for x in hotel if x.get("type") == "gamescom_hotel_offer"]
        tickets = [x for x in hotel if x.get("type") == "gamescom_ticket_status"]
        epix = [x for x in hotel if "epix" in str(x.get("type", "")).lower()]
        announcements = [x for x in hotel if "announcement" in str(x.get("type", "")).lower()]
        travel = _read("travel_list.json", [])
        if not isinstance(travel, list): travel = []
        history = _read("hotel_history.json", [])
        if not isinstance(history, list): history = []
        rows = ''.join(f'<tr><td>{e.get("day", e.get("date", "—"))}</td><td>{e.get("stock", e.get("status", "—"))}</td><td><a href="{e.get("url", "#")}" target="_blank">Bron</a></td></tr>' for e in tickets[-30:])
        hotel_rows = ''.join(f'<tr><td>{h.get("product", "—")}</td><td>{h.get("price_per_night", "—")} {h.get("currency", "EUR")}</td><td>{h.get("total_price", "—")}</td><td>{h.get("availability", "—")}</td><td>{h.get("source", "—")}</td></tr>' for h in hotels[-50:])
        travel_html = ''.join(f'<div class="item"><b>{x.get("title", x.get("name", "Reispunt"))}</b><br><span class="muted">{x.get("date", x.get("description", ""))}</span></div>' for x in travel[-50:]) or '<span class="muted">Geen travel-list data gevonden.</span>'
        event_html = ''.join(f'<div class="item"><b>{e.get("title", e.get("name", "GamesCom event"))}</b><br><span class="muted">{e.get("date", e.get("time", ""))}</span></div>' for e in events[-50:]) or '<span class="muted">Geen events beschikbaar.</span>'
        body = f'''<section class="wide"><h2>GamesCom 2026 overzicht</h2><div class="pill">Jaar: {g.get("year", "—")}</div><div class="pill">Status: {g.get("status", "—")}</div><p>Opening Night Live: <b>{g.get("opening_night_live", g.get("opening_night", "—"))}</b></p><p>Live dagen: <b>{g.get("live_days", g.get("days", "—"))}</b></p><p>Periode: <b>{g.get("start", "—")} → {g.get("end", "—")}</b></p></section>
<section><h2>Travel List</h2>{travel_html}</section>
<section class="full"><h2>Hotel Watcher</h2><table><tr><th>Hotel</th><th>Per nacht</th><th>Totaal</th><th>Beschikbaarheid</th><th>Bron</th></tr>{hotel_rows or '<tr><td colspan="5">Geen hoteloffers beschikbaar</td></tr>'}</table><p class="muted">Historische hotelobservaties: {len(history)}</p></section>
<section class="wide"><h2>Ticket Watcher</h2><table><tr><th>Dag</th><th>Status</th><th>Bron</th></tr>{rows or '<tr><td colspan="3">Geen ticketdata</td></tr>'}</table></section>
<section><h2>EPIX</h2>{''.join(f'<div class="item">{x.get("product", x.get("title", "EPIX item"))}</div>' for x in epix[-30:]) or '<span class="muted">Geen EPIX data</span>'}</section>
<section><h2>Announcements</h2>{''.join(f'<div class="item">{x.get("title", x.get("message", "Announcement"))}</div>' for x in announcements[-30:]) or '<span class="muted">Geen aankondigingen</span>'}</section>
<section class="wide"><h2>GamesCom Events</h2>{event_html}</section>'''
        return _page("GamesCom Center", body)

    @app.get("/watchers", response_class=HTMLResponse)
    def watchers_page():
        state = _read("watcher_state.json", [])
        if not isinstance(state, list): state = []
        groups = {
            "Games": ["SteamDB", "Steam", "PS Store", "Wishlist", "EPIX", "GamesCom Tickets"],
            "Hardware": ["Hardware", "GPU", "RAM", "Tweakers", "Retailers"],
            "Discord": ["Discord Price", "Discord News"],
            "GamesCom": ["Hotel", "Tickets", "Announcements", "EPIX", "Travel"],
            "System": ["Monitoring Cycle", "Change Detection", "Price History", "Notifications"],
        }
        cards = ''.join('<section><h2>'+k+'</h2>'+''.join(f'<div class="item"><b>{v}</b><br><span class="ok">● Watcher geregistreerd</span></div>' for v in vals)+'</section>' for k, vals in groups.items())
        recent = ''.join(f'<tr><td>{x.get("type", "—")}</td><td>{x.get("source", "—")}</td><td>{x.get("checked_at", "—")}</td><td>{x.get("error", "OK") or "OK"}</td></tr>' for x in state[-100:])
        body = cards + f'<section class="full"><h2>Watcher Observations</h2><table><tr><th>Type</th><th>Source</th><th>Checked</th><th>Status</th></tr>{recent or "<tr><td colspan=4>Geen observaties</td></tr>"}</table></section>'
        return _page("Watcher Center", body)
