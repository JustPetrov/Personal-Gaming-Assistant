from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROFILES = DATA / "steam_profiles.json"


class ProfileRequest(BaseModel):
    url: str = Field(min_length=10)
    name: str | None = None


def _read_profiles() -> list[dict]:
    try:
        value = json.loads(PROFILES.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_profiles(value: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    PROFILES.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _steam_id(url: str, client: httpx.Client, api_key: str) -> str:
    match = re.search(r"/profiles/(\d{17})(?:/|$)", url)
    if match:
        return match.group(1)
    match = re.search(r"/id/([^/?#]+)", url)
    if match:
        response = client.get("https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/", params={"key": api_key, "vanityurl": match.group(1)})
        response.raise_for_status()
        data = response.json().get("response", {})
        if data.get("success") == 1:
            return str(data["steamid"])
    raise ValueError("Steam profiel-URL moet /profiles/STEAMID64 of /id/gebruikersnaam bevatten")


def fetch_profile(profile: dict) -> dict:
    api_key = __import__("os").getenv("STEAM_API_KEY")
    if not api_key:
        raise RuntimeError("STEAM_API_KEY ontbreekt op de VPS")
    url = profile["url"]
    with httpx.Client(timeout=25, headers={"User-Agent": "Personal-Gaming-Assistant/1.0"}) as client:
        steam_id = _steam_id(url, client, api_key)
        summary = client.get("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/", params={"key": api_key, "steamids": steam_id}).json().get("response", {}).get("players", [])
        player = summary[0] if summary else {}
        level_data = client.get("https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/", params={"key": api_key, "steamid": steam_id}).json().get("response", {})
        games = client.get("https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/", params={"key": api_key, "steamid": steam_id, "include_appinfo": 1, "include_played_free_games": 1, "format": "json"}).json().get("response", {}).get("games", [])
        games = sorted(games, key=lambda x: x.get("playtime_forever", 0), reverse=True)
        recent = sorted([g for g in games if g.get("rtime_last_played")], key=lambda x: x.get("rtime_last_played", 0), reverse=True)[:10]
        wishlist: list[dict] = []
        try:
            raw = client.get(f"https://store.steampowered.com/wishlist/profiles/{steam_id}/wishlistdata/", timeout=20)
            if raw.is_success:
                payload = raw.json()
                for app_id, item in payload.items() if isinstance(payload, dict) else []:
                    wishlist.append({"app_id": app_id, "title": item.get("name"), "price": item.get("price", {}).get("final_formatted") if isinstance(item.get("price"), dict) else None, "url": f"https://store.steampowered.com/app/{app_id}/"})
        except Exception:
            pass
        return {
            "id": steam_id,
            "name": profile.get("name") or player.get("personaname") or steam_id,
            "profile_url": player.get("profileurl", url),
            "avatar": player.get("avatarfull"),
            "level": level_data.get("player_level"),
            "game_count": len(games),
            "played_hours": round(sum(g.get("playtime_forever", 0) for g in games) / 60, 1),
            "recent_games": [{"name": g.get("name"), "hours": round(g.get("playtime_forever", 0) / 60, 1), "last_played": datetime.fromtimestamp(g["rtime_last_played"], timezone.utc).isoformat()} for g in recent],
            "wishlist": wishlist[:50],
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }


def _page(body: str) -> str:
    return f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Steam Stats · Personal Gaming Assistant</title><style>
:root{{--g:#20ff3b;--bg:#020503;--card:rgba(3,12,5,.94);--line:rgba(32,255,59,.28);--muted:#8aa58d}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:#e9f8ea;font-family:Inter,system-ui,sans-serif}}header{{position:sticky;top:0;z-index:5;background:rgba(0,5,1,.97);border-bottom:1px solid var(--line);padding:14px 18px;display:flex;gap:18px;align-items:center}}header h1{{margin:0;color:var(--g);font-size:20px}}nav{{margin-left:auto;display:flex;gap:7px;overflow-x:auto;white-space:nowrap}}nav a,button{{color:var(--g);background:#061608;border:1px solid var(--line);border-radius:8px;padding:9px 12px;text-decoration:none;cursor:pointer}}nav a:hover,nav a.active,button:hover{{background:#0b2b10}}main{{max-width:1600px;margin:auto;padding:22px;display:grid;grid-template-columns:repeat(12,1fr);gap:16px}}section{{grid-column:span 4;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:0 0 25px rgba(0,255,40,.05)}}section.wide{{grid-column:span 8}}section.full{{grid-column:1/-1}}h2{{margin:0 0 12px;color:var(--g);font-size:15px;text-transform:uppercase}}input{{background:#020703;color:#fff;border:1px solid var(--line);border-radius:8px;padding:10px;width:100%;margin-bottom:8px}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:8px;border-bottom:1px solid rgba(32,255,59,.12);text-align:left}}a{{color:var(--g)}}.pill{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 8px;margin:2px;color:var(--g);font-size:11px}}.profile{{border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:16px}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0}}.stat{{background:#061608;border-radius:8px;padding:12px;text-align:center}}.stat b{{display:block;color:var(--g);font-size:22px}}.avatar{{width:64px;height:64px;border-radius:8px;float:left;margin-right:12px}}.muted{{color:var(--muted);font-size:12px}}.error{{color:#ff7777}}@media(max-width:900px){{section,section.wide{{grid-column:1/-1}}.stats{{grid-template-columns:repeat(2,1fr)}}nav{{margin-left:0}}header{{flex-wrap:wrap}}}}
</style></head><body><header><h1>🎮 Steam Stats</h1><nav><a href="/">🏠 Home</a><a href="/gamescom">🎮 GamesCom</a><a href="/watchers">👁 Watchers</a><a href="/wishlist">❤️ Wishlist</a><a href="/calendar">📅 Calendar</a><a class="active" href="/steam-stats">🎮 Steam Stats</a></nav></header><main>{body}</main></body></html>'''


def register(app):
    @app.get("/api/steam-profiles")
    def api_profiles():
        return _read_profiles()

    @app.post("/api/steam-profiles")
    def api_add_profile(request: ProfileRequest):
        profiles = _read_profiles()
        if not ("steamcommunity.com/" in request.url or "steamcommunity.com" in request.url):
            raise HTTPException(400, "Gebruik een Steam Community profiel-link")
        if any(x.get("url") == request.url for x in profiles):
            return {"added": False, "profiles": profiles}
        item = {"url": request.url, "name": request.name}
        profiles.append(item)
        _write_profiles(profiles)
        return {"added": True, "profiles": profiles}

    @app.delete("/api/steam-profiles/{index}")
    def api_delete_profile(index: int):
        profiles = _read_profiles()
        if index < 0 or index >= len(profiles):
            raise HTTPException(404, "Profiel niet gevonden")
        profiles.pop(index)
        _write_profiles(profiles)
        return profiles

    @app.get("/api/steam-stats")
    def api_stats():
        result = []
        for profile in _read_profiles():
            try:
                result.append({"ok": True, "profile": fetch_profile(profile)})
            except Exception as exc:
                result.append({"ok": False, "profile": profile, "error": str(exc)})
        return result

    @app.get("/steam-stats", response_class=HTMLResponse)
    def steam_stats_page():
        body = '''<section class="wide"><h2>Steam profielen</h2><p class="muted">Voeg meerdere openbare Steam-profielen toe. Per profiel worden level, games, totale speeltijd, recente games en de openbare wishlist opgehaald.</p><input id="url" placeholder="https://steamcommunity.com/profiles/765611... of https://steamcommunity.com/id/gebruikersnaam"><input id="name" placeholder="Naam/label (optioneel)"><button onclick="addProfile()">＋ Profiel toevoegen</button><button onclick="loadStats()">↻ Vernieuwen</button><div id="profiles" style="margin-top:14px"></div></section><section class="full"><h2>Steam statistieken</h2><div id="stats">Laden...</div></section>
<script>
const get=async u=>(await fetch(u)).json();function esc(s){return String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
async function loadProfiles(){const p=await get('/api/steam-profiles');document.querySelector('#profiles').innerHTML=p.length?p.map((x,i)=>`<span class="pill">${esc(x.name||x.url)} <button onclick="delProfile(${i})">×</button></span>`).join(''):'<span class="muted">Nog geen profielen.</span>'}
async function addProfile(){const url=document.querySelector('#url').value.trim();if(!url)return alert('Plaats een Steam profiel-link.');const name=document.querySelector('#name').value.trim()||null;const r=await fetch('/api/steam-profiles',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,name})});const j=await r.json();if(!r.ok)return alert(j.detail||'Profiel toevoegen mislukt');document.querySelector('#url').value='';document.querySelector('#name').value='';loadProfiles();loadStats()}
async function delProfile(i){await fetch('/api/steam-profiles/'+i,{method:'DELETE'});loadProfiles();loadStats()}
async function loadStats(){const rows=await get('/api/steam-stats');const html=rows.map(r=>{if(!r.ok)return `<div class="profile"><b>${esc(r.profile.name||r.profile.url)}</b><div class="error">${esc(r.error)}</div></div>`;const p=r.profile;return `<div class="profile">${p.avatar?`<img class="avatar" src="${esc(p.avatar)}">`:''}<b style="font-size:20px">${esc(p.name)}</b><br><a href="${esc(p.profile_url)}" target="_blank">Steam profiel →</a><div style="clear:both"></div><div class="stats"><div class="stat"><b>${p.level??'—'}</b>Level</div><div class="stat"><b>${p.game_count}</b>Games</div><div class="stat"><b>${p.played_hours}</b>Uren gespeeld</div><div class="stat"><b>${p.wishlist.length}</b>Wishlist</div></div><h3>Recente games</h3>${p.recent_games.length?'<table><tr><th>Game</th><th>Uren</th><th>Laatst gespeeld</th></tr>'+p.recent_games.map(g=>`<tr><td>${esc(g.name)}</td><td>${g.hours}</td><td>${esc(g.last_played)}</td></tr>`).join('')+'</table>':'<div class="muted">Geen recente games of profiel is privé.</div>'}<h3>Wishlist</h3>${p.wishlist.length?'<table><tr><th>Game</th><th>Prijs</th><th></th></tr>'+p.wishlist.map(w=>`<tr><td>${esc(w.title)}</td><td>${esc(w.price||'—')}</td><td><a href="${esc(w.url)}" target="_blank">Steam</a></td></tr>`).join('')+'</table>':'<div class="muted">Geen openbare Steam-wishlist beschikbaar.</div>'}</div>`}).join('');document.querySelector('#stats').innerHTML=html||'<div class="muted">Voeg hierboven een profiel toe.</div>'}
loadProfiles();loadStats();setInterval(loadStats,300000)
</script>'''
        return _page(body)


__all__ = ["register"]
