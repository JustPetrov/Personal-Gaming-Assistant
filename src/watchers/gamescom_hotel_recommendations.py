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
    url: str | None
    reason: str


def rank_hotels(offers: list[HotelRecommendation]) -> tuple[HotelRecommendation | None, HotelRecommendation | None]:
    """Return best price/quality and a cheaper alternative.

    Score favours guest rating and proximity while penalising price. Missing
    live prices are never treated as zero, so the watcher cannot fabricate a
    cheap recommendation.
    """
    priced = [o for o in offers if o.price_per_night is not None]
    if not priced:
        return None, None

    def score(o: HotelRecommendation) -> Decimal:
        rating = Decimal(str(o.rating or 0))
        distance = Decimal(str(o.distance_to_koelnmesse_m or 5000))
        price = o.price_per_night or Decimal("9999")
        return rating * Decimal("20") - price * Decimal("0.10") - distance / Decimal("500")

    best = max(priced, key=score)
    cheaper = min(
        (o for o in priced if o.price_per_night < best.price_per_night),
        key=lambda o: (-Decimal(str(o.rating or 0)), o.price_per_night),
        default=None,
    )
    return best, cheaper
