from __future__ import annotations

import re
from dataclasses import dataclass

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
    """Read the official gamescom ticket shop and expose day-level status."""

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
        return [self._status_for_day(text, day, page.url) for day in DAYS]

    def _status_for_day(self, text: str, day: str, url: str) -> TicketStatus:
        regular = self._day_available(text, day, evening=False)
        evening = day in EVENING_DAYS and self._day_available(text, day, evening=True)
        low = self._day_low(text, day)
        stock = classify_ticket_status(
            regular_available=regular,
            evening_available=evening,
            low_stock=low,
        )
        return TicketStatus(day, stock, regular, evening, url)

    @staticmethod
    def _day_available(text: str, day: str, evening: bool) -> bool:
        match = re.search(rf".{0,120}{re.escape(day)}.{0,180}", text, re.IGNORECASE)
        if not match:
            return False
        window = match.group(0)
        if evening and not re.search(r"evening|abend", window, re.IGNORECASE):
            return False
        if not evening and re.search(r"evening|abend", window, re.IGNORECASE):
            return False
        return not bool(re.search(r"sold\s*out|ausverkauft|not\s*available|unavailable|uitverkocht", window, re.IGNORECASE))

    @staticmethod
    def _day_low(text: str, day: str) -> bool:
        match = re.search(rf".{0,160}{re.escape(day)}.{0,160}", text, re.IGNORECASE)
        return bool(match and re.search(r"low\s*(?:stock|availability)|limited\s*(?:stock|availability)|geringe\s*(?:verfügbarkeit|anzahl)|lage\s*voorraad", match.group(0), re.IGNORECASE))

    def close(self) -> None:
        if self._owns_session:
            self.session.close()
