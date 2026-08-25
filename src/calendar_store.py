from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EVENTS_PATH = DATA / "calendar.json"
REMINDERS_PATH = DATA / "calendar_reminders.json"


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def _save(path: Path, value: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def list_events() -> list[dict]:
    return sorted(_load(EVENTS_PATH), key=lambda x: str(x.get("start", "")))


def add_event(title: str, event_type: str, start: str, end: str | None = None, *, url: str | None = None, notes: str | None = None, source: str | None = None) -> dict:
    events = _load(EVENTS_PATH)
    item = {
        "id": uuid4().hex,
        "title": title.strip(),
        "type": event_type,
        "start": start,
        "end": end,
        "url": url,
        "notes": notes,
        "source": source,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    events.append(item)
    _save(EVENTS_PATH, events)
    return item


def delete_event(event_id: str) -> bool:
    events = _load(EVENTS_PATH)
    filtered = [x for x in events if x.get("id") != event_id]
    changed = len(filtered) != len(events)
    if changed:
        _save(EVENTS_PATH, filtered)
    return changed


def list_reminders() -> list[dict]:
    return sorted(_load(REMINDERS_PATH), key=lambda x: str(x.get("remind_at", "")))


def add_reminder(title: str, remind_at: str, *, event_id: str | None = None, sound: bool = True) -> dict:
    reminders = _load(REMINDERS_PATH)
    item = {
        "id": uuid4().hex,
        "title": title.strip(),
        "remind_at": remind_at,
        "event_id": event_id,
        "sound": bool(sound),
        "sent": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    reminders.append(item)
    _save(REMINDERS_PATH, reminders)
    return item


def delete_reminder(reminder_id: str) -> bool:
    reminders = _load(REMINDERS_PATH)
    filtered = [x for x in reminders if x.get("id") != reminder_id]
    changed = len(filtered) != len(reminders)
    if changed:
        _save(REMINDERS_PATH, filtered)
    return changed


def due_reminders(now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    reminders = _load(REMINDERS_PATH)
    due: list[dict] = []
    changed = False
    for item in reminders:
        if item.get("sent"):
            continue
        try:
            when = datetime.fromisoformat(str(item.get("remind_at", "")).replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if when <= now:
            due.append(dict(item))
            item["sent"] = True
            item["sent_at"] = now.isoformat()
            changed = True
    if changed:
        _save(REMINDERS_PATH, reminders)
    return due
