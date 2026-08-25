from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
import json


@dataclass(frozen=True)
class GamesComYear:
    year: int
    start: date
    end: date
    official_url: str


# Dates can be updated from the official GamesCom feed/source when available.
# Keeping the season model yearly means the dashboard continues after the current event.
SEASONS = {
    2026: GamesComYear(2026, date(2026, 8, 26), date(2026, 8, 30), "https://www.gamescom.global/"),
}


def next_gamescom(after: date) -> GamesComYear | None:
    future = [s for s in SEASONS.values() if s.start > after]
    return min(future, key=lambda x: x.start) if future else None


def countdown(after: date, now: datetime | None = None) -> dict:
    now = now or datetime.now().astimezone()
    current = SEASONS.get(after.year)
    if current and current.start <= now.date() <= current.end:
        return {"status": "live", "target": current.end.isoformat(), "days": 0}
    upcoming = next_gamescom(now.date())
    if not upcoming:
        return {"status": "awaiting_next_year_data", "target": None, "days": None}
    return {
        "status": "countdown",
        "target": upcoming.start.isoformat(),
        "days": max(0, (upcoming.start - now.date()).days),
    }


def write_dashboard_data(events: list[dict] | None = None) -> None:
    path = Path("data/gamescom.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone()
    season = SEASONS.get(now.year)
    data = {
        "year": season.year if season else None,
        "status": "live" if season and season.start <= now.date() <= season.end else "countdown",
        "start": season.start.isoformat() if season else None,
        "end": season.end.isoformat() if season else None,
        "countdown_target": (next_gamescom(now.date()).start.isoformat() if next_gamescom(now.date()) else None),
        "events": events or [],
        "last_synced": now.isoformat(),
        "official_url": season.official_url if season else "https://www.gamescom.global/",
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
