from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .gamescom_schedule import GamesComYear


@dataclass(frozen=True)
class GamesComAlert:
    kind: str
    title: str
    day: date
    url: str | None = None


def filter_attended_events(events: list[GamesComAlert], season: GamesComYear, today: date) -> list[GamesComAlert]:
    """Only expose events on the user's attended days while the GamesCom season is active."""
    if not season.is_active(today):
        return []
    return [event for event in events if season.is_attended_day(event.day)]


def entry_alerts(events: list[GamesComAlert], season: GamesComYear, today: date) -> list[GamesComAlert]:
    """Entry alerts are restricted to the same attended-day filter."""
    return [event for event in filter_attended_events(events, season, today) if event.kind == "entry"]


def watcher_visibility(season: GamesComYear, today: date) -> bool:
    """Ticket/hotel watchers are visible only during the active GamesCom season."""
    return season.is_active(today)
