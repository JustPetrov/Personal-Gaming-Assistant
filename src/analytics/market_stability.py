from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean


@dataclass(frozen=True)
class MarketPoint:
    timestamp: datetime
    price: float
    category: str


@dataclass(frozen=True)
class StabilityResult:
    active: bool
    average_price: float | None
    reason: str


def evaluate_instability(points: list[MarketPoint], *, days: int = 14, explosive_ratio: float = 1.20) -> StabilityResult:
    """Require a full rolling window before declaring an explosive market state."""
    if not points:
        return StabilityResult(False, None, "No market data")
    cutoff = max(p.timestamp for p in points) - timedelta(days=days)
    window = [p for p in points if p.timestamp >= cutoff]
    if not window or min(p.timestamp for p in window) > cutoff:
        return StabilityResult(False, mean(p.price for p in window), "Insufficient 14-day history")
    baseline = min(p.price for p in window)
    average = mean(p.price for p in window)
    active = baseline > 0 and average / baseline >= explosive_ratio
    return StabilityResult(active, average, f"14-day average/min ratio={average / baseline:.2f}" if baseline else "Invalid baseline")


def rammegedon(points: list[MarketPoint]) -> StabilityResult:
    return evaluate_instability(points)


def gpu_doomsday(points: list[MarketPoint]) -> StabilityResult:
    return evaluate_instability(points)
