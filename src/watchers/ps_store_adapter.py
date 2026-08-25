from __future__ import annotations

from collections.abc import Iterable

from .price_models import PriceObservation
from .price_observations import observation_from_values
from .ps_store import PlayStationStoreClient


class PlayStationStoreAdapter:
    """Adapt configured PlayStation Store URLs to the common observation model."""

    def __init__(self, urls: Iterable[str], client: PlayStationStoreClient | None = None):
        self.urls = tuple(urls)
        self.client = client or PlayStationStoreClient(locale="nl-nl")
        self._owns_client = client is None

    def fetch(self) -> list[PriceObservation]:
        observations: list[PriceObservation] = []
        for url in self.urls:
            listing = self.client.get_listing(url)
            observations.append(observation_from_values(
                product=listing.name,
                platform="PS5",
                edition=listing.edition,
                price=listing.price,
                currency=listing.currency,
                stock="Available" if listing.available else "Unavailable",
                url=listing.url,
                source="PlayStation Store",
            ))
        return observations

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
