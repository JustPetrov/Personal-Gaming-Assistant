from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup


@dataclass
class G2GListing:
    title: str
    price: str | None
    currency: str | None
    stock: str | None
    rating: str | None
    review_count: int | None
    url: str
    source: str = "G2G"


class G2GClient:
    BASE = "https://www.g2g.com/search?query="

    def __init__(self, timeout: float = 20.0):
        self.client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Personal-Gaming-Assistant/1.0"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def search(self, query: str) -> list[G2GListing]:
        url = self.BASE + quote_plus(query)
        response = self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        listings: list[G2GListing] = []
        for card in soup.select("[class*=product], [class*=item], [class*=offer]")[:20]:
            text = card.get_text(" ", strip=True)
            if not text:
                continue
            link = card.find("a", href=True)
            href = link.get("href") if link else url
            if href and href.startswith("/"):
                href = "https://www.g2g.com" + href
            listings.append(G2GListing(
                title=text[:160],
                price=self._price(text),
                currency="$" if "$" in text else None,
                stock="Available" if "available" in text.lower() or "in stock" in text.lower() else None,
                rating=None,
                review_count=None,
                url=href or url,
            ))
        return listings

    @staticmethod
    def _price(text: str) -> str | None:
        import re
        match = re.search(r"(?:US\$|\$)\s?[0-9]+(?:[.,][0-9]+)?", text)
        return match.group(0) if match else None
