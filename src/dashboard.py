from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ollama_web import OllamaClient, WebContext
from web_sources import DEFAULT_SOURCES

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="Personal Gaming Assistant Dashboard")


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
    title: str = Field(min_length=1)
    category: Literal["game", "hardware", "gear"] = "game"
    platform: str | None = None
    app_id: int | None = None
    url: str | None = None
    notes: str | None = None


class AIRequest(BaseModel):
    question: str
    sources: list[str] | None = None


def normalize_wishlist_item(item: dict) -> dict:
    # Keep existing wishlist entries working after the schema expansion.
    category = item.get("category") or ("game" if item.get("platform") else "hardware")
    if category not in {"game", "hardware", "gear"}:
        category = "game"
    item["category"] = category
    item.setdefault("platform", None)
    item.setdefault("app_id", None)
    item.setdefault("url", None)
    item.setdefault("notes", None)
    return item


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
    return [normalize_wishlist_item(x) for x in read_json("wishlist.json", [])]


@app.post("/api/wishlist")
def create_wishlist(item: WishlistItem):
    items = [normalize_wishlist_item(x) for x in read_json("wishlist.json", [])]
    if any(x.get("id") == item.id for x in items):
        raise HTTPException(409, "Wishlist item already exists")
    value = item.model_dump()
    items.append(value)
    write_json("wishlist.json", items)
    return value


@app.put("/api/wishlist/{item_id}")
def edit_wishlist(item_id: str, item: WishlistItem):
    items = [normalize_wishlist_item(x) for x in read_json("wishlist.json", [])]
    for index, existing in enumerate(items):
        if existing.get("id") == item_id:
            value = item.model_dump()
            value["id"] = item_id
            items[index] = value
            write_json("wishlist.json", items)
            return value
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
    return read_json("steam_profile.json", {"profile_url": None, "display_name": None, "level": None, "games": [], "total_spend_eur": None, "total_spend_uah": None, "last_synced": None})


@app.get("/api/gamescom")
def gamescom():
    return read_json("gamescom.json", {"year": None, "status": "not_configured", "start": None, "end": None, "countdown_target": None, "events": [], "last_synced": None})


@app.post("/api/update")
def manual_update():
    stamp = datetime.now(ZoneInfo("Europe/Amsterdam")).isoformat()
    updates = read_json("updates.json", [])
    updates.append({"timestamp": stamp, "type": "manual", "status": "requested"})
    write_json("updates.json", updates[-100:])
    return {"status": "requested", "timestamp": stamp}


@app.post("/api/ai")
def ai(request: AIRequest):
    urls = request.sources or DEFAULT_SOURCES
    web = WebContext()
    ollama = OllamaClient()
    try:
        sources = web.fetch(urls)
        answer = ollama.chat_with_web_context(request.question, sources)
        return {"answer": answer, "sources": [s.url for s in sources]}
    finally:
        web.close()
        ollama.close()


