from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from gamescom.ticket_sale_watch import check_ticket_sale_start

TZ = ZoneInfo("Europe/Amsterdam")


def ticket_sale_observation(start: datetime, *, now: datetime | None = None, notified: bool = False) -> dict:
    """Create a monitoring observation for the GamesCom ticket-sale start."""
    status = check_ticket_sale_start(start, now=now, notified=notified)
    return {
        "type": "gamescom_ticket_sale_status",
        "open": status.open,
        "notify": status.notify,
        "message": status.message,
        "start": start.astimezone(TZ).isoformat(),
    }
