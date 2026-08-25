from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


GAMESCOM_OFFICIAL_URL = "https://www.gamescom.global/"
GAMESCOM_TICKETS_URL = "https://www.gamescom.global/en/tickets/buy-tickets"
GAMESCOM_EPIX_URL = "https://www.gamescom.global/en/epix/quests"


@dataclass(frozen=True)
class AnnouncementState:
    ticket_sales_open: bool
    epix_available: bool
    checked_at: datetime
    ticket_url: str = GAMESCOM_TICKETS_URL
    epix_url: str = GAMESCOM_EPIX_URL


@dataclass(frozen=True)
class AnnouncementChange:
    kind: str
    title: str
    url: str


def detect_announcement_changes(previous: AnnouncementState | None, current: AnnouncementState) -> list[AnnouncementChange]:
    if previous is None:
        return []
    changes: list[AnnouncementChange] = []
    if not previous.ticket_sales_open and current.ticket_sales_open:
        changes.append(AnnouncementChange("ticket_sales", "🎟️ GamesCom ticketverkoop is gestart!", current.ticket_url))
    if not previous.epix_available and current.epix_available:
        changes.append(AnnouncementChange("epix_start", "🟣 GamesCom EPIX is gestart!", current.epix_url))
    return changes
