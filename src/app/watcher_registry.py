from __future__ import annotations

from collections.abc import Callable, Iterable
import os

from watchers.price_models import PriceObservation

WatcherFetcher = Callable[[], Iterable[PriceObservation]]


def get_fetchers() -> tuple[WatcherFetcher, ...]:
    """Return enabled live watchers, including GamesCom/EPIX monitoring."""
    fetchers: list[WatcherFetcher] = []

    steam_ids = _csv_ints("STEAM_APP_IDS")
    if steam_ids:
        from watchers.steamdb_adapter import SteamDBAdapter
        fetchers.append(SteamDBAdapter(steam_ids).fetch)

    ps_urls = _csv("PS_STORE_URLS")
    if ps_urls:
        from watchers.ps_store_adapter import PlayStationStoreAdapter
        fetchers.append(PlayStationStoreAdapter(ps_urls).fetch)

    hardware_queries = _csv("HARDWARE_WATCH_QUERIES")
    if hardware_queries:
        from watchers.hardware_retailer_adapter import HardwareRetailerAdapter
        fetchers.append(HardwareRetailerAdapter(hardware_queries).fetch)

    if os.getenv("DISCORD_PRICE_WATCH_ENABLED", "false").lower() == "true":
        from watchers.discord_price_adapter import DiscordPriceAdapter
        fetchers.append(DiscordPriceAdapter().fetch)

    if os.getenv("EPIX_WATCH_ENABLED", "true").lower() == "true":
        from watchers.gamescom_registry_adapters import epix_quest_fetcher
        fetchers.append(epix_quest_fetcher)

    return tuple(fetchers)


def _csv(name: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, "").split(",") if item.strip())


def _csv_ints(name: str) -> tuple[int, ...]:
    values: list[int] = []
    for item in _csv(name):
        try:
            values.append(int(item))
        except ValueError:
            continue
    return tuple(values)
