from __future__ import annotations

from collections.abc import Iterable

from .price_models import PriceObservation
from .price_observations import observation_from_values
from .retailers import RetailerSearchClient, RETAILER_SEARCH_URLS


RETAILERS = tuple(RETAILER_SEARCH_URLS)


class HardwareRetailerAdapter:
    """Run the configured Dutch hardware retailers through the common model."""

    def __init__(self, queries: Iterable[str], client: RetailerSearchClient | None = None):
        self.queries = tuple(queries)
        self.client = client or RetailerSearchClient()
        self._owns_client = client is None

    def fetch(self) -> list[PriceObservation]:
        observations: list[PriceObservation] = []
        for query in self.queries:
            for retailer in RETAILERS:
                result = self.client.search(retailer, query)
                observations.append(observation_from_values(
                    product=query,
                    platform="Hardware",
                    edition=retailer,
                    price=result.price,
                    currency="EUR" if result.price else None,
                    stock=result.stock,
                    url=result.url,
                    source=retailer,
                ))
        return observations

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
