from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ScheduledUpdate:
    hour: int
    minute: int
    kind: str
    late_night_round_up: bool = False


SCHEDULE = (
    ScheduledUpdate(8, 0, "morning"),
    ScheduledUpdate(12, 0, "midday"),
    ScheduledUpdate(20, 0, "evening"),
    ScheduledUpdate(22, 0, "late_night", late_night_round_up=True),
)


def get_schedule(timezone_name: str = "Europe/Amsterdam") -> tuple[ScheduledUpdate, ...]:
    """Return the fixed daily schedule; timezone is used by the runner."""
    ZoneInfo(timezone_name)  # validate configured timezone early
    return SCHEDULE


def update_kind_at(dt: datetime, timezone_name: str = "Europe/Amsterdam") -> ScheduledUpdate | None:
    local = dt.astimezone(ZoneInfo(timezone_name))
    for scheduled in SCHEDULE:
        if local.hour == scheduled.hour and local.minute == scheduled.minute:
            return scheduled
    return None
