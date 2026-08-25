from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Europe/Amsterdam")


@dataclass(frozen=True)
class CountdownState:
    active: bool
    label: str
    target: datetime
    days: int
    hours: int
    minutes: int
    seconds: int


def countdown_state(target: datetime, now: datetime | None = None) -> CountdownState:
    """Return active countdown, or the post-event 'Tot 2027!' state."""
    current = now or datetime.now(TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=TZ)
    target = target.astimezone(TZ)
    remaining = target - current
    if remaining.total_seconds() <= 0:
        return CountdownState(False, "Tot 2027!", target, 0, 0, 0, 0)
    total = int(remaining.total_seconds())
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    return CountdownState(True, "GamesCom Countdown", target, days, hours, minutes, seconds)
