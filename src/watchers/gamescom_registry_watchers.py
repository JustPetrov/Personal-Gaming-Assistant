from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import os

from .gamescom_ticket_stock import TicketStatus, classify_ticket_status, stock_alert


@dataclass(frozen=True)
class GamesComAnnouncementStatus:
    ticket_sales_started: bool
    epix_started: bool
    ticket_sales_url: str
    epix_url: str


@dataclass(frozen=True)
class GamesComTicketSnapshot:
    statuses: tuple[TicketStatus, ...]
    checked_at: str


def announcement_observations(status: GamesComAnnouncementStatus) -> list[dict[str, str]]:
    """Normalize ticket/EPIX start states for persistent change detection."""
    return [
        {
            "product": "GamesCom Ticket Sales",
            "platform": "gamescom",
            "stock": "Started" if status.ticket_sales_started else "Not started",
            "url": status.ticket_sales_url,
            "source": "gamescom official",
        },
        {
            "product": "GamesCom EPIX",
            "platform": "gamescom",
            "stock": "Started" if status.epix_started else "Not started",
            "url": status.epix_url,
            "source": "gamescom official",
        },
    ]


def ticket_alerts(snapshot: GamesComTicketSnapshot) -> list[str]:
    return [alert for status in snapshot.statuses if (alert := stock_alert(status))]


def evening_ticket_active(day: date, today: date, start_hour: int = 16) -> bool:
    """Return whether an evening ticket is relevant for Thu-Sun after 16:00."""
    # Caller supplies the actual GamesCom day/date; Wednesday has no evening
    # ticket in this model.
    if day.weekday() not in {3, 4, 5, 6}:
        return False
    return today == day
