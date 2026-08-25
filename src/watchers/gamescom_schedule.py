from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class GamesComYear:
    year: int
    start: date
    end: date
    attended_days: frozenset[date]

    def is_active(self, today: date) -> bool:
        return self.start <= today <= self.end

    def is_attended_day(self, day: date) -> bool:
        return day in self.attended_days

    def should_show_event(self, event_day: date, today: date) -> bool:
        return self.is_active(today) and self.is_attended_day(event_day)


def build_gamescom_year(year: int, start: date, end: date, attended_days: set[date]) -> GamesComYear:
    return GamesComYear(year, start, end, frozenset(attended_days))
