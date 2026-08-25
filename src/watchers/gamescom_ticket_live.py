from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .gamescom_ticket_stock import TicketStatus, classify_ticket_status

OFFICIAL_TICKET_SHOP = "https://tickets.gamescom.global/"
DAYS = ("Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
EVENING_DAYS = frozenset(("Thursday", "Friday", "Saturday", "Sunday"))


@dataclass(frozen=True)
class LiveTicketPage:
    url: str
    html: str


class GamesComTicketLiveClient:
    """Read the official gamescom ticket shop and expose day-level status.

    The shop markup is allowed to change: selectors are deliberately broad and
    status is inferred from visible text rather than relying on one CSS class.
    """

    def __init__(self, session: requests.Session | None = None, timeout: float = 20.0):
        self.session = session or requests.Session()
        self.timeout = timeout
        self._owns_session = session is None

    def fetch_page(self) -> LiveTicketPage:
        response = self.session.get(OFFICIAL_TICKET_SHOP, timeout=self.timeout)
        response.raise_for_status()
        return LiveTicketPage(response.url, response.text)

    def fetch_statuses(self) -> list[TicketStatus]:
        page = self.fetch_page()
        soup = BeautifulSoup(page.html, "html.parser")
        text = " ".join(soup.stripped_strings)
        statuses: list[TicketStatus] = []
        for day in DAYS:
            regular = self._day_available(text, day, evening=False)
            evening = day in EVENING_DAYS and self._day_available(text, day, evening=True)
            low = self._day_low(text, day)
            stock = classify_ticket_status(
                regular_available=regular,
                evening_available=evening,
                low_stock=low,
            )
            statuses.append(TicketStatus(day, stock, regular, evening, page.url))
        return statuses

    @staticmethod
    def _day_available(text: str, day: str, evening: bool) -> bool:
        day_pattern = re.escape(day)
        evening_pattern = r"(?:evening|abend)" if evening else r"(?!evening|abend)"
        sold_pattern = r"(?:sold\s*out|ausverkauft|not\s*available|unavailable)"
        pattern = rf".{0,120}{day_pattern}.{0,120}{evening_pattern}.{0,120}"
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return False
        return not bool(re.search(sold_pattern, match.group(0), re.IGNORECASE))

    @staticmethod
    def _day_low(text: str, day: str) -> bool:
        match = re.search(rf".{0,160}{re.escape(day)}.{0,160}", text, re.IGNORECASE)
        if not match:
            return False
        return bool(re.search(r"low\s*(?:stock|availability)|limited\s*(?:stock|availability)|geringe\s*(?:verfügbarkeit|anzahl)", match.group(0), re.IGNORECASE))

    def close(self) -> None:
        if self._owns_session:
            self.session.close()
