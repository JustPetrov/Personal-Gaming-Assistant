from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PriceObservation:
    product: str
    platform: str
    edition: str | None
    price: str | None
    currency: str | None
    stock: str | None
    url: str | None
    source: str
    checked_at: datetime


@dataclass
class SellerObservation:
    seller: str
    product: str
    price: str | None
    currency: str | None
    stock: str | None
    rating: str | None
    review_count: int | None
    url: str | None
    source: str
    checked_at: datetime
