from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class TweakersPricePoint:
    product: str
    price: float
    currency: str
    url: str
    source: str
    checked_at: str


class TweakersPriceHistoryClient:
    """Read publicly visible Tweakers product-price pages for history.

    URLs are supplied by configuration so the watcher never fabricates a
    product page. Only prices explicitly visible in the fetched page are
    recorded.
    """

    def __init__(self, urls: tuple[str, ...], timeout: float = 20.0):
        self.urls = urls
        self.timeout = timeout

    def fetch(self) -> list[TweakersPricePoint]:
        points: list[TweakersPricePoint] = []
        checked_at = datetime.now(timezone.utc).isoformat()
        for url in self.urls:
            response = requests.get(url, timeout=self.timeout, headers={"User-Agent": "Personal-Gaming-Assistant/1.0"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else url
            text = " ".join(soup.stripped_strings)
            for match in re.finditer(r"€\s*([0-9]+(?:[.,][0-9]{1,2})?)", text):
                price = float(match.group(1).replace(".", "").replace(",", "."))
                points.append(TweakersPricePoint(title, price, "EUR", urljoin(url, url), "Tweakers", checked_at))
                break
        return points
