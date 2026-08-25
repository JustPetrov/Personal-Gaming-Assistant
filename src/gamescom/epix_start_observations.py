from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from gamescom.epix_start_state import load_notified, mark_notified
from gamescom.epix_start_watch import check_epix_start

TZ = ZoneInfo("Europe/Amsterdam")


def epix_start_observation(start: datetime, *, now: datetime | None = None) -> dict:
    """Create an EPIX start observation using persistent one-time state."""
    status = check_epix_start(start, now=now, notified=load_notified())
    if status.notify:
        mark_notified()
    return {
        "type": "gamescom_epix_start_status",
        "started": status.started,
        "notify": status.notify,
        "message": status.message,
        "start": start.astimezone(TZ).isoformat(),
    }
