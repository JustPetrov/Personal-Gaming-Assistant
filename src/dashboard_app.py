from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.responses import HTMLResponse

_MODULE_PATH = Path(__file__).with_name("dashboard.py")
_SPEC = importlib.util.spec_from_file_location("pga_dashboard_module", _MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load dashboard module from {_MODULE_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app

from dashboard_pages import register  # noqa: E402
register(app)
from calendar_page import register as register_calendar  # noqa: E402
register_calendar(app)

app.routes[:] = [
    route for route in app.routes
    if not (getattr(route, "path", None) == "/" and "GET" in getattr(route, "methods", set()))
]

@app.get("/", response_class=HTMLResponse)
def homepage():
    return HOMEPAGE


HOMEPAGE = r'''<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Personal Gaming Assistant</title>
<style>
:root{--g:#20ff3b;--bg:#020503;--card:rgba(3,12,5,.9);--line:rgba(32,255,59,.28);--muted:#8aa58d}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:#e9f8ea;font-family:Inter,system-ui,sans-serif}
body{overflow-x:hidden}.matrix{position:fixed;inset:0;z-index:-2;background:#000}.matrix canvas{width:100%;height:100%;display:block}
.veil{position:fixed;inset:0;z-index:-1;background:radial-gradient(circle at 50% 20%,rgba(0,40,5,.28),rgba(0,0,0,.8) 72%)}
.topbar{position:sticky;top:0;z-index:10;background:rgba(0,5,1,.94);border-bottom:1px solid var(--line);backdrop-filter:blur(12px);padding:10px 18px;display:flex;align-items:center;gap:18px}.brand{font-weight:900;color:var(--g);white-space:nowrap;letter-spacing:.5px}.tabs{display:flex;gap:7px;flex-wrap:wrap}.tabs a{color:#a9c8ad;text-decoration:none;background:#061608;border:1px solid rgba(32,255,59,.18);border-radius:8px;padding:8px 12px;font-size:13px}.tabs a:hover,.tabs a.active{color:var(--g);border-color:var(--line);background:#0a2810;box-shadow:0 0 12px rgba(32,255,59,.12)}
main{min-height:calc(100vh - 58px);max-width:1500px;margin:auto;padding:28px;display:grid;grid-template-columns:repeat(12,1fr);gap:18px;align-content:center}
.card{grid-column:span 4;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 0 30px rgba(0,255,40,.07),inset 0 0 25px rgba(0,255,59,.025);backdrop-filter:blur(7px)}
h1{grid-column:1/-1;text-align:center;color:var(--g);font-size:24px;letter-spacing:1px;margin:0 0 2px;text-shadow:0 0 18px rgba(32,255,59,.3)}
h2{margin:0 0 16px;color:var(--g);font-size:15px;text-transform:uppercase;letter-spacing:.8px}
.newsTitle{font-size:23px;font-weight:800;color:#fff;margin-bottom:10px}.newsSummary{font-size:15px;line-height:1.6;color:#d5efd7}.meta{font-size:11px;color:var(--muted);margin-top:15px}.meta a,a{color:var(--g)}
.countdown{text-align:center}.countValue{font-size:42px;font-weight:900;color:var(--g);text-shadow:0 0 24px rgba(32,255,59,.4);margin:18px 0}.countLabel{font-size:12px;color:var(--muted)}
.aiDesc{font-size:12px;color:var(--muted);line-height:1.5;margin-bottom:12px}.airow{display:flex;gap:8px}.airow input{min-width:0;flex:1;background:#020703;color:#fff;border:1px solid var(--line);border-radius:8px;padding:11px}.airow button{background:#061608;color:var(--g);border:1px solid var(--line);border-radius:8px;padding:10px 14px;cursor:pointer}.answer{white-space:pre-wrap;margin-top:13px;color:#d5efd7;max-height:310px;overflow:auto;line-height:1.5}.sources{font-size:10px;color:var(--muted);margin-top:10px;word-break:break-all}
@media(max-width:950px){.topbar{align-items:flex-start;flex-direction:column}.tabs{width:100%;overflow-x:auto;flex-wrap:nowrap;padding-bottom:2px}.tabs a{white-space:nowrap}main{align-content:start;padding:18px}.card{grid-column:1/-1}h1{margin-top:10px}}
</style>
</head>
<body>
<div class="matrix"><canvas id="rain"></canvas></div><div class="veil"></div>
<header class="topbar"><div class="brand">▣ PGA</div><nav class="tabs"><a class="active" href="/">🏠 Home</a><a href="/gamescom">🎮 GamesCom</a><a href="/watchers">👁 Watchers</a><a href="/wishlist">❤️ Wishlist</a><a href="/calendar">📅 Calendar</a></nav></header>
<main>
<h1>▣ PERSONAL GAMING ASSISTANT</h1>
<section class="card"><h2>📰 Laatste nieuwsupdate</h2><div id="news">Laden...</div></section>
<section class="card countdown"><h2>🎮 GamesCom Countdown</h2><div id="countdown">Laden...</div></section>
<section class="card"><h2>🤖 Ollama AI</h2><div class="aiDesc">Stel een vraag. Ollama gebruikt de ingestelde live webbronnen als context voor het antwoord.</div><div class="airow"><input id="q" placeholder="Vraag iets over games, hardware…" onkeydown="if(event.key==='Enter')askAI()"><button onclick="askAI()">➤</button></div><div id="answer" class="answer"></div><div id="sources" class="sources"></div></section>
</main>
<script>
const get=async u=>(await fetch(u)).json();
function esc(s){return String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
async function load(){
 const [n,g]=await Promise.all([get('/api/news'),get('/api/gamescom')]);
 document.querySelector('#news').innerHTML=`<div class="newsTitle">${esc(n.title||'Nog geen nieuwsupdate')}</div><div class="newsSummary">${esc(n.summary||'Geen samenvatting beschikbaar.')}</div><div class="meta">${esc(n.timestamp||'')}${n.source?' · '+esc(n.source):''}${n.url?` · <a href="${esc(n.url)}" target="_blank">Lees bron</a>`:''}</div>`;
 const target=g.countdown_target||g.start;
 document.querySelector('#countdown').dataset.target=target||'';
 renderCountdown();
}
function renderCountdown(){
 const el=document.querySelector('#countdown'), target=el.dataset.target;
 if(!target){el.innerHTML='<div class="countValue">—</div><div class="countLabel">Geen GamesCom datum ingesteld</div>';return}
 const diff=new Date(target).getTime()-Date.now();
 if(Number.isNaN(diff)){el.innerHTML='<div class="countValue">—</div><div class="countLabel">Ongeldige GamesCom datum</div>';return}
 if(diff<=0){el.innerHTML='<div class="countValue">LIVE</div><div class="countLabel">GamesCom is bezig</div>';return}
 const s=Math.floor(diff/1000),d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60),sec=s%60;
 el.innerHTML=`<div class="countValue">${d}d ${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}</div><div class="countLabel">tot GamesCom ${esc(target)}</div>`;
}
setInterval(renderCountdown,1000);
async function askAI(){
 const input=document.querySelector('#q'), q=input.value.trim(); if(!q)return;
 const answer=document.querySelector('#answer'); answer.textContent='Onderzoek en antwoord wordt opgebouwd…';
 document.querySelector('#sources').textContent='';
 try{const r=await fetch('/api/ai',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});const j=await r.json();answer.textContent=j.answer||j.detail||'Geen antwoord';document.querySelector('#sources').innerHTML=(j.sources||[]).map(x=>esc(x)).join('<br>')}catch(e){answer.textContent='AI-fout: '+e}
}
load();
const c=document.getElementById('rain'),ctx=c.getContext('2d');let w,h,cols,drops;
function resize(){w=c.width=innerWidth*devicePixelRatio;h=c.height=innerHeight*devicePixelRatio;c.style.width=innerWidth+'px';c.style.height=innerHeight+'px';ctx.font=(14*devicePixelRatio)+'px monospace';cols=Math.floor(w/(14*devicePixelRatio));drops=Array(cols).fill(0).map(()=>Math.random()*h/(14*devicePixelRatio))}
addEventListener('resize',resize);resize();function rain(){ctx.fillStyle='rgba(0,0,0,.08)';ctx.fillRect(0,0,w,h);ctx.fillStyle='#0f3';for(let i=0;i<cols;i++){ctx.fillText(Math.random()>.5?'1':'0',i*14*devicePixelRatio,drops[i]*14*devicePixelRatio);if(drops[i]*14*devicePixelRatio>h&&Math.random()>.975)drops[i]=0;drops[i]++}requestAnimationFrame(rain)}rain();
</script>
</body></html>'''

__all__ = ["app"]
