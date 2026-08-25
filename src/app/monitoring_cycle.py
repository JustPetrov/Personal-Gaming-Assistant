from __future__ import annotations

from datetime import datetime, timezone

from app.watcher_registry import get_fetchers
from storage.change_detection import ChangeDetector
from storage.history_ingest import persist_price_observations
from watchers.hardware_source_dispatcher import configured_hardware_observations
from watchers.watcher_registry_gamescom import get_gamescom_fetchers
from gamescom.stock_monitor import monitor_stock
from gamescom.epix_observations import collect_epix_observations
from gamescom.discord_epix_alerts import send_epix_alerts


def _watcher_name(fetcher) -> str:
    """Return a stable human-readable watcher name for error reporting."""
    name = getattr(fetcher, "__name__", None)
    if name:
        return str(name)
    owner = getattr(fetcher, "__self__", None)
    if owner is not None:
        return f"{owner.__class__.__name__}.{getattr(fetcher, '__name__', 'fetch')}"
    return getattr(fetcher, "__qualname__", None) or "unknown"


def _watcher_error(fetcher, exc: Exception) -> dict:
    """Build a consistent, non-fatal watcher error observation."""
    return {
        "type": "watcher_error",
        "source": _watcher_name(fetcher),
        "error_type": exc.__class__.__name__,
        "error": str(exc),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def collect_observations() -> list[dict]:
    """Collect every enabled watcher result for one monitoring cycle."""
    observations: list[dict] = []
    fetchers = (*get_fetchers(), *get_gamescom_fetchers())
    for fetcher in fetchers:
        try:
            observations.extend(dict(item) for item in fetcher())
        except Exception as exc:
            observations.append(_watcher_error(fetcher, exc))

    try:
        observations.extend(dict(item) for item in configured_hardware_observations())
    except Exception as exc:
        observations.append(_watcher_error(configured_hardware_observations, exc))

    try:
        epix_observations = collect_epix_observations()
        observations.extend(epix_observations)
        if epix_observations:
            try:
                send_epix_alerts(epix_observations)
            except Exception as exc:
                observations.append(_watcher_error(send_epix_alerts, exc))
    except Exception as exc:
        observations.append(_watcher_error(collect_epix_observations, exc))

    ticket_statuses = [
        item for item in observations
        if item.get("type") == "gamescom_ticket_status"
    ]
    if ticket_statuses:
        try:
            for alert in monitor_stock(ticket_statuses):
                observations.append({
                    "type": "gamescom_stock_alert",
                    "day": alert.day,
                    "ticket_type": alert.ticket_type,
                    "status": alert.status.value,
                    "message": alert.message,
                })
        except Exception as exc:
            observations.append(_watcher_error(monitor_stock, exc))
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
