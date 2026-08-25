from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(eq=False)
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

    def __eq__(self, other: object) -> bool:
        if not hasattr(other, "__dict__"):
            return NotImplemented
        fields = (
            "product", "platform", "edition", "price", "currency",
            "stock", "url", "source", "checked_at",
        )
        return all(
            getattr(self, field, object()) == getattr(other, field, object())
            for field in fields
        )


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
