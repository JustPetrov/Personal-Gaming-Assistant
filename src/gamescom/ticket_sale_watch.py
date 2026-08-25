from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Europe/Amsterdam")


@dataclass(frozen=True)
class SaleStatus:
    open: bool
    notify: bool
    message: str


def check_ticket_sale_start(start: datetime, now: datetime | None = None, *, notified: bool = False) -> SaleStatus:
    """Return a one-time notification when GamesCom ticket sales open."""
    current = now or datetime.now(TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=TZ)
    start = start.astimezone(TZ)
    if current < start:
        return SaleStatus(False, False, "GamesCom ticketverkoop is nog niet gestart")
    if notified:
        return SaleStatus(True, False, "GamesCom ticketverkoop is gestart")
    return SaleStatus(True, True, "GamesCom ticketverkoop is gestart — ticketvoorraad wordt nu gevolgd")
