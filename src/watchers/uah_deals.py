from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


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


@dataclass(frozen=True)
class UAHGameRoute:
    app_id: int
    title: str
    steam_price_uah: int
    required_card_uah: int
    total_cost: Decimal
    seller: str
    url: str
    source: str = "UAH Gift Card"


@dataclass(frozen=True)
class UAHRouteSummary:
    routes: tuple[UAHGameRoute, ...]
    total_cost: Decimal
    games_considered: int
    games_with_verified_route: int


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
    candidates = [
        offer for offer in offers
        if offer.amount_uah >= required
        and offer.url
        and offer.price >= 0
        and offer.fees >= 0
    ]
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


def build_uah_route_summary(
    prices: Iterable[dict],
    offers_by_app_id: Mapping[int, Iterable[GiftCardOffer]],
    denominations: Iterable[int],
) -> UAHRouteSummary:
    """Build the cheapest verified UAH gift-card route for every eligible game.

    No FX conversion is performed: EUR is retained as reference data and only
    verified UAH purchase routes are summed. Games without a verified UAH route
    are excluded from the total rather than estimated.
    """
    routes: list[UAHGameRoute] = []
    seen: set[int] = set()
    games_considered = 0

    for raw in prices:
        try:
            app_id = int(raw["app_id"])
            steam_uah = parse_uah_amount(raw["uah_price"])
        except (KeyError, TypeError, ValueError):
            continue
        if app_id in seen or steam_uah is None or steam_uah <= 0:
            continue
        seen.add(app_id)
        games_considered += 1
        deal = find_best_uah_offer(steam_uah, offers_by_app_id.get(app_id, ()), denominations)
        if deal is None or not deal.offer.url:
            continue
        routes.append(
            UAHGameRoute(
                app_id=app_id,
                title=str(raw.get("title") or "Unknown game"),
                steam_price_uah=deal.steam_price_uah,
                required_card_uah=deal.required_card_uah,
                total_cost=deal.total_cost,
                seller=deal.offer.seller,
                url=deal.offer.url,
            )
        )

    total = sum((route.total_cost for route in routes), Decimal("0"))
    return UAHRouteSummary(
        routes=tuple(routes),
        total_cost=total,
        games_considered=games_considered,
        games_with_verified_route=len(routes),
    )
