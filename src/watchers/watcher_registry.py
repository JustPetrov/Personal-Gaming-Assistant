from __future__ import annotations

from watchers.retailer_aggregator import RetailerAggregator


class WatcherRegistry:
    def __init__(self):
        self.retailers = RetailerAggregator()

    def hardware_prices(self, products: list[str]):
        rows = []
        for product in products:
            rows.extend(self.retailers.search_all(product))
        return rows

    def close(self):
        self.retailers.close()
