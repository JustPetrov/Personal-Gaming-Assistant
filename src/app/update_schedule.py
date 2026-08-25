from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.update_writer import write_update


@dataclass(frozen=True)
class ScheduledUpdate:
    name: str
    hour: int
    minute: int = 0
    style: str = "compact Dutch gaming assistant update"


SCHEDULE = (
    ScheduledUpdate("morning", 8),
    ScheduledUpdate("noon", 12),
    ScheduledUpdate("evening", 20),
    ScheduledUpdate("late_night_roundup", 22, style="compact Dutch late-night gaming roundup"),
)


def due_update(now: datetime, *, timezone_name: str = "Europe/Amsterdam") -> ScheduledUpdate | None:
    local = now.astimezone(ZoneInfo(timezone_name))
    for item in SCHEDULE:
        if local.hour == item.hour and local.minute == item.minute:
            return item
    return None


def render_scheduled_update(changes: list[dict], now: datetime, *, timezone_name: str = "Europe/Amsterdam") -> str | None:
    item = due_update(now, timezone_name=timezone_name)
    if item is None:
        return None
    return write_update(changes, style=item.style)
