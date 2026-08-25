from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import os
import re
from urllib.parse import urljoin

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

    Sources are configured through environment variables rather than guessed
    provider URLs. Booking.com and Trivago can therefore be enabled explicitly
    while keeping the parser conservative and source-labelled.
    """

    DEFAULT_SOURCE_VARS = (
        "GAMESCOM_HOTEL_URL",
        "GAMESCOM_BOOKING_URL",
        "GAMESCOM_TRIVAGO_URL",
    )

    def __init__(self, url: str | None = None, timeout: float = 20.0):
        self.url = url
        self.timeout = timeout

    @classmethod
    def configured_clients(cls, timeout: float = 20.0) -> list["GamesComHotelLiveClient"]:
        return [
            cls(os.getenv(name), timeout=timeout)
            for name in cls.DEFAULT_SOURCE_VARS
            if os.getenv(name, "").strip()
        ]

    def fetch(self, check_in: date, check_out: date) -> list[HotelOffer]:
        if not self.url:
            return []
        response = requests.get(
            self.url,
            timeout=self.timeout,
            headers={"User-Agent": "Personal-Gaming-Assistant/1.0"},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        source = self._source_name(self.url)
        offers: list[HotelOffer] = []
        for card in soup.find_all(
            ["article", "li", "div"],
            class_=re.compile(r"hotel|property|accommodation", re.I),
        ):
            text = " ".join(card.stripped_strings)
            if not text:
                continue
            link = card.find("a", href=True)
            if not link:
                continue
            offers.append(
                HotelOffer(
                    hotel=" ".join(card.stripped_strings[:3]),
                    check_in=check_in,
                    check_out=check_out,
                    price=self._price(text),
                    currency="EUR" if "€" in text else None,
                    availability=(
                        "Available"
                        if re.search(r"available|beschikbaar|verfügbar", text, re.I)
                        else "Unknown"
                    ),
                    url=urljoin(self.url, link["href"]),
                    source=source,
                )
            )
        return offers

    @staticmethod
    def _source_name(url: str) -> str:
        host = re.sub(r"^www\\.", "", url.split("/", 3)[2].lower()) if "://" in url else url.lower()
        if "booking.com" in host:
            return "Booking.com"
        if "trivago" in host:
            return "Trivago"
        return host

    @staticmethod
    def _price(text: str) -> str | None:
        match = re.search(r"€\s?[0-9]+(?:[.,][0-9]{1,2})?", text)
        return match.group(0) if match else None
