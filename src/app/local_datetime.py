from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


NL_TZ = ZoneInfo("Europe/Amsterdam")


def news_datetime(now: datetime | None = None) -> dict[str, str]:
    """Return one timestamp in Dutch local time for the news header."""
    value = now or datetime.now(NL_TZ)
    if value.tzinfo is None:
        value = value.replace(tzinfo=NL_TZ)
    local = value.astimezone(NL_TZ)
    return {
        "date": local.strftime("%d-%m-%Y"),
        "time": local.strftime("%H:%M"),
        "timezone": "Europe/Amsterdam",
        "iso": local.isoformat(),
    }
