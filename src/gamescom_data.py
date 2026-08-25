from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import json


@dataclass(frozen=True)
class GamesComYear:
    year: int
    start: date
    end: date
    official_url: str
    opening_night_live: date | None = None


SEASONS = {
    2026: GamesComYear(
        2026,
        date(2026, 8, 26),
        date(2026, 8, 30),
        "https://www.gamescom.global/",
        date(2026, 8, 25),
    ),
}


def live_start(season: GamesComYear) -> date:
    """Return the first day counted as live, including Opening Night Live."""
    return season.opening_night_live or season.start


def next_gamescom(after: date) -> GamesComYear | None:
    future = [s for s in SEASONS.values() if live_start(s) > after]
    return min(future, key=lambda x: live_start(x)) if future else None


def countdown(after: date, now: datetime | None = None) -> dict:
    now = now or datetime.now().astimezone()
    current = SEASONS.get(after.year)
    if current and live_start(current) <= now.date() <= current.end:
        return {
            "status": "live",
            "target": current.end.isoformat(),
            "days": 0,
        }
    if current and now.date() < live_start(current):
        start = live_start(current)
        return {
            "status": "countdown",
            "target": start.isoformat(),
            "days": max(0, (start - now.date()).days),
        }
    upcoming = next_gamescom(now.date())
    if not upcoming:
        return {"status": "awaiting_next_year_data", "target": None, "days": None}
    start = live_start(upcoming)
    return {
        "status": "countdown",
        "target": start.isoformat(),
        "days": max(0, (start - now.date()).days),
    }


def write_dashboard_data(events: list[dict] | None = None) -> None:
    """Write the canonical GamesCom state consumed by the dashboard."""
    path = Path("data/gamescom.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone()
    season = SEASONS.get(now.year)
    state = countdown(now.date(), now=now)

    if season:
        status = state["status"]
        target = state["target"]
        year = season.year
        start = season.start.isoformat()
        end = season.end.isoformat()
        official_url = season.official_url
    else:
        upcoming = next_gamescom(now.date())
        status = state["status"]
        target = state["target"]
        year = upcoming.year if upcoming else None
        start = upcoming.start.isoformat() if upcoming else None
        end = upcoming.end.isoformat() if upcoming else None
        official_url = upcoming.official_url if upcoming else "https://www.gamescom.global/"

    normalized_events: list[dict] = []
    for event in events or []:
        item = dict(event)
        normalized_events.append(item)

    # Keep the dashboard useful even when a live source returns no event rows.
    if season:
        normalized_events.insert(0, {
            "type": "gamescom_schedule",
            "name": "gamescom 2026",
            "start": season.start.isoformat(),
            "end": season.end.isoformat(),
            "live_start": live_start(season).isoformat(),
            "source": "GamesCom official",
            "url": season.official_url,
        })
        normalized_events.insert(0, {
            "type": "gamescom_opening_night_live",
            "name": "Opening Night Live",
            "date": season.opening_night_live.isoformat() if season.opening_night_live else None,
            "counts_as_live_day": True,
            "source": "GamesCom official",
            "url": season.official_url,
        })

    data = {
        "year": year,
        "status": status,
        "start": start,
        "end": end,
        "live_start": live_start(season).isoformat() if season else (upcoming.opening_night_live.isoformat() if upcoming and upcoming.opening_night_live else start),
        "opening_night_live": season.opening_night_live.isoformat() if season and season.opening_night_live else None,
        "counted_live_days": 6 if season and season.opening_night_live else None,
        "countdown_target": target,
        "countdown_days": state["days"],
        "events": normalized_events,
        "last_synced": now.isoformat(),
        "official_url": official_url,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
