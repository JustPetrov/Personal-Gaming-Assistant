from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from storage.price_history import PriceHistory


@dataclass(frozen=True)
class MarketAlert:
    name: str
    active: bool
    average_price: float | None
    baseline_price: float | None
    ratio: float | None
    history_points: int
    reason: str


def _evaluate(history: PriceHistory, item_ids: list[str], name: str, *, days: int = 14, ratio_threshold: float = 1.20) -> MarketAlert:
    prices: list[float] = []
    for item_id in item_ids:
        prices.extend(point.price for point in history.recent(item_id, days=days))
    if not prices:
        return MarketAlert(name, False, None, None, None, 0, "Geen historische prijsdata")
    average = mean(prices)
    baseline = min(prices)
    ratio = average / baseline if baseline > 0 else None
    active = len(prices) > 1 and ratio is not None and ratio >= ratio_threshold
    return MarketAlert(name, active, average, baseline, ratio, len(prices), f"14-daagse gemiddelde/minimum ratio: {ratio:.2f}" if ratio is not None else "Ongeldige basisprijs")


def rammegedon_alert(history: PriceHistory, ram_item_ids: list[str]) -> MarketAlert:
    return _evaluate(history, ram_item_ids, "Rammegedon")


def gpu_doomsday_alert(history: PriceHistory, gpu_item_ids: list[str]) -> MarketAlert:
    return _evaluate(history, gpu_item_ids, "GPU Doomsday")
