from __future__ import annotations

from dataclasses import dataclass
import re

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

    def __init__(self, timeout: float = 20.0):
        self.client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Personal-Gaming-Assistant/1.0"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def get_price(self, app_id: int) -> SteamPrice:
        url = f"{self.BASE}/app/{app_id}/"
        response = self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        name = soup.select_one("h1")
        text = soup.get_text(" ", strip=True)

        eur = self._currency_value(text, "€")
        uah = self._currency_value(text, "₴")
        return SteamPrice(
            app_id=app_id,
            name=name.get_text(" ", strip=True) if name else str(app_id),
            eur=eur,
            uah=uah,
            url=url,
        )

    @staticmethod
    def _currency_value(text: str, symbol: str) -> str | None:
        match = re.search(rf"{re.escape(symbol)}\s?[0-9][0-9.,]*", text)
        return match.group(0) if match else None
