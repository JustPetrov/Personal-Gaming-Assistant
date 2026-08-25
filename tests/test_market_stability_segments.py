from datetime import datetime, timedelta, timezone

from analytics.market_stability import MarketPoint, evaluate_required_segments


def _points(category: str, multiplier: float = 1.0):
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    return [
        MarketPoint(start, 100.0 * multiplier, category),
        MarketPoint(start + timedelta(days=7), 120.0 * multiplier, category),
        MarketPoint(start + timedelta(days=14), 125.0 * multiplier, category),
    ]


def test_all_required_segments_must_have_history():
    points = _points("32GB") + _points("48GB")
    result = evaluate_required_segments(points, ("32GB", "48GB", "64GB"))
    assert result.active is False
    assert "64GB" in result.reason


def test_all_required_segments_can_activate():
    points = []
    for segment in ("32GB", "48GB", "64GB"):
        points.extend(_points(segment))
    result = evaluate_required_segments(points, ("32GB", "48GB", "64GB"))
    assert result.active is True
