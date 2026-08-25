from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class GamesComSeason:
    year: int
    opening_day: date
    closing_day: date

    def active(self, today: date) -> bool:
        return self.opening_day <= today <= self.closing_day


@dataclass(frozen=True)
class VisitDay:
    day: date
    confirmed: bool


def visible_events(events: list[dict], visit_days: list[VisitDay]) -> list[dict]:
    allowed = {v.day for v in visit_days if v.confirmed}
    return [event for event in events if event.get("date") in allowed]


def entry_alert_minutes(minutes_until_entry: int) -> str | None:
    for threshold in (60, 30, 15, 10, 5):
        if minutes_until_entry == threshold:
            return f"T-{threshold}"
    if minutes_until_entry == 0:
        return "Opening"
    return None
