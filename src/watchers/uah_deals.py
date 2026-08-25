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
    valid = sorted(amount for amount in denominations if amount >= price_uah)
    return valid[0] if valid else None


def find_best_uah_offer(price_uah: int, offers: Iterable[GiftCardOffer], denominations: Iterable[int]) -> UAHDealResult | None:
    required = required_gift_card_amount(price_uah, denominations)
    if required is None:
        return None
    candidates = [offer for offer in offers if offer.amount_uah >= required and offer.url]
    if not candidates:
        return None
    best = min(candidates, key=lambda offer: offer.price + offer.fees)
    return UAHDealResult(price_uah, required, best, best.price + best.fees)


def parse_uah_amount(value: str | int) -> int | None:
    try:
        text = str(value).replace("₴", "").replace("UAH", "").replace(" ", "")
        return int(Decimal(text.replace(",", ".")))
    except (InvalidOperation, ValueError):
        return None


def build_uah_deal_from_steamdb(steam_uah: str | int, offers: Iterable[GiftCardOffer], denominations: Iterable[int]) -> UAHDealResult | None:
    amount = parse_uah_amount(steam_uah)
    if amount is None:
        return None
    return find_best_uah_offer(amount, offers, denominations)


def verified_uah_game_deals(prices: Iterable[dict], *, limit: int = 10) -> list[dict]:
    """Return only games with verified Steam EUR + UAH prices."""
    valid = []
    for raw in prices:
        try:
            app_id = int(raw["app_id"])
            eur = float(raw["eur_price"])
            uah = float(raw["uah_price"])
        except (KeyError, TypeError, ValueError):
            continue
        if eur <= 0 or uah <= 0:
            continue
        valid.append({
            "app_id": app_id,
            "title": str(raw.get("title") or "Unknown game"),
            "eur_price": eur,
            "uah_price": uah,
            "ratio": uah / eur,
            "url": str(raw.get("url") or f"https://steamdb.info/app/{app_id}/"),
            "source": "SteamDB",
        })
    return sorted(valid, key=lambda item: item["ratio"])[:limit]
