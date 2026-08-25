from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GamePriceNews:
    title: str
    eur_price: float | None
    uah_price: float | None
    price_changed: bool
    url: str
    source: str


def build_game_price_news(observations: list[dict[str, Any]]) -> list[GamePriceNews]:
    """Select stored Game Price Watcher observations for the news layer."""
    result: list[GamePriceNews] = []
    for item in observations:
        if str(item.get("source", "")).lower() != "steamdb":
            continue
        eur = _float(item.get("eur_price", item.get("price")))
        uah = _float(item.get("uah_price"))
        result.append(GamePriceNews(
            title=str(item.get("title") or item.get("product") or "Onbekende game"),
            eur_price=eur,
            uah_price=uah,
            price_changed=bool(item.get("price_changed", False)),
            url=str(item.get("url") or ""),
            source="SteamDB",
        ))
    return result


def _float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace("€", "").replace("₴", "").replace(",", ".").strip())
    except ValueError:
        return None
