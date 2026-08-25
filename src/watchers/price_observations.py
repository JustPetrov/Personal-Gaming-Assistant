from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Iterable

from .price_models import PriceObservation


def observation_from_values(
    *,
    product: str,
    platform: str,
    edition: str | None = None,
    price: str | None = None,
    currency: str | None = None,
    stock: str | None = None,
    url: str | None = None,
    source: str,
    checked_at: datetime | None = None,
) -> PriceObservation:
    """Create one normalized price observation with a timezone-aware timestamp."""
    timestamp = checked_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return PriceObservation(
        product=product.strip(),
        platform=platform.strip(),
        edition=edition.strip() if edition else None,
        price=price.strip() if price else None,
        currency=currency.strip() if currency else None,
        stock=stock.strip() if stock else None,
        url=url.strip() if url else None,
        source=source.strip(),
        checked_at=timestamp,
    )


def observation_key(observation: PriceObservation) -> tuple[str, str, str | None]:
    """Stable identity used for comparing observations between watcher runs."""
    return (observation.product, observation.platform, observation.edition)


def normalize_observations(observations: Iterable[PriceObservation]) -> list[PriceObservation]:
    """Normalize and deterministically order watcher output."""
    result = list(observations)
    result.sort(key=lambda item: observation_key(item))
    return result


def observation_dict(observation: PriceObservation) -> dict:
    """Serialize an observation for JSON/history storage."""
    data = asdict(observation)
    data["checked_at"] = observation.checked_at.isoformat()
    return data
