from __future__ import annotations

from datetime import datetime, timezone
from collections.abc import Iterable

from app.watcher_registry import get_fetchers
from watchers.watcher_registry_gamescom import get_gamescom_fetchers


def collect_observations() -> list[dict]:
    """Collect every enabled watcher result for one monitoring cycle."""
    observations: list[dict] = []
    for fetcher in (*get_fetchers(), *get_gamescom_fetchers()):
        try:
            observations.extend(dict(item) for item in fetcher())
        except Exception as exc:  # one failing provider must not stop others
            observations.append({
                "type": "watcher_error",
                "source": getattr(fetcher, "__name__", "unknown"),
                "error": str(exc),
            })
    return observations


def run_monitoring_cycle() -> list[dict]:
    started = datetime.now(timezone.utc).isoformat()
    observations = collect_observations()
    print(f"Monitoring cycle started={started} observations={len(observations)}")
    return observations


if __name__ == "__main__":
    run_monitoring_cycle()
