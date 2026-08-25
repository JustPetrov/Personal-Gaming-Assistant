from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HotelOffer:
    name: str
    location: str
    price_per_night: float | None
    currency: str = "EUR"
    value_score: float | None = None
    booking_url: str | None = None


def rank_hotels(offers: list[HotelOffer]) -> list[HotelOffer]:
    """Rank supplied hotel offers by value score without inventing prices."""
    return sorted(
        offers,
        key=lambda offer: offer.value_score if offer.value_score is not None else float("-inf"),
        reverse=True,
    )
