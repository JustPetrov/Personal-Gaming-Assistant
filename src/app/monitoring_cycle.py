from __future__ import annotations

from datetime import datetime, timezone

from app.watcher_registry import get_fetchers
from storage.change_detection import ChangeDetector
from storage.history_ingest import persist_price_observations
from watchers.hardware_source_dispatcher import configured_hardware_observations
from watchers.watcher_registry_gamescom import get_gamescom_fetchers
from gamescom.stock_monitor import monitor_stock


def collect_observations() -> list[dict]:
    """Collect every enabled watcher result for one monitoring cycle."""
    observations: list[dict] = []
    fetchers = (*get_fetchers(), *get_gamescom_fetchers())
    for fetcher in fetchers:
        try:
            observations.extend(dict(item) for item in fetcher())
        except Exception as exc:
            observations.append({
                "type": "watcher_error",
                "source": getattr(fetcher, "__name__", "unknown"),
                "error": str(exc),
            })

    try:
        observations.extend(dict(item) for item in configured_hardware_observations())
    except Exception as exc:
        observations.append({
            "type": "watcher_error",
            "source": "configured_hardware_observations",
            "error": str(exc),
        })

    # Ticket stock is handled as a stateful alert stream. Keep the live
    # observations in the normal payload while only emitting changed alerts.
    ticket_statuses = [
        item for item in observations
        if item.get("type") == "gamescom_ticket_status"
    ]
    if ticket_statuses:
        for alert in monitor_stock(ticket_statuses):
            observations.append({
                "type": "gamescom_stock_alert",
                "day": alert.day,
                "ticket_type": alert.ticket_type,
                "status": alert.status.value,
                "message": alert.message,
            })
    return observations


def run_monitoring_cycle() -> list[dict]:
    """Collect observations, persist price history, then emit changes."""
    started = datetime.now(timezone.utc).isoformat()
    observations = collect_observations()
    persisted = persist_price_observations(observations)
    changed = ChangeDetector().process(observations)
    print(
        f"Monitoring cycle started={started} "
        f"observations={len(observations)} prices_persisted={persisted} changes={len(changed)}"
    )
    return changed


if __name__ == "__main__":
    run_monitoring_cycle()
