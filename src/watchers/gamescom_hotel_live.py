from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class HotelOffer:
    hotel: str
    check_in: date
    check_out: date
    price: str | None
    currency: str | None
    availability: str
    url: str
    source: str


class GamesComHotelLiveClient:
    """Generic live hotel source adapter.

    The actual booking/search URL is supplied through GAMESCOM_HOTEL_URL so
    provider-specific URLs are not hard-coded or fabricated. The parser is
    deliberately conservative and reports UNKNOWN when availability cannot
    be established from the page.
    """

    def __init__(self, url: str | None = None, timeout: float = 20.0):
        self.url = url
        self.timeout = timeout

    def fetch(self, check_in: date, check_out: date) -> list[HotelOffer]:
        if not self.url:
            return []
        response = requests.get(self.url, timeout=self.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        offers: list[HotelOffer] = []
        for card in soup.find_all(["article", "li", "div"], class_=re.compile(r"hotel|property|accommodation", re.I)):
            text = " ".join(card.stripped_strings)
            if not text:
                continue
            link = card.find("a", href=True)
            if not link:
                continue
            offers.append(HotelOffer(
                hotel=" ".join(card.stripped_strings[:3]),
                check_in=check_in,
                check_out=check_out,
                price=self._price(text),
                currency="EUR" if "€" in text else None,
                availability="Available" if re.search(r"available|beschikbaar|verfügbar", text, re.I) else "Unknown",
                url=link["href"],
                source=self.url,
            ))
        return offers

    @staticmethod
    def _price(text: str) -> str | None:
        match = re.search(r"€\s?[0-9]+(?:[.,][0-9]{1,2})?", text)
        return match.group(0) if match else None
