from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TravelTask:
    title: str
    completed: bool = False


DEFAULT_TRAVEL_TASKS = (
    "Standplanning maken",
    "Beurshallen / locaties bepalen",
    "Persoonlijke must-visits toevoegen",
    "EPIX Quest locaties toevoegen",
    "Eten/drinken plannen",
)


def build_travel_list(tasks: list[str] | None = None) -> list[TravelTask]:
    """Return the GamesCom travel list as a separate to-do list."""
    return [TravelTask(title) for title in (tasks or list(DEFAULT_TRAVEL_TASKS))]
