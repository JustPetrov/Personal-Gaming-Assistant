from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date
import os

from .gamescom_hotel_live import GamesComHotelLiveClient, HotelOffer
from .gamescom_registry_watchers import GamesComAnnouncementStatus, announcement_observations
from .gamescom_hotel_recommendations import HotelRecommendation, rank_hotels
from .gamescom_ticket_live import GamesComTicketLiveClient
from .gamescom_ticket_stock import TicketStatus
from storage.hotel_history import append_hotel_observations


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
    return announcement_observations(GamesComAnnouncementStatus(
        ticket_sales_started=False,
        epix_started=False,
        ticket_sales_url=os.getenv("GAMESCOM_TICKET_URL", "https://tickets.gamescom.global/"),
        epix_url=os.getenv("GAMESCOM_EPIX_URL", "https://www.gamescom.global/en/epix/quests"),
    ))


def _ticket_stock_fetcher() -> Iterable[dict]:
    client = GamesComTicketLiveClient()
    try:
        statuses: list[TicketStatus] = client.fetch_statuses()
        for status in statuses:
            yield {
                "type": "gamescom_ticket_status",
                "product": f"GamesCom Ticket {status.day}",
                "platform": "gamescom",
                "edition": "Evening" if status.evening_available and not status.regular_available else "Regular",
                "price": None,
                "currency": None,
                "stock": status.stock.value,
                "regular_available": status.regular_available,
                "evening_available": status.evening_available,
                "url": status.url,
                "source": "gamescom official ticket shop",
                "day": status.day,
            }
    finally:
        client.close()


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
        nights=offer.nights,
        total_price=offer.total_price,
    )


def _hotel_recommendation_fetcher() -> Iterable[dict]:
    """Fetch configured live hotel sources and emit verified observations."""
    dates = _hotel_check_dates()
    if dates is None:
        return ()

    check_in, check_out = dates
    offers: list[HotelOffer] = []
    for client in GamesComHotelLiveClient.configured_clients():
        try:
            offers.extend(client.fetch(check_in, check_out))
        except Exception:
            continue

    recommendations = [_hotel_to_recommendation(offer) for offer in offers]
    best, cheaper = rank_hotels(recommendations)
    selected: list[tuple[str, HotelRecommendation]] = []
    if best is not None:
        selected.append(("Beste prijs/kwaliteit", best))
    if cheaper is not None and (best is None or cheaper.name != best.name):
        selected.append(("Goedkoper alternatief", cheaper))
    if not selected:
        selected = [("Live hotel offer", item) for item in recommendations if item.url]

    output: list[dict] = []
    for category, offer in selected:
        raw_offer = next((item for item in offers if item.hotel == offer.name and item.url == offer.url), None)
        output.append({
            "type": "gamescom_hotel_offer",
            "product": offer.name,
            "platform": "GamesCom Hotel",
            "category": category,
            "price": str(offer.price_per_night) if offer.price_per_night is not None else None,
            "price_per_night": str(offer.price_per_night) if offer.price_per_night is not None else None,
            "total_price": str(raw_offer.total_price) if raw_offer and raw_offer.total_price is not None else None,
            "currency": raw_offer.currency if raw_offer else ("EUR" if offer.price_per_night is not None else None),
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
        })

    append_hotel_observations(output)
    yield from output
