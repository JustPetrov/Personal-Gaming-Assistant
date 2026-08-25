from __future__ import annotations

from collections.abc import Iterable

from .price_models import PriceObservation
from .price_observations import observation_from_values
from .steamdb import SteamDBClient


class SteamDBAdapter:
    """Adapt configured Steam app IDs into the common watcher observation model."""

    def __init__(self, app_ids: Iterable[int], client: SteamDBClient | None = None):
        self.app_ids = tuple(app_ids)
        self.client = client or SteamDBClient()
        self._owns_client = client is None

    def fetch(self) -> list[PriceObservation]:
        observations: list[PriceObservation] = []
        for app_id in self.app_ids:
            price = self.client.get_price(app_id)
            observations.append(observation_from_values(
                product=price.name,
                platform="Steam",
                edition=None,
                price=price.eur,
                currency="EUR" if price.eur else None,
                stock="Available" if price.eur or price.uah else "Unavailable",
                url=price.url,
                source="SteamDB",
            ))
            # EUR and UAH are stored as separate observations so the change
            # detector can report a regional currency change independently.
            if price.uah:
                observations.append(observation_from_values(
                    product=price.name,
                    platform="Steam",
                    edition="UAH",
                    price=price.uah,
                    currency="UAH",
                    stock="Available",
                    url=price.url,
                    source="SteamDB",
                ))
        return observations

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
