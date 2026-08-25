from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from zoneinfo import ZoneInfo

from watchers.retailers import RetailerSearchClient, RETAILER_SEARCH_URLS
from watchers.price_models import PriceObservation


class RetailerAggregator:
    """Run the configured hardware retailers and normalize their results."""

    def __init__(self):
        self.client = RetailerSearchClient()

    def close(self):
        self.client.close()

    def search_all(self, query: str) -> list[PriceObservation]:
        checked_at = datetime.now(ZoneInfo("Europe/Amsterdam"))
        results: list[PriceObservation] = []
        for retailer in RETAILER_SEARCH_URLS:
            try:
                result = self.client.search(retailer, query)
                results.append(PriceObservation(
                    product=query,
                    platform="Hardware",
                    edition=None,
                    price=result.price,
                    currency="EUR" if result.price else None,
                    stock=result.stock,
                    url=result.url,
                    source=result.source,
                    checked_at=checked_at,
                ))
            except Exception as exc:
                # A blocked/unavailable retailer must not break the complete update.
                print(f"Retailer error ({retailer}): {exc}")
        return results
