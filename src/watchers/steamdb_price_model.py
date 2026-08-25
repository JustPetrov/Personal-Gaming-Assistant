from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SteamDBPriceObservation:
    app_id: int
    title: str
    eur_price: float | None
    uah_price: float | None
    eur_currency: str = "EUR"
    uah_currency: str = "UAH"
    source: str = "SteamDB"
    url: str | None = None


def to_price_observation(item: SteamDBPriceObservation) -> dict[str, Any]:
    """Normalize SteamDB EUR + UAH into one game-price record."""
    return {
        "id": f"steam:{item.app_id}",
        "product": item.title,
        "platform": "Steam",
        "source": item.source,
        "url": item.url,
        "prices": {
            "EUR": item.eur_price,
            "UAH": item.uah_price,
        },
        "has_uah": item.uah_price is not None,
    }


def uah_deal_candidates(items: list[SteamDBPriceObservation]) -> list[dict[str, Any]]:
    """Only return UAH deals when both EUR and UAH are actually present."""
    result = []
    for item in items:
        if item.eur_price is None or item.uah_price is None or item.eur_price <= 0:
            continue
        result.append({
            "id": item.app_id,
            "title": item.title,
            "eur_price": item.eur_price,
            "uah_price": item.uah_price,
            "uah_to_eur_ratio": item.uah_price / item.eur_price,
            "url": item.url,
            "source": item.source,
        })
    return sorted(result, key=lambda x: x["uah_to_eur_ratio"])
