from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from urllib.parse import urljoin

import requests


OFFICIAL_GAMESCOM_TICKETS_URL = "https://tickets.gamescom.global/cgi-bin/fmkm_visit/lib/pub/tt.cgi/Tickets_private_visitor.html?oid=63485&lang=2&ticket=39129273870273#/articles"


@dataclass(frozen=True)
class LiveTicketStatus:
    day: str
    regular_available: bool
    evening_available: bool
    low_stock: bool
    sold_out: bool
    url: str
    checked_at: datetime


class GamesComTicketSource:
    """Read the official private-visitor Gamescom ticket portal.

    Availability is only reported as SOLD_OUT when the portal explicitly
    contains a sold-out marker. A blocked, incomplete, changed, or otherwise
    unrecognisable page is deliberately treated as UNKNOWN by the caller
    instead of being converted into a false SOLD_OUT state.
    """

    def __init__(self, url: str = OFFICIAL_GAMESCOM_TICKETS_URL, timeout: float = 20.0):
        self.url = url
        self.timeout = timeout

    def fetch(self) -> tuple[str, str, datetime]:
        response = requests.get(
            self.url,
            timeout=self.timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; Personal-Gaming-Assistant/1.0)",
                "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            },
        )
        response.raise_for_status()
        return response.text, response.url, datetime.now(timezone.utc)

    @staticmethod
    def classify_text(text: str) -> tuple[bool, bool, bool, bool]:
        normalized = re.sub(r"\s+", " ", text).lower()
        sold_out = any(token in normalized for token in (
            "sold out", "sold-out", "ausverkauft", "ausverkauft!",
        ))
        evening = any(token in normalized for token in (
            "evening ticket", "evening-ticket", "evening admission",
            "ab 16", "from 16:00", "from 4:00 pm",
        ))
        low = any(token in normalized for token in (
            "low stock", "limited availability", "few tickets",
            "wenige", "knapp", "nur noch",
        ))
        regular = not sold_out and any(token in normalized for token in (
            "day ticket", "day-ticket", "day admission", "tageskarte",
            "ticket available", "available tickets", "buy ticket",
            "tickets available", "available now",
        ))
        return regular, evening, low, sold_out

    def fetch_day(self, day: str) -> LiveTicketStatus:
        html, final_url, checked_at = self.fetch()
        regular, evening, low, sold_out = self.classify_text(html)
        return LiveTicketStatus(
            day=day,
            regular_available=regular,
            evening_available=evening,
            low_stock=low,
            sold_out=sold_out,
            url=final_url or urljoin(self.url, "/"),
            checked_at=checked_at,
        )
