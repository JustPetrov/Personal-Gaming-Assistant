from __future__ import annotations

import json
from pathlib import Path

from fastapi.responses import HTMLResponse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _read(name: str, default):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def register(app):
    @app.get("/watchers-live-prices", response_class=HTMLResponse)
    def watchers_live_prices():
        return HTMLResponse('''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Live prijzen · Personal Gaming Assistant</title><style>:root{--g:#20ff3b;--bg:#020503;--card:rgba(3,12,5,.94);--line:rgba(32,255,59,.28);--muted:#8aa58d}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#e9f8ea;font-family:Inter,system-ui,sans-serif}header{position:sticky;top:0;z-index:5;background:rgba(0,5,1,.97);border-bottom:1px solid var(--line);padding:14px 22px}h1,h2{color:var(--g)}h1{font-size:20px;margin:0 0 10px}nav{display:flex;gap:8px;flex-wrap:wrap}nav a{color:var(--g);background:#061608;border:1px solid var(--line);border-radius:8px;padding:9px 12px;text-decoration:none}main{max-width:1600px;margin:auto;padding:22px}section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:0 0 25px rgba(0,255,40,.05)}h2{margin-top:0;font-size:16px;text-transform:uppercase}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:10px 8px;text-align:left;border-bottom:1px solid rgba(32,255,59,.12)}a{color:var(--g)}.muted{color:var(--muted)}.price{color:var(--g);font-weight:800;font-size:17px}.stock{color:var(--g)}@media(max-width:700px){table{font-size:12px}th,td{padding:8px 4px}.optional{display:none}}</style></head><body><header><h1>▣ WATCHERS · LIVE PRIJZEN</h1><nav><a href="/">🏠 Home</a><a href="/gamescom">🎮 GamesCom</a><a href="/watchers">👁 Watchers</a><a href="/wishlist">❤️ Wishlist</a></nav></header><main><section><h2>Games · Live prijzen</h2><div id="prices" class="muted">Laden...</div></section></main><script>const esc=s=>String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');async function load(){try{const r=await fetch('/api/prices');const p=await r.json();const items=Array.isArray(p)?p:[];document.querySelector('#prices').innerHTML=items.length?'<table><tr><th>Product</th><th>Platform</th><th>Prijs</th><th>Stock</th><th class="optional">Bron</th></tr>'+items.map(x=>`<tr><td>${esc(x.product)}</td><td>${esc(x.platform)}</td><td class="price">${esc(x.price)} ${esc(x.currency||'EUR')}</td><td class="stock">${esc(x.stock||'—')}</td><td class="optional">${x.url?`<a href="${esc(x.url)}" target="_blank">${esc(x.source||'Bron')}</a>`:esc(x.source||'—')}</td></tr>`).join('')+'</table>':'Geen live prijsdata beschikbaar.'}catch(e){document.querySelector('#prices').innerHTML='<span class="muted">Live prijsdata tijdelijk niet beschikbaar.</span>'}}load();setInterval(load,30000);</script></body></html>''')
