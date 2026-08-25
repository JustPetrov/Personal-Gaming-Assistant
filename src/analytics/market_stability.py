from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean


RAM_SEGMENTS = ("32GB", "48GB", "64GB", "96GB")


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


@dataclass(frozen=True)
class MultiSegmentResult:
    active: bool
    segments: dict[str, StabilityResult]
    reason: str


def evaluate_instability(
    points: list[MarketPoint],
    *,
    days: int = 14,
    explosive_ratio: float = 1.20,
) -> StabilityResult:
    """Require a full rolling window before declaring an explosive market state."""
    if not points:
        return StabilityResult(False, None, "No market data")
    cutoff = max(p.timestamp for p in points) - timedelta(days=days)
    window = [p for p in points if p.timestamp >= cutoff]
    if not window or min(p.timestamp for p in window) > cutoff:
        return StabilityResult(False, mean(p.price for p in window) if window else None, "Insufficient 14-day history")
    baseline = min(p.price for p in window)
    average = mean(p.price for p in window)
    active = baseline > 0 and average / baseline >= explosive_ratio
    return StabilityResult(active, average, f"14-day average/min ratio={average / baseline:.2f}" if baseline else "Invalid baseline")


def evaluate_required_segments(
    points: list[MarketPoint],
    required_categories: tuple[str, ...],
    *,
    days: int = 14,
    explosive_ratio: float = 1.15,
) -> MultiSegmentResult:
    """Require every configured segment to have a full 14-day signal."""
    results: dict[str, StabilityResult] = {}
    for category in required_categories:
        category_points = [point for point in points if point.category == category]
        results[category] = evaluate_instability(
            category_points,
            days=days,
            explosive_ratio=explosive_ratio,
        )

    missing = [category for category, result in results.items() if result.average_price is None]
    if missing:
        return MultiSegmentResult(False, results, f"Missing market history: {', '.join(missing)}")
    inactive = [category for category, result in results.items() if not result.active]
    if inactive:
        return MultiSegmentResult(False, results, f"Segments below threshold: {', '.join(inactive)}")
    return MultiSegmentResult(True, results, "All required market segments meet the stability threshold")


def rammegedon(points: list[MarketPoint]) -> StabilityResult:
    return evaluate_instability(points)


def rammegedon_segments(points: list[MarketPoint], segments: tuple[str, ...] = RAM_SEGMENTS) -> MultiSegmentResult:
    return evaluate_required_segments(points, segments)


def gpu_doomsday(points: list[MarketPoint]) -> StabilityResult:
    return evaluate_instability(points)


def gpu_doomsday_segments(points: list[MarketPoint], required_categories: tuple[str, ...]) -> MultiSegmentResult:
    return evaluate_required_segments(points, required_categories)
