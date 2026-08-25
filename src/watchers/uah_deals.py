from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreditRoute:
    name: str
    face_value: float
    currency: str
    total_cost: float
    fee: float
    url: str | None
    seller_rating: float | None = None
    review_count: int | None = None

    @property
    def effective_cost(self) -> float:
        return self.total_cost + self.fee


def choose_cheapest(routes: list[CreditRoute]) -> CreditRoute | None:
    """Choose the cheapest verified route after fees."""
    valid = [r for r in routes if r.url and r.total_cost >= 0 and r.fee >= 0]
    return min(valid, key=lambda r: r.effective_cost, default=None)
