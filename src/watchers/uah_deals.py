from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from collections.abc import Iterable


@dataclass(frozen=True)
class GiftCardOffer:
    amount_uah: int
    price: Decimal
    currency: str
    seller: str
    rating: str | None
    reviews: int | None
    fees: Decimal = Decimal("0")
    url: str | None = None


@dataclass(frozen=True)
class UAHDealResult:
    steam_price_uah: int
    required_card_uah: int
    offer: GiftCardOffer
    total_cost: Decimal
    route: str = "UAH Gift Card"


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


def required_gift_card_amount(price_uah: int, denominations: Iterable[int]) -> int | None:
    """Return the smallest configured denomination that covers the Steam price."""
    valid = sorted(amount for amount in denominations if amount >= price_uah)
    return valid[0] if valid else None


def find_best_uah_offer(
    price_uah: int,
    offers: Iterable[GiftCardOffer],
    denominations: Iterable[int],
) -> UAHDealResult | None:
    required = required_gift_card_amount(price_uah, denominations)
    if required is None:
        return None
    candidates = [offer for offer in offers if offer.amount_uah >= required]
    if not candidates:
        return None
    best = min(candidates, key=lambda offer: offer.price + offer.fees)
    return UAHDealResult(
        steam_price_uah=price_uah,
        required_card_uah=required,
        offer=best,
        total_cost=best.price + best.fees,
    )


def parse_uah_amount(value: str | int) -> int | None:
    """Parse a UAH price such as '899₴' into an integer amount."""
    try:
        text = str(value).replace("₴", "").replace("UAH", "").replace(" ", "")
        return int(Decimal(text.replace(",", ".")))
    except (InvalidOperation, ValueError):
        return None
