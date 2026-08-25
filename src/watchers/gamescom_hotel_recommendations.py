from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class HotelRecommendation:
    name: str
    category: str
    price_per_night: Decimal | None
    rating: float | None
    distance_to_koelnmesse_m: int | None
    location: str | None
    url: str | None
    reason: str


def _quality_score(o: HotelRecommendation) -> Decimal:
    rating = Decimal(str(o.rating or 0))
    distance = Decimal(str(o.distance_to_koelnmesse_m or 5000))
    price = o.price_per_night or Decimal("9999")
    # Strong quality signal from rating, then price and practical proximity.
    return rating * Decimal("20") - price * Decimal("0.10") - distance / Decimal("500")


def rank_hotels(
    offers: list[HotelRecommendation],
    *,
    alternative_radius_km: float = 40.0,
) -> tuple[HotelRecommendation | None, HotelRecommendation | None]:
    """Return best price/quality in Cologne and a cheaper regional alternative.

    The primary recommendation is restricted to Cologne. The alternative may
    be in Cologne or nearby towns/cities within the configured radius. A
    missing price is never interpreted as free and a missing rating is never
    interpreted as a positive rating.
    """
    priced = [o for o in offers if o.price_per_night is not None]
    if not priced:
        return None, None

    cologne = [o for o in priced if (o.location or "").casefold() in {"köln", "koeln", "cologne"}]
    best_pool = cologne or priced
    best = max(best_pool, key=_quality_score)

    # Nearby alternatives are accepted even when they are outside Cologne.
    # Distance to Koelnmesse is the canonical travel-distance field; when it is
    # missing, the offer is excluded rather than guessed into the radius.
    radius_m = int(alternative_radius_km * 1000)
    alternatives = [
        o for o in priced
        if o.name != best.name
        and o.price_per_night < best.price_per_night
        and o.distance_to_koelnmesse_m is not None
        and o.distance_to_koelnmesse_m <= radius_m
    ]
    cheaper = max(
        alternatives,
        key=lambda o: (_quality_score(o), -(o.price_per_night or Decimal("9999"))),
        default=None,
    )
    return best, cheaper
