from __future__ import annotations

from dataclasses import dataclass
import re
import time

import httpx
from bs4 import BeautifulSoup


@dataclass
class SteamPrice:
    app_id: int
    name: str
    eur: str | None
    uah: str | None
    url: str
    source: str = "SteamDB"


class SteamDBClient:
    BASE = "https://steamdb.info"

    def __init__(self, timeout: float = 20.0, retries: int = 2):
        self.retries = max(0, retries)
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "Personal-Gaming-Assistant/1.0",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def get_price(self, app_id: int) -> SteamPrice:
        url = f"{self.BASE}/app/{app_id}/"
        response = self._get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.select_one("h1")
        text = soup.get_text(" ", strip=True)

        # Prefer the current-price section when present. SteamDB also exposes
        # historical prices on the same page, so blindly taking the first
        # currency match can return the wrong value.
        current_text = self._current_price_context(soup, text)
        eur = self._currency_value(current_text, "€")
        uah = self._currency_value(current_text, "₴")

        return SteamPrice(
            app_id=app_id,
            name=name.get_text(" ", strip=True) if name else str(app_id),
            eur=eur,
            uah=uah,
            url=url,
        )

    def _get(self, url: str) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                return response
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(1.0 * (attempt + 1))
        assert last_error is not None
        raise last_error

    @staticmethod
    def _current_price_context(soup: BeautifulSoup, fallback: str) -> str:
        # SteamDB markup changes occasionally. Try semantic labels first and
        # fall back to the page text rather than failing the entire watcher.
        for node in soup.find_all(string=re.compile(r"current price", re.I)):
            parent = node.parent
            if parent:
                container = parent.parent or parent
                context = container.get_text(" ", strip=True)
                if "€" in context or "₴" in context:
                    return context
        return fallback

    @staticmethod
    def _currency_value(text: str, symbol: str) -> str | None:
        matches = re.findall(rf"{re.escape(symbol)}\s?[0-9][0-9.,]*", text)
        if not matches:
            return None
        # Preserve the displayed SteamDB value rather than converting it.
        # De-duplicate repeated DOM/mobile markup before selecting a value.
        unique = list(dict.fromkeys(matches))
        return unique[0]
