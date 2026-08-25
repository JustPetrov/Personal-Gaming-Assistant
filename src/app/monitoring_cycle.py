from __future__ import annotations

from datetime import datetime, timezone

from app.watcher_registry import get_fetchers
from storage.change_detection import ChangeDetector
from watchers.watcher_registry_gamescom import get_gamescom_fetchers


def collect_observations() -> list[dict]:
    """Collect every enabled watcher result for one monitoring cycle."""
    observations: list[dict] = []
    for fetcher in (*get_fetchers(), *get_gamescom_fetchers()):
        try:
            observations.extend(dict(item) for item in fetcher())
        except Exception as exc:
            observations.append({
                "type": "watcher_error",
                "source": getattr(fetcher, "__name__", "unknown"),
                "error": str(exc),
            })
    return observations


def run_monitoring_cycle() -> list[dict]:
    """Collect observations and return only new/changed facts."""
    started = datetime.now(timezone.utc).isoformat()
    observations = collect_observations()
    changed = ChangeDetector().process(observations)
    print(
        f"Monitoring cycle started={started} "
        f"observations={len(observations)} changes={len(changed)}"
    )
    return changed


if __name__ == "__main__":
    run_monitoring_cycle()
