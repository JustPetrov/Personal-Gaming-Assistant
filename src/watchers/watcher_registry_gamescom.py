from __future__ import annotations

import os
from collections.abc import Callable, Iterable

from .gamescom_registry_watchers import GamesComAnnouncementStatus, GamesComTicketSnapshot, announcement_observations, ticket_alerts
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
    # Live provider parsing is deliberately kept behind this boundary.
    # Unknown status must not become a false positive.
    return announcement_observations(GamesComAnnouncementStatus(
        ticket_sales_started=False,
        epix_started=False,
        ticket_sales_url=os.getenv("GAMESCOM_TICKET_URL", "https://tickets.gamescom.global/"),
        epix_url=os.getenv("GAMESCOM_EPIX_URL", "https://www.gamescom.global/en/epix/quests"),
    ))


def _ticket_stock_fetcher() -> Iterable[dict]:
    """Adapter hook for live ticket-stock results."""
    # The live ticket client should supply GamesComTicketSnapshot here.
    # Returning no observations is safer than inventing stock.
    return ()


def _hotel_recommendation_fetcher() -> Iterable[dict]:
    """Convert live hotel recommendation results into watcher observations."""
    # Provider-specific hotel fetching supplies HotelRecommendation objects.
    # No fake hotel/price data is generated when the provider is unavailable.
    offers: list[HotelRecommendation] = []
    best, cheaper = rank_hotels(offers)
    for category, offer in (("Beste prijs/kwaliteit", best), ("Goedkoper alternatief", cheaper)):
        if offer is None:
            continue
        yield {
            "product": offer.name,
            "platform": "GamesCom Hotel",
            "category": category,
            "price": str(offer.price_per_night) if offer.price_per_night is not None else None,
            "rating": offer.rating,
            "distance_to_koelnmesse_m": offer.distance_to_koelnmesse_m,
            "location": offer.location,
            "url": offer.url,
            "source": "live hotel provider",
        }
