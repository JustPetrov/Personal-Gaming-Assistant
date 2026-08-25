from __future__ import annotations

from dataclasses import dataclass
import re

import httpx
from bs4 import BeautifulSoup


@dataclass
class PlayStationListing:
    name: str
    edition: str | None
    price: str | None
    currency: str | None
    available: bool
    url: str
    source: str = "PlayStation Store"


class PlayStationStoreClient:
    def __init__(self, locale: str = "nl-nl", timeout: float = 20.0):
        self.locale = locale
        self.client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Personal-Gaming-Assistant/1.0"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def get_listing(self, url: str) -> PlayStationListing:
        response = self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("h1")
        text = soup.get_text(" ", strip=True)
        price_match = re.search(r"(?:€\s?\d+[,.]?\d*|\d+[,.]?\d*\s?€)", text)
        return PlayStationListing(
            name=title.get_text(" ", strip=True) if title else "Unknown",
            edition=None,
            price=price_match.group(0) if price_match else None,
            currency="EUR" if "€" in (price_match.group(0) if price_match else "") else None,
            available="Pre-order" in text or "Add to Cart" in text or "Buy" in text,
            url=url,
        )
