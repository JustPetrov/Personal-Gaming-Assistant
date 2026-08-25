from __future__ import annotations

import json
from pathlib import Path

from hotels.hotel_watcher import HotelOffer, rank_hotels


STATE_PATH = Path("data/state/hotel_offers.json")


def changed_hotel_offers(offers: list[HotelOffer], *, path: Path = STATE_PATH) -> list[HotelOffer]:
    """Return newly seen or price/value-changed hotel offers."""
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        old = {}

    current: dict[str, dict] = {}
    changed: list[HotelOffer] = []
    for offer in rank_hotels(offers):
        key = offer.booking_url or f"{offer.name}|{offer.location}"
        snapshot = {
            "price_per_night": offer.price_per_night,
            "currency": offer.currency,
            "value_score": offer.value_score,
        }
        current[key] = snapshot
        if old.get(key) != snapshot:
            changed.append(offer)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return changed
