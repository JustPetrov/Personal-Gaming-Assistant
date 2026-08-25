from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from storage.observation_store import ObservationStore
from watchers.watcher_pipeline import WatcherPipeline


def run_cycle() -> None:
    """Run one five-minute monitoring cycle.

    Watchers are loaded from the registry when available. A missing/empty
    registry is deliberately a no-op so the GitHub Actions job remains safe
    while individual live adapters are being enabled.
    """
    registry_path = Path("src/app/watcher_registry.py")
    if not registry_path.exists():
        print("Watcher registry not configured; nothing to run.")
        return

    from app.watcher_registry import get_fetchers

    fetchers = tuple(get_fetchers())
    if not fetchers:
        print("No watchers registered; nothing to run.")
        return

    store = ObservationStore("data/state/price_observations.json")
    pipeline = WatcherPipeline(store)
    changed = 0
    for fetcher in fetchers:
        result = pipeline.run(fetcher)
        changed += len(result.changes)

    print(f"Watcher cycle completed at {datetime.now(timezone.utc).isoformat()}; changes={changed}")


if __name__ == "__main__":
    run_cycle()
