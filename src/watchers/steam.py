from __future__ import annotations

from dataclasses import dataclass
import re

import httpx
from bs4 import BeautifulSoup


@dataclass
class SteamGameStatus:
    app_id: int
    name: str
    url: str
    price: str | None
    free_to_play: bool
    free_to_keep: bool
    available: bool
    source: str = "Steam"


class SteamStoreClient:
    BASE = "https://store.steampowered.com"

    def __init__(self, timeout: float = 20.0):
        self.client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Personal-Gaming-Assistant/1.0"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def get_app(self, app_id: int) -> SteamGameStatus:
        url = f"{self.BASE}/app/{app_id}/"
        response = self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.select_one(".apphub_AppName") or soup.select_one("h1")
        text = soup.get_text(" ", strip=True)
        price_node = soup.select_one(".game_purchase_price")
        price = price_node.get_text(" ", strip=True) if price_node else None
        free_to_play = "Free to Play" in text
        free_to_keep = bool(re.search(r"Free to Keep|Keep it forever", text, re.I))
        return SteamGameStatus(
            app_id=app_id,
            name=title.get_text(" ", strip=True) if title else str(app_id),
            url=url,
            price=price,
            free_to_play=free_to_play,
            free_to_keep=free_to_keep,
            available="Currently available" in text or "Add to Cart" in text,
        )
