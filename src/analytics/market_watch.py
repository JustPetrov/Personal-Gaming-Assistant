from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from storage.price_history import PriceHistory, PriceSnapshot


@dataclass(frozen=True)
class MarketSummary:
    category: str
    item_count: int
    average_price: float | None
    history_points: int


def summarize_history(history: PriceHistory, item_ids: list[str], *, days: int = 14) -> list[MarketSummary]:
    summaries: list[MarketSummary] = []
    for item_id in item_ids:
        points: list[PriceSnapshot] = history.recent(item_id, days=days)
        if not points:
            summaries.append(MarketSummary(item_id, 0, None, 0))
            continue
        prices = [p.price for p in points]
        category = points[-1].category
        summaries.append(MarketSummary(category, 1, mean(prices), len(points)))
    return summaries


def average_for_capacity(history: PriceHistory, item_ids: list[str], capacity_gb: int, *, days: int = 14) -> float | None:
    """Average historical price for configured RAM products of one capacity."""
    values: list[float] = []
    marker = f"{capacity_gb}GB"
    for item_id in item_ids:
        if marker.lower() not in item_id.lower():
            continue
        values.extend(point.price for point in history.recent(item_id, days=days))
    return mean(values) if values else None
