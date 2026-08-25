from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SteamDBPrice:
    app_id: int
    title: str
    eur_price: float | None
    uah_price: float | None
    url: str
    source: str = "SteamDB"


def normalize_steamdb_price(raw: dict) -> SteamDBPrice | None:
    """Normalize an adapter result; missing currencies stay missing."""
    try:
        app_id = int(raw["app_id"])
    except (KeyError, TypeError, ValueError):
        return None
    title = str(raw.get("title") or "Unknown game")
    url = str(raw.get("url") or f"https://steamdb.info/app/{app_id}/")
    eur = _number(raw.get("eur_price"))
    uah = _number(raw.get("uah_price"))
    return SteamDBPrice(app_id, title, eur, uah, url)


def _number(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace("€", "").replace("₴", "").replace(",", ".").strip())
    except ValueError:
        return None
