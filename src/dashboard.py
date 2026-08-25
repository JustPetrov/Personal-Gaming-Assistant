from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import json
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "config.yaml"
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Personal Gaming Assistant Dashboard")


def load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def read_json(name: str, default: Any):
    path = DATA / name
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(name: str, value: Any):
    (DATA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


class WishlistItem(BaseModel):
    id: str
    title: str
    platform: str
    url: str | None = None
    notes: str | None = None


class SteamSettings(BaseModel):
    profile_url: str


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now(ZoneInfo("Europe/Amsterdam")).isoformat()}


@app.get("/api/updates")
def updates():
    return read_json("updates.json", [])[-6:][::-1]


@app.get("/api/prices")
def prices():
    return read_json("prices.json", [])


@app.get("/api/wishlist")
def wishlist():
    return read_json("wishlist.json", [])


@app.post("/api/wishlist")
def create_wishlist(item: WishlistItem):
    items = read_json("wishlist.json", [])
    if any(x.get("id") == item.id for x in items):
        raise HTTPException(409, "Wishlist item already exists")
    items.append(item.model_dump())
    write_json("wishlist.json", items)
    return item


@app.put("/api/wishlist/{item_id}")
def edit_wishlist(item_id: str, item: WishlistItem):
    items = read_json("wishlist.json", [])
    for index, existing in enumerate(items):
        if existing.get("id") == item_id:
            items[index] = item.model_dump()
            write_json("wishlist.json", items)
            return item
    raise HTTPException(404, "Wishlist item not found")


@app.delete("/api/wishlist/{item_id}")
def delete_wishlist(item_id: str):
    items = read_json("wishlist.json", [])
    new_items = [x for x in items if x.get("id") != item_id]
    if len(new_items) == len(items):
        raise HTTPException(404, "Wishlist item not found")
    write_json("wishlist.json", new_items)
    return {"deleted": item_id}


@app.get("/api/steam/profile")
def steam_profile():
    return read_json("steam_profile.json", {
        "profile_url": None,
        "display_name": None,
        "level": None,
        "games": [],
        "total_spend_eur": None,
        "total_spend_uah": None,
        "last_synced": None,
    })


@app.get("/api/gamescom")
def gamescom():
    return read_json("gamescom.json", {
        "year": None,
        "status": "not_configured",
        "start": None,
        "end": None,
        "countdown_target": None,
        "events": [],
        "last_synced": None,
    })


@app.post("/api/update")
def manual_update():
    # The scheduler/orchestrator can be called here once deployed.
    stamp = datetime.now(ZoneInfo("Europe/Amsterdam")).isoformat()
    updates = read_json("updates.json", [])
    updates.append({"timestamp": stamp, "type": "manual", "status": "requested"})
    write_json("updates.json", updates[-100:])
    return {"status": "requested", "timestamp": stamp}


HTML = """<!doctype html>
<html lang='nl'>
<head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Personal Gaming Assistant</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#0f1117;color:#eee}header{padding:22px 28px;background:#171a23;position:sticky;top:0}main{padding:24px;display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}.card{background:#181c26;border:1px solid #292f3d;border-radius:14px;padding:18px}.wide{grid-column:1/-1}button{padding:9px 13px;border:0;border-radius:8px;cursor:pointer}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:8px;border-bottom:1px solid #2b3040}small{color:#9ca3af}</style>
</head><body><header><h1>🎮 Personal Gaming Assistant</h1><button onclick='manualUpdate()'>🔄 Manual update</button> <span id='status'></span></header>
<main>
<section class='card wide'><h2>🕐 Laatste 6 updates</h2><div id='updates'>Laden...</div></section>
<section class='card'><h2>🎮 Steam profiel</h2><div id='steam'>Laden...</div></section>
<section class='card'><h2>🎟️ GamesCom</h2><div id='gamescom'>Laden...</div></section>
<section class='card wide'><h2>💰 Live prijzen</h2><div id='prices'>Laden...</div></section>
<section class='card wide'><h2>❤️ Wishlist</h2><p><button onclick='addWish()'>＋ Toevoegen</button></p><div id='wishlist'>Laden...</div></section>
</main><script>
const get=async u=>(await fetch(u)).json();
function esc(s){return String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')}
async function load(){
 let [u,p,w,s,g]=await Promise.all([get('/api/updates'),get('/api/prices'),get('/api/wishlist'),get('/api/steam/profile'),get('/api/gamescom')]);
 document.querySelector('#updates').innerHTML=u.length?'<table><tr><th>Tijd</th><th>Type</th><th>Status</th></tr>'+u.map(x=>`<tr><td>${esc(x.timestamp)}</td><td>${esc(x.type)}</td><td>${esc(x.status)}</td></tr>`).join('')+'</table>':'Geen updates';
 document.querySelector('#prices').innerHTML=p.length?'<table><tr><th>Product</th><th>Platform</th><th>Prijs</th><th>Stock</th><th>Bron</th></tr>'+p.map(x=>`<tr><td>${esc(x.product)}</td><td>${esc(x.platform)}</td><td>${esc(x.price)} ${esc(x.currency)}</td><td>${esc(x.stock)}</td><td>${x.url?`<a href='${esc(x.url)}' target='_blank'>${esc(x.source)}</a>`:esc(x.source)}</td></tr>`).join('')+'</table>':'Geen live prijsdata';
 document.querySelector('#wishlist').innerHTML=w.length?w.map(x=>`<div><b>${esc(x.title)}</b> · ${esc(x.platform)} <button onclick='editWish(${JSON.stringify(x)})'>Bewerken</button><button onclick='deleteWish("${esc(x.id)}")'>Verwijderen</button></div>`).join(''):'Wishlist is leeg';
 document.querySelector('#steam').innerHTML=`<b>${esc(s.display_name||'Niet gekoppeld')}</b><br>Level: ${esc(s.level??'—')}<br>Games: ${s.games?.length??0}<br>Uitgaven EUR: ${esc(s.total_spend_eur??'—')}<br>Uitgaven UAH: ${esc(s.total_spend_uah??'—')}<br><small>Laatste sync: ${esc(s.last_synced??'—')}</small>`;
 document.querySelector('#gamescom').innerHTML=`<b>${esc(g.year??'—')}</b><br>Status: ${esc(g.status)}<br>Volgende: ${esc(g.countdown_target??'—')}<br>Events: ${g.events?.length??0}`;
}
async function manualUpdate(){document.querySelector('#status').textContent='Update aangevraagd…';await fetch('/api/update',{method:'POST'});await load();document.querySelector('#status').textContent='Klaar';}
async function addWish(){let title=prompt('Titel');if(!title)return;let platform=prompt('Platform (Steam/PS5)')||'Steam';let id=crypto.randomUUID();await fetch('/api/wishlist',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,title,platform,url:null,notes:null})});load();}
async function editWish(x){let title=prompt('Titel',x.title);if(!title)return;await fetch('/api/wishlist/'+encodeURIComponent(x.id),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({...x,title})});load();}
async function deleteWish(id){if(!confirm('Verwijderen?'))return;await fetch('/api/wishlist/'+encodeURIComponent(id),{method:'DELETE'});load();}
load();setInterval(load,60000);
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTML
