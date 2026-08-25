from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from watchers.gamescom_schedule import GamesComYear


@dataclass(frozen=True)
class GamesComDashboardState:
    year: int
    selected_days: frozenset[date]


def select_visit_days(year: GamesComYear, selected_days: set[date]) -> GamesComDashboardState:
    invalid = selected_days - set(year.attended_days)
    if invalid:
        # Dashboard selection is authoritative: allow any date inside the
        # configured GamesCom season, not just a pre-filled default.
        invalid = {day for day in selected_days if not (year.start <= day <= year.end)}
    if invalid:
        raise ValueError("Selected visit days must fall within GamesCom")
    return GamesComDashboardState(year=year.year, selected_days=frozenset(selected_days))


def countdown_to_next_gamescom(next_start: date, today: date) -> int:
    return max(0, (next_start - today).days)


def post_gamescom_view(next_year: int, next_start: date, today: date) -> dict:
    return {
        "visible": False,
        "message": f"Tot {next_year}!",
        "next_year": next_year,
        "countdown_days": countdown_to_next_gamescom(next_start, today),
    }