HTML = r'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Personal Gaming Assistant</title>
<style>
:root{--g:#20ff3b;--bg:#020503;--card:rgba(3,12,5,.88);--line:rgba(32,255,59,.28);--muted:#8aa58d}*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:#e9f8ea;font-family:Inter,system-ui,sans-serif}body{overflow-x:hidden}.matrix{position:fixed;inset:0;z-index:-2;background:#000}.matrix canvas{width:100%;height:100%;display:block}.veil{position:fixed;inset:0;z-index:-1;background:radial-gradient(circle at 50% 20%,rgba(0,40,5,.25),rgba(0,0,0,.78) 70%)}header{position:sticky;top:0;z-index:5;background:rgba(0,5,1,.9);backdrop-filter:blur(12px);border-bottom:1px solid var(--line);padding:14px 22px;display:flex;align-items:center;gap:18px}.logo{font-weight:800;color:var(--g);letter-spacing:.4px}.sub{font-size:12px;color:var(--muted)}button{background:#061608;color:var(--g);border:1px solid var(--line);border-radius:8px;padding:9px 13px;cursor:pointer}button:hover{background:#0a2810;box-shadow:0 0 14px rgba(32,255,59,.15)}.manual{margin-left:auto}main{max-width:1600px;margin:auto;padding:22px;display:grid;grid-template-columns:repeat(12,1fr);gap:16px}.card{grid-column:span 4;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:0 0 28px rgba(0,255,40,.06),inset 0 0 24px rgba(0,255,40,.025);backdrop-filter:blur(5px)}.wide{grid-column:span 8}.full{grid-column:1/-1}.card h2{margin:0 0 12px;color:var(--g);font-size:15px;text-transform:uppercase;letter-spacing:.8px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:9px 7px;text-align:left;border-bottom:1px solid rgba(32,255,59,.12)}a{color:var(--g)}.pill{display:inline-block;border:1px solid var(--line);padding:4px 8px;border-radius:999px;color:var(--g);font-size:11px}.form{display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px;margin-bottom:12px}.form input,.form select{background:#020703;color:#fff;border:1px solid var(--line);border-radius:8px;padding:10px}.form .widefield{grid-column:span 2}.wishrow{padding:9px 0;border-bottom:1px solid rgba(32,255,59,.12);display:flex;align-items:center;gap:8px;flex-wrap:wrap}.wishname{font-weight:700;min-width:180px}.ai{min-height:220px}.airow{display:flex;gap:8px}.airow input{flex:1;background:#020703;color:#fff;border:1px solid var(--line);border-radius:8px;padding:11px}.answer{white-space:pre-wrap;margin-top:12px;color:#d5efd7;max-height:280px;overflow:auto}.sources{font-size:11px;color:var(--muted);margin-top:10px}.count{font-size:42px;color:var(--g);font-weight:800;text-shadow:0 0 20px rgba(32,255,59,.35)}@media(max-width:900px){.card,.wide{grid-column:1/-1}.form{grid-template-columns:1fr}.form .widefield{grid-column:auto}}
</style></head><body><div class="matrix"><canvas id="rain"></canvas></div><div class="veil"></div>
<header><div><div class="logo">▣ PERSONAL GAMING ASSISTANT</div><div class="sub">VPS DASHBOARD · OLLAMA + LIVE WEB SOURCES</div></div><span id="clock" class="pill"></span><button class="manual" onclick="manualUpdate()">↻ Manual Update</button></header>
<main>
<section class="card wide"><h2>Laatste 6 updates</h2><div id="updates">Laden...</div></section>
<section class="card"><h2>Steam profiel</h2><div id="steam">Laden...</div></section>
<section class="card"><h2>GamesCom</h2><div id="gamescom">Laden...</div></section>
<section class="card full"><h2>Live prijzen data</h2><div id="prices">Laden...</div></section>
<section class="card wide"><h2>Wishlist</h2><div class="form"><input id="wishTitle" class="widefield" placeholder="Naam, bijvoorbeeld RTX 5070 Ti / GTA VI / Arctis Nova 7"><select id="wishCategory"><option value="game">🎮 Game</option><option value="hardware">🖥️ Hardware</option><option value="gear">🎧 Gear</option></select><input id="wishPlatform" placeholder="Platform (optioneel)"><input id="wishUrl" class="widefield" placeholder="Link (optioneel)"><input id="wishNotes" placeholder="Notitie (optioneel)"><button onclick="addWish()">＋ Toevoegen</button></div><div id="wishlist">Laden...</div></section>
<section class="card ai"><h2>Ollama AI · Web Research</h2><div class="sub">Ollama draait lokaal. De app haalt eerst live informatie van meerdere bronnen en geeft die context door aan het model.</div><div class="airow" style="margin-top:12px"><input id="q" placeholder="Vraag iets over games, prijzen, hardware…" onkeydown="if(event.key==='Enter')askAI()"><button onclick="askAI()">➤</button></div><div id="answer" class="answer"></div><div id="sources" class="sources"></div></section>
<section class="card"><h2>Bronnen</h2><div class="pill">SteamDB</div> <div class="pill">Steam</div> <div class="pill">PS Store</div> <div class="pill">Tweakers</div> <div class="pill">bol.com</div> <div class="pill">Azerty</div> <div class="pill">Alternate</div> <div class="pill">Megekko</div> <div class="pill">Amazon.nl</div> <div class="pill">G2G</div> <div class="pill">GamesCom</div></section>
</main>
<script>
const get=async u=>(await fetch(u)).json();function esc(s){return String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
const catLabel={game:'🎮 Game',hardware:'🖥️ Hardware',gear:'🎧 Gear'};
function tick(){document.querySelector('#clock').textContent=new Intl.DateTimeFormat('nl-NL',{dateStyle:'medium',timeStyle:'medium',timeZone:'Europe/Amsterdam'}).format(new Date())}setInterval(tick,1000);tick();
async function load(){let [u,p,w,s,g]=await Promise.all([get('/api/updates'),get('/api/prices'),get('/api/wishlist'),get('/api/steam/profile'),get('/api/gamescom')]);document.querySelector('#updates').innerHTML=u.length?'<table><tr><th>Tijd</th><th>Type</th><th>Status</th></tr>'+u.map(x=>`<tr><td>${esc(x.timestamp)}</td><td>${esc(x.type)}</td><td>${esc(x.status)}</td></tr>`).join('')+'</table>':'Geen updates';document.querySelector('#prices').innerHTML=p.length?'<table><tr><th>Product</th><th>Platform</th><th>Prijs</th><th>Stock</th><th>Bron</th></tr>'+p.map(x=>`<tr><td>${esc(x.product)}</td><td>${esc(x.platform)}</td><td>${esc(x.price)} ${esc(x.currency)}</td><td>${esc(x.stock)}</td><td>${x.url?`<a href="${esc(x.url)}" target="_blank">${esc(x.source)}</a>`:esc(x.source)}</td></tr>`).join('')+'</table>':'Geen live prijsdata';document.querySelector('#wishlist').innerHTML=w.length?w.map(x=>`<div class="wishrow"><span class="wishname">${esc(x.title)}</span><span class="pill">${catLabel[x.category]||'🎮 Game'}</span>${x.platform?`<span class="pill">${esc(x.platform)}</span>`:''}<button onclick='editWish(${JSON.stringify(x)})'>Bewerken</button><button onclick='deleteWish("${esc(x.id)}")'>Verwijderen</button></div>`).join(''):'Wishlist is leeg';document.querySelector('#steam').innerHTML=`<b>${esc(s.display_name||'Niet gekoppeld')}</b><br>Level: ${esc(s.level??'—')}<br>Games: ${s.games?.length??0}<br>Uitgaven EUR: ${esc(s.total_spend_eur??'—')}<br>Uitgaven UAH: ${esc(s.total_spend_uah??'—')}`;document.querySelector('#gamescom').innerHTML=`<b>${esc(g.year??'—')}</b><br>Status: ${esc(g.status)}<br><div class="count">${esc(g.countdown_target??'—')}</div><small>${esc(g.start??'')} → ${esc(g.end??'')}</small>`}
function clearWishForm(){for(const id of ['wishTitle','wishPlatform','wishUrl','wishNotes'])document.querySelector('#'+id).value='';document.querySelector('#wishCategory').value='game'}
async function addWish(){const title=document.querySelector('#wishTitle').value.trim();if(!title)return;const body={id:crypto.randomUUID(),title,category:document.querySelector('#wishCategory').value,platform:document.querySelector('#wishPlatform').value.trim()||null,app_id:null,url:document.querySelector('#wishUrl').value.trim()||null,notes:document.querySelector('#wishNotes').value.trim()||null};await fetch('/api/wishlist',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});clearWishForm();load()}
async function editWish(x){const title=prompt('Naam',x.title);if(!title)return;const category=prompt('Categorie: game, hardware of gear',x.category)||x.category;const platform=prompt('Platform (optioneel)',x.platform||'');await fetch('/api/wishlist/'+encodeURIComponent(x.id),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({...x,title,category,platform:platform||null})});load()}
async function deleteWish(id){if(!confirm('Verwijderen?'))return;await fetch('/api/wishlist/'+encodeURIComponent(id),{method:'DELETE'});load()}
async function manualUpdate(){await fetch('/api/update',{method:'POST'});load()}
async function askAI(){const q=document.querySelector('#q').value.trim();if(!q)return;document.querySelector('#answer').textContent='Webbronnen ophalen…';document.querySelector('#sources').textContent='';const r=await fetch('/api/ai',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});const d=await r.json();document.querySelector('#answer').textContent=d.answer||'Geen antwoord';document.querySelector('#sources').textContent='Bronnen: '+(d.sources||[]).join(' · ')}load();setInterval(load,60000);
const c=document.querySelector('#rain'),x=c.getContext('2d'),chars='アカサタナハマヤラワ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<>[]{}+-*/';let drops=[];function resize(){c.width=innerWidth*devicePixelRatio;c.height=innerHeight*devicePixelRatio;x.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);drops=Array(Math.ceil(innerWidth/18)).fill(0).map(()=>Math.random()*innerHeight/18)}addEventListener('resize',resize);resize();function rain(){x.fillStyle='rgba(0,0,0,.10)';x.fillRect(0,0,innerWidth,innerHeight);x.font='14px monospace';for(let i=0;i<drops.length;i++){let ch=chars[Math.floor(Math.random()*chars.length)],y=drops[i]*18;x.fillStyle=Math.random()>.96?'#baffc0':'#0bd42b';x.fillText(ch,i*18,y);if(y>innerHeight&&Math.random()>.975)drops[i]=0;else drops[i]+=.55}requestAnimationFrame(rain)}rain();
</script></body></html>'''


@app.get('/', response_class=HTMLResponse)
def dashboard():
    return HTML
