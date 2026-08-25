from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Europe/Amsterdam")


@dataclass(frozen=True)
class StartStatus:
    started: bool
    notify: bool
    message: str


def check_epix_start(start: datetime, now: datetime | None = None, *, notified: bool = False) -> StartStatus:
    """Return a one-time notification when EPIX reaches its configured start."""
    current = now or datetime.now(TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=TZ)
    start = start.astimezone(TZ)
    if current < start:
        return StartStatus(False, False, "EPIX is nog niet gestart")
    if notified:
        return StartStatus(True, False, "EPIX is gestart")
    return StartStatus(True, True, "EPIX is gestart — nieuwe quests kunnen nu beschikbaar zijn")
