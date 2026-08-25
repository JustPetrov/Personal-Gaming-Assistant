from __future__ import annotations

from typing import Any

from analytics.market_alerts import gpu_doomsday_alert, rammegedon_alert
from storage.price_history import PriceHistory


def market_alert_observations(
    history: PriceHistory,
    *,
    ram_item_ids: list[str],
    gpu_item_ids: list[str],
) -> list[dict[str, Any]]:
    """Expose data-backed market alerts to the news/Ollama layer."""
    alerts = (
        rammegedon_alert(history, ram_item_ids),
        gpu_doomsday_alert(history, gpu_item_ids),
    )
    return [
        {
            "type": "market_alert",
            "name": alert.name,
            "active": alert.active,
            "average_price": alert.average_price,
            "baseline_price": alert.baseline_price,
            "ratio": alert.ratio,
            "history_points": alert.history_points,
            "reason": alert.reason,
        }
        for alert in alerts
    ]
