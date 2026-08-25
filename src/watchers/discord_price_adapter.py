from __future__ import annotations

from collections.abc import Iterable

from .g2g import G2GClient
from .price_models import PriceObservation
from .price_observations import observation_from_values


DISCORD_OFFERS = (
    ("Server Boost", "1 month", 14),
    ("Server Boost", "3 months", 14),
    ("Nitro", "1 month", 1),
    ("Nitro", "1 year", 1),
    ("Nitro Basic", "1 month", 1),
    ("Nitro Basic", "1 year", 1),
)


class DiscordPriceAdapter:
    """Convert G2G Discord listings to normalized observations.

    A boost listing is interpreted as a per-boost price and multiplied by 14
    for the configured server size. The multiplier is never applied to Nitro.
    """

    def __init__(self, client: G2GClient | None = None):
        self.client = client or G2GClient()
        self._owns_client = client is None

    def fetch(self) -> list[PriceObservation]:
        observations: list[PriceObservation] = []
        try:
            for product, duration, multiplier in DISCORD_OFFERS:
                query = f"Discord {product} {duration}"
                for listing in self.client.search(query):
                    price = self._scaled_price(listing.price, multiplier)
                    observations.append(
                        observation_from_values(
                            product=product,
                            platform="Discord",
                            edition=duration,
                            price=price,
                            currency=listing.currency,
                            stock=listing.stock,
                            url=listing.url,
                            source="G2G",
                        )
                    )
            return observations
        finally:
            # The registry creates one adapter per monitoring cycle. Close
            # adapter-owned HTTP/session resources after every cycle.
            self.close()

    @staticmethod
    def _scaled_price(price: str | None, multiplier: int) -> str | None:
        if not price or multiplier == 1:
            return price
        import re
        match = re.search(r"([0-9]+(?:[.,][0-9]+)?)", price)
        if not match:
            return price
        raw = match.group(1).replace(",", ".")
        value = float(raw) * multiplier
        formatted = f"{value:.2f}".replace(".", ",")
        prefix = price[:match.start(1)]
        suffix = price[match.end(1):]
        return f"{prefix}{formatted}{suffix}"

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
