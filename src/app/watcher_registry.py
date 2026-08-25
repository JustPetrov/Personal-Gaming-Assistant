from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime, timezone
import os

from watchers.price_models import PriceObservation
from config.game_price_watchlist import load_game_watchlist

WatcherFetcher = Callable[[], Iterable[PriceObservation]]


def get_fetchers() -> tuple[WatcherFetcher, ...]:
    """Return enabled live watchers, including GamesCom/EPIX monitoring."""
    fetchers: list[WatcherFetcher] = []

    steam_ids = load_game_watchlist()
    if steam_ids:
        from watchers.steamdb_adapter import SteamDBAdapter

        def steam_price_fetcher() -> Iterable[PriceObservation]:
            adapter = SteamDBAdapter(steam_ids)
            try:
                yield from adapter.fetch()
            finally:
                adapter.close()

        fetchers.append(steam_price_fetcher)

    if os.getenv("WISHLIST_WATCH_ENABLED", "true").lower() == "true":
        from watchers.wishlist_adapter import WishlistWatcherAdapter
        fetchers.append(WishlistWatcherAdapter().fetch)

    ps_urls = _csv("PS_STORE_URLS")
    if ps_urls:
        from watchers.ps_store_adapter import PlayStationStoreAdapter

        def ps_store_price_fetcher() -> Iterable[PriceObservation]:
            adapter = PlayStationStoreAdapter(ps_urls)
            try:
                yield from adapter.fetch()
            finally:
                adapter.close()

        fetchers.append(ps_store_price_fetcher)

    hardware_queries = _csv("HARDWARE_WATCH_QUERIES")
    if hardware_queries:
        from watchers.hardware_retailer_adapter import HardwareRetailerAdapter
        fetchers.append(HardwareRetailerAdapter(hardware_queries).fetch)

    tweakers_urls = _csv("TWEAKERS_PRICE_HISTORY_URLS")
    if tweakers_urls:
        from watchers.tweakers_price_history import TweakersPriceHistoryClient

        def tweakers_price_fetcher() -> Iterable[PriceObservation]:
            for point in TweakersPriceHistoryClient(tweakers_urls).fetch():
                yield PriceObservation(
                    product=point.product,
                    platform="Tweakers",
                    edition=None,
                    price=point.price,
                    currency=point.currency,
                    stock=None,
                    url=point.url,
                    source=point.source,
                    checked_at=point.checked_at,
                )

        fetchers.append(tweakers_price_fetcher)

    if os.getenv("DISCORD_PRICE_WATCH_ENABLED", "false").lower() == "true":
        from watchers.discord_price_adapter import DiscordPriceAdapter
        fetchers.append(DiscordPriceAdapter().fetch)

    if os.getenv("EPIX_WATCH_ENABLED", "true").lower() == "true":
        from watchers.gamescom_registry_adapters import epix_quest_fetcher
        fetchers.append(epix_quest_fetcher)

    if os.getenv("GAMESCOM_TICKET_WATCH_ENABLED", "true").lower() == "true":
        from watchers.gamescom_ticket_live import GamesComTicketLiveClient

        def gamescom_ticket_fetcher() -> Iterable[PriceObservation]:
            client = GamesComTicketLiveClient()
            try:
                for status in client.fetch_statuses():
                    yield PriceObservation(
                        product=f"GamesCom Ticket {status.day}",
                        platform="gamescom",
                        edition="Evening" if status.evening_available and not status.regular_available else "Regular",
                        price=None,
                        currency=None,
                        stock=status.stock.value,
                        url=status.url,
                        source="gamescom official ticket shop",
                        checked_at=datetime.now(timezone.utc),
                    )
            finally:
                client.close()

        fetchers.append(gamescom_ticket_fetcher)

    return tuple(fetchers)


def _csv(name: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, "").split(",") if item.strip())
