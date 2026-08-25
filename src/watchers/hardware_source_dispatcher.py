from __future__ import annotations

from collections.abc import Iterable
import os

from watchers.hardware_sources import enabled_hardware_sources
from watchers.price_models import PriceObservation


def configured_hardware_observations() -> Iterable[PriceObservation]:
    """Dispatch configured hardware source URLs through the generic retailer adapter."""
    from watchers.hardware_retailer_adapter import HardwareRetailerAdapter

    env = dict(os.environ)
    sources = enabled_hardware_sources(env)
    for source in sources:
        urls = tuple(item.strip() for item in env.get(source.url_env, "").split(",") if item.strip())
        if not urls:
            continue
        for observation in HardwareRetailerAdapter(urls).fetch():
            # Preserve the concrete source even when the generic adapter supplies a fallback.
            yield PriceObservation(
                product=observation.product,
                platform=observation.platform,
                edition=observation.edition,
                price=observation.price,
                currency=observation.currency,
                stock=observation.stock,
                url=observation.url,
                source=source.name,
                checked_at=observation.checked_at,
            )
