from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date
import os

from .gamescom_hotel_live import GamesComHotelLiveClient, HotelOffer
from .gamescom_registry_watchers import (
    GamesComAnnouncementStatus,
    GamesComTicketSnapshot,
    announcement_observations,
    ticket_alerts,
)
from .gamescom_hotel_recommendations import HotelRecommendation, rank_hotels


def get_gamescom_fetchers() -> tuple[Callable[[], Iterable[dict]], ...]:
    """Return GamesCom live fetchers enabled by configuration."""
    fetchers: list[Callable[[], Iterable[dict]]] = []

    if os.getenv("GAMESCOM_ANNOUNCEMENT_WATCH_ENABLED", "true").lower() == "true":
        fetchers.append(_announcement_fetcher)
    if os.getenv("GAMESCOM_TICKET_STOCK_WATCH_ENABLED", "true").lower() == "true":
        fetchers.append(_ticket_stock_fetcher)
    if os.getenv("GAMESCOM_HOTEL_WATCH_ENABLED", "true").lower() == "true":
        fetchers.append(_hotel_recommendation_fetcher)
    return tuple(fetchers)


def _announcement_fetcher() -> Iterable[dict]:
    """Adapter hook for the live GamesCom announcement client."""
    return announcement_observations(GamesComAnnouncementStatus(
        ticket_sales_started=False,
        epix_started=False,
        ticket_sales_url=os.getenv("GAMESCOM_TICKET_URL", "https://tickets.gamescom.global/"),
        epix_url=os.getenv("GAMESCOM_EPIX_URL", "https://www.gamescom.global/en/epix/quests"),
    ))


def _ticket_stock_fetcher() -> Iterable[dict]:
    """Adapter hook for live ticket-stock results."""
    # The dedicated ticket client is handled by app.monitoring_cycle.
    return ()


def _hotel_check_dates() -> tuple[date, date] | None:
    """Read explicit hotel dates; never guess travel dates."""
    check_in_raw = os.getenv("GAMESCOM_HOTEL_CHECK_IN", "").strip()
    check_out_raw = os.getenv("GAMESCOM_HOTEL_CHECK_OUT", "").strip()
    if not check_in_raw or not check_out_raw:
        return None
    try:
        check_in = date.fromisoformat(check_in_raw)
        check_out = date.fromisoformat(check_out_raw)
    except ValueError:
        return None
    if check_out <= check_in:
        return None
    return check_in, check_out


def _hotel_to_recommendation(offer: HotelOffer) -> HotelRecommendation:
    """Normalize a live offer into the shared recommendation model."""
    from decimal import Decimal, InvalidOperation

    price: Decimal | None = None
    if offer.price:
        try:
            raw = offer.price.replace("€", "").replace(" ", "").replace(".", "").replace(",", ".")
            price = Decimal(raw)
        except (InvalidOperation, ValueError):
            price = None

    return HotelRecommendation(
        name=offer.hotel,
        category="Live hotel offer",
        price_per_night=price,
        rating=None,
        distance_to_koelnmesse_m=None,
        url=offer.url,
        reason=f"{offer.source}; availability={offer.availability}; nights={offer.nights}",
        location=None,
    )


def _hotel_recommendation_fetcher() -> Iterable[dict]:
    """Fetch configured live hotel sources and emit verified observations."""
    dates = _hotel_check_dates()
    if dates is None:
        return ()

    check_in, check_out = dates
    offers: list[HotelOffer] = []
    clients = GamesComHotelLiveClient.configured_clients()
    for client in clients:
        try:
            offers.extend(client.fetch(check_in, check_out))
        except Exception:
            # A broken provider must not suppress other providers or create fake data.
            continue

    recommendations = [_hotel_to_recommendation(offer) for offer in offers]
    best, cheaper = rank_hotels(recommendations)

    selected: list[tuple[str, HotelRecommendation]] = []
    if best is not None:
        selected.append(("Beste prijs/kwaliteit", best))
    if cheaper is not None and (best is None or cheaper.name != best.name):
        selected.append(("Goedkoper alternatief", cheaper))

    # When ranking cannot score a live offer yet, retain every verified offer
    # rather than returning an empty result.
    if not selected:
        selected = [("Live hotel offer", item) for item in recommendations if item.url]

    for category, offer in selected:
        raw_offer = next((item for item in offers if item.hotel == offer.name and item.url == offer.url), None)
        yield {
            "type": "gamescom_hotel_offer",
            "product": offer.name,
            "platform": "GamesCom Hotel",
            "category": category,
            "price": str(offer.price_per_night) if offer.price_per_night is not None else None,
            "price_per_night": str(offer.price_per_night) if offer.price_per_night is not None else None,
            "total_price": str(raw_offer.total_price) if raw_offer and raw_offer.total_price is not None else None,
            "nights": raw_offer.nights if raw_offer else (check_out - check_in).days,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "rating": offer.rating,
            "distance_to_koelnmesse_m": offer.distance_to_koelnmesse_m,
            "availability": raw_offer.availability if raw_offer else "Unknown",
            "location": offer.location,
            "url": offer.url,
            "source": raw_offer.source if raw_offer else "live hotel provider",
            "reason": offer.reason,
        }
