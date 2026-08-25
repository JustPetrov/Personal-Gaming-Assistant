from __future__ import annotations

from gamescom.stock_alerts import StockAlert, build_stock_alerts
from gamescom.stock_state import StockState, changed_stock_states


def monitor_stock(statuses: list[dict]) -> list[StockAlert]:
    """Convert live ticket statuses into deduplicated actionable alerts."""
    alerts = build_stock_alerts(statuses)
    states = [
        StockState(alert.day, alert.ticket_type, alert.status.value)
        for alert in alerts
    ]
    changed = changed_stock_states(states)
    changed_keys = {(item.day, item.ticket_type, item.status) for item in changed}
    return [
        alert for alert in alerts
        if (alert.day, alert.ticket_type, alert.status.value) in changed_keys
    ]
