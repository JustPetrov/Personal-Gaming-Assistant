from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from urllib.parse import urljoin

import requests


OFFICIAL_GAMESCOM_TICKETS_URL = "https://tickets.gamescom.global/"


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
    """Fetch the official gamescom ticket shop page.

    The shop is the authoritative source for live ticket availability. The
    parser intentionally accepts several common availability phrases because
    the shop may change its wording between sales periods.
    """

    def __init__(self, url: str = OFFICIAL_GAMESCOM_TICKETS_URL, timeout: float = 15.0):
        self.url = url
        self.timeout = timeout

    def fetch(self) -> tuple[str, str, datetime]:
        response = requests.get(
            self.url,
            timeout=self.timeout,
            headers={"User-Agent": "Personal-Gaming-Assistant/1.0"},
        )
        response.raise_for_status()
        return response.text, response.url, datetime.now(timezone.utc)

    @staticmethod
    def classify_text(text: str) -> tuple[bool, bool, bool, bool]:
        normalized = re.sub(r"\s+", " ", text).lower()
        sold_out = any(token in normalized for token in ("sold out", "ausverkauft", "not available"))
        evening = any(token in normalized for token in ("evening ticket", "evening-ticket", "ab 16", "from 16:00"))
        low = any(token in normalized for token in ("low stock", "limited availability", "wenige", "knapp"))
        regular = not sold_out and any(token in normalized for token in ("day ticket", "tageskarte", "ticket available", "buy ticket"))
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
            url=urljoin(final_url, "/"),
            checked_at=checked_at,
        )
