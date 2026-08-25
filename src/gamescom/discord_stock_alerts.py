from __future__ import annotations

from gamescom.stock_monitor import monitor_stock


def collect_discord_stock_alerts(statuses: list[dict]) -> list[str]:
    """Return only newly changed GamesCom stock messages for Discord delivery."""
    return [alert.message for alert in monitor_stock(statuses)]
