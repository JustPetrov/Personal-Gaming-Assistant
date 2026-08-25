from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup


@dataclass
class RetailerResult:
    retailer: str
    query: str
    price: str | None
    stock: str | None
    url: str | None
    source: str


RETAILER_SEARCH_URLS = {
    "tweakers": "https://tweakers.net/pricewatch/zoeken/?keyword={q}",
    "bol": "https://www.bol.com/nl/nl/s/?searchtext={q}",
    "azerty": "https://azerty.nl/zoeken?q={q}",
    "alternate": "https://www.alternate.nl/listing.xhtml?q={q}",
    "megekko": "https://www.megekko.nl/Zoeken/{q}",
    "amazon_nl": "https://www.amazon.nl/s?k={q}",
}


class RetailerSearchClient:
    def __init__(self, timeout: float = 20.0):
        self.client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Personal-Gaming-Assistant/1.0"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def search(self, retailer: str, query: str) -> RetailerResult:
        template = RETAILER_SEARCH_URLS[retailer]
        url = template.format(q=quote_plus(query))
        response = self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        return RetailerResult(
            retailer=retailer,
            query=query,
            price=self._find_price(text),
            stock=self._find_stock(text),
            url=url,
            source=retailer,
        )

    @staticmethod
    def _find_price(text: str) -> str | None:
        import re
        match = re.search(r"€\s?\d+[,.]?\d*", text)
        return match.group(0) if match else None

    @staticmethod
    def _find_stock(text: str) -> str | None:
        lowered = text.lower()
        if "op voorraad" in lowered or "direct leverbaar" in lowered:
            return "Op voorraad"
        if "uitverkocht" in lowered or "niet leverbaar" in lowered:
            return "Niet op voorraad"
        return None
