from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from watchers.gamescom_schedule import GamesComYear


@dataclass(frozen=True)
class GamesComDashboardState:
    year: int
    selected_days: frozenset[date]
    preferred_day: date | None = None


def select_visit_days(
    year: GamesComYear,
    selected_days: set[date],
    preferred_day: date | None = None,
) -> GamesComDashboardState:
    invalid = {day for day in selected_days if not (year.start <= day <= year.end)}
    if preferred_day is not None and not (year.start <= preferred_day <= year.end):
        raise ValueError("Preferred day must fall within GamesCom")
    if preferred_day is not None and preferred_day not in selected_days:
        raise ValueError("Preferred day must be one of the selected visit days")
    if invalid:
        raise ValueError("Selected visit days must fall within GamesCom")
    return GamesComDashboardState(
        year=year.year,
        selected_days=frozenset(selected_days),
        preferred_day=preferred_day,
    )


def countdown_to_next_gamescom(next_start: date, today: date) -> int:
    return max(0, (next_start - today).days)


def post_gamescom_view(next_year: int, next_start: date, today: date) -> dict:
    return {
        "visible": False,
        "message": f"Tot {next_year}!",
        "next_year": next_year,
        "countdown_days": countdown_to_next_gamescom(next_start, today),
        "preferred_day_selection_enabled": True,
    }
