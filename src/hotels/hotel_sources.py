from __future__ import annotations

from dataclasses import dataclass

from hotels.hotel_watcher import HotelOffer, rank_hotels


@dataclass(frozen=True)
class HotelSearch:
    destination: str
    include_surrounding_towns: bool = True
    max_price_per_night: float | None = None


def select_recommendations(offers: list[HotelOffer]) -> dict[str, HotelOffer | None]:
    """Select best value in Cologne and the best cheaper surrounding option.

    This function only ranks supplied offers; it never fabricates availability
    or prices. Location classification is based on the supplied location text.
    """
    ranked = rank_hotels(offers)
    cologne = [o for o in ranked if o.location.lower() in {"cologne", "köln", "koln"}]
    surrounding = [o for o in ranked if o not in cologne]
    best = cologne[0] if cologne else None
    cheaper = None
    if best and best.price_per_night is not None:
        candidates = [o for o in surrounding if o.price_per_night is not None and o.price_per_night < best.price_per_night]
        cheaper = min(candidates, key=lambda o: o.price_per_night) if candidates else None
    elif surrounding:
        cheaper = surrounding[0]
    return {"best_cologne": best, "cheaper_surrounding": cheaper}
