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
    style: str = "compact Dutch gaming assistant update with a short Round-Up"
    daily_window_hours: int = 4


SCHEDULE = (
    ScheduledUpdate("morning", 8, style="compact Dutch gaming assistant update; end with a short Round-Up"),
    ScheduledUpdate("noon", 12, style="compact Dutch gaming assistant update; end with a short Round-Up"),
    ScheduledUpdate("evening", 20, style="compact Dutch gaming assistant update; end with a short Round-Up"),
    ScheduledUpdate(
        "late_night",
        22,
        style="Dutch Late Night Update with an expanded Late Night Round-Up covering the whole day",
        daily_window_hours=24,
    ),
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
