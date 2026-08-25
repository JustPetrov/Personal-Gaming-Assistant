from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from gamescom.ticket_sale_state import load_notified, mark_notified
from gamescom.ticket_sale_watch import check_ticket_sale_start

TZ = ZoneInfo("Europe/Amsterdam")


def ticket_sale_observation(start: datetime, *, now: datetime | None = None) -> dict:
    """Create a ticket-sale observation using persistent one-time notification state."""
    notified = load_notified()
    status = check_ticket_sale_start(start, now=now, notified=notified)
    if status.notify:
        mark_notified()
    return {
        "type": "gamescom_ticket_sale_status",
        "open": status.open,
        "notify": status.notify,
        "message": status.message,
        "start": start.astimezone(TZ).isoformat(),
    }
