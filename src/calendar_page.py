from __future__ import annotations

from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from calendar_store import add_event, add_reminder, delete_event, delete_reminder, list_events, list_reminders
from notifications_api import router as notifications_router, send_push


class CalendarEventRequest(BaseModel):
    title: str = Field(min_length=1)
    event_type: str = "release"
    start: str
    end: str | None = None
    url: str | None = None
    notes: str | None = None
    source: str | None = None


class ReminderRequest(BaseModel):
    title: str = Field(min_length=1)
    remind_at: str
    event_id: str | None = None
    sound: bool = True


def _page(body: str) -> str:
    return f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Calendar · Personal Gaming Assistant</title><style>
:root{{--g:#20ff3b;--bg:#020503;--card:rgba(3,12,5,.94);--line:rgba(32,255,59,.28);--muted:#8aa58d}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:#e9f8ea;font-family:Inter,system-ui,sans-serif}}header{{position:sticky;top:0;z-index:5;background:rgba(0,5,1,.97);border-bottom:1px solid var(--line);padding:14px 18px;display:flex;gap:18px;align-items:center}}header h1{{margin:0;color:var(--g);font-size:20px}}nav{{margin-left:auto;display:flex;gap:7px;overflow-x:auto;white-space:nowrap}}nav a{{color:#a9c8ad;text-decoration:none;background:#061608;border:1px solid rgba(32,255,59,.18);border-radius:8px;padding:8px 11px;font-size:13px}}nav a:hover,nav a.active{{color:var(--g);border-color:var(--line);background:#0b2b10}}main{{max-width:1500px;margin:auto;padding:22px;display:grid;grid-template-columns:repeat(12,1fr);gap:16px}}section{{grid-column:span 6;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;box-shadow:0 0 24px rgba(0,255,40,.05)}}section.full{{grid-column:1/-1}}h2{{margin:0 0 12px;color:var(--g);font-size:15px;text-transform:uppercase}}.form{{display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px}}input,select,textarea{{background:#020703;color:#fff;border:1px solid var(--line);border-radius:8px;padding:10px;min-width:0}}textarea{{min-height:80px;resize:vertical}}button{{background:#061608;color:var(--g);border:1px solid var(--line);border-radius:8px;padding:10px 12px;cursor:pointer}}.wide{{grid-column:span 2}}.event,.reminder{{padding:12px 0;border-bottom:1px solid rgba(32,255,59,.12)}}.muted{{color:var(--muted);font-size:12px}}.pill{{display:inline-block;padding:4px 8px;border:1px solid var(--line);border-radius:999px;color:var(--g);font-size:11px;margin:2px}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:8px;border-bottom:1px solid rgba(32,255,59,.12);text-align:left}}a{{color:var(--g)}}@media(max-width:900px){{section{{grid-column:1/-1}}.form{{grid-template-columns:1fr}}.wide{{grid-column:auto}}}}
</style></head><body><header><h1>📅 Calendar</h1><nav><a href="/">🏠 Home</a><a href="/gamescom">🎮 GamesCom</a><a href="/watchers">👁 Watchers</a><a href="/wishlist">❤️ Wishlist</a><a class="active" href="/calendar">📅 Calendar</a></nav></header><main>{body}</main></body></html>'''


def register(app):
    app.include_router(notifications_router)

    @app.get("/api/calendar")
    def api_calendar():
        return list_events()

    @app.post("/api/calendar/events")
    def api_add_event(request: CalendarEventRequest):
        return add_event(**request.model_dump())

    @app.delete("/api/calendar/events/{event_id}")
    def api_delete_event(event_id: str):
        return {"deleted": delete_event(event_id)}

    @app.get("/api/calendar/reminders")
    def api_reminders():
        return list_reminders()

    @app.post("/api/calendar/reminders")
    def api_add_reminder(request: ReminderRequest):
        return add_reminder(**request.model_dump())

    @app.delete("/api/calendar/reminders/{reminder_id}")
    def api_delete_reminder(reminder_id: str):
        return {"deleted": delete_reminder(reminder_id)}

    @app.post("/api/notifications/test")
    def api_test_push():
        sent = send_push("PGA testmelding", "Push notificaties werken. Geluid staat op default.")
        return {"sent": sent}

    @app.get("/calendar", response_class=HTMLResponse)
    def calendar_page():
        body = '''
<section class="full"><h2>Kalender</h2><div class="muted">Releases, pre-order bonus deadlines, GamesCom-dagen en eigen herinneringen op één plek.</div><div id="calendar" style="margin-top:12px">Laden...</div></section>
<section><h2>Event toevoegen</h2><div class="form"><input id="title" class="wide" placeholder="Bijv. GTA VI release"><select id="type"><option value="release">🎮 Release</option><option value="preorder_bonus_deadline">🎁 Pre-order bonus einddatum</option><option value="gamescom">🎟️ GamesCom</option><option value="event">📌 Overig</option></select><input id="start" type="datetime-local"><input id="end" type="datetime-local"><input id="url" class="wide" placeholder="Link (optioneel)"><textarea id="notes" class="wide" placeholder="Notities"></textarea><button onclick="addEvent()">＋ Event toevoegen</button></div></section>
<section><h2>Reminder instellen</h2><div class="form"><input id="rtitle" class="wide" placeholder="Bijv. Pre-order bonus verloopt"><input id="remindAt" type="datetime-local"><label class="pill"><input id="sound" type="checkbox" checked> 🔊 Geluid</label><button onclick="addReminder()">⏰ Reminder zetten</button></div><div class="muted" style="margin-top:10px">Herinneringen worden door de 5-minuten worker gecontroleerd.</div></section>
<section class="full"><h2>Herinneringen</h2><div id="reminders">Laden...</div></section>
<script>
const get=async u=>(await fetch(u)).json();function esc(s){return String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
function typeLabel(t){return {release:'🎮 Release',preorder_bonus_deadline:'🎁 Pre-order bonus',gamescom:'🎟️ GamesCom',event:'📌 Event'}[t]||t}
async function load(){const [e,r]=await Promise.all([get('/api/calendar'),get('/api/calendar/reminders')]);document.querySelector('#calendar').innerHTML=e.length?'<table><tr><th>Datum</th><th>Type</th><th>Titel</th><th>Bron</th><th></th></tr>'+e.map(x=>`<tr><td>${esc(x.start)}</td><td>${esc(typeLabel(x.type))}</td><td><b>${esc(x.title)}</b><br><span class="muted">${esc(x.notes||'')}</span></td><td>${x.url?`<a href="${esc(x.url)}" target="_blank">Link</a>`:esc(x.source||'—')}</td><td><button onclick="deleteEvent('${esc(x.id)}')">Verwijderen</button></td></tr>`).join('')+'</table>':'<div class="muted">Nog geen kalenderitems.</div>';document.querySelector('#reminders').innerHTML=r.length?r.map(x=>`<div class="reminder"><b>${esc(x.title)}</b><span class="pill">${esc(x.remind_at)}</span>${x.sound?'<span class="pill">🔊 geluid</span>':''}<button onclick="deleteReminder('${esc(x.id)}')">Verwijderen</button></div>`).join(''):'<div class="muted">Geen reminders.</div>'}
async function addEvent(){const body={title:document.querySelector('#title').value.trim(),event_type:document.querySelector('#type').value,start:document.querySelector('#start').value,end:document.querySelector('#end').value||null,url:document.querySelector('#url').value.trim()||null,notes:document.querySelector('#notes').value.trim()||null};if(!body.title||!body.start)return alert('Titel en datum zijn verplicht.');await fetch('/api/calendar/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});load()}
async function addReminder(){const title=document.querySelector('#rtitle').value.trim(),at=document.querySelector('#remindAt').value;if(!title||!at)return alert('Titel en datum zijn verplicht.');await fetch('/api/calendar/reminders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,remind_at:new Date(at).toISOString(),sound:document.querySelector('#sound').checked})});load()}
async function deleteEvent(id){await fetch('/api/calendar/events/'+encodeURIComponent(id),{method:'DELETE'});load()}async function deleteReminder(id){await fetch('/api/calendar/reminders/'+encodeURIComponent(id),{method:'DELETE'});load()}
load();setInterval(load,30000)
</script>'''
        return _page(body)
