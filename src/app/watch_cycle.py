from __future__ import annotations

from datetime import datetime, timezone

from app.monitoring_cycle import run_monitoring_cycle


def run_cycle() -> list[dict]:
    """Run the complete five-minute monitoring cycle.

    This is the single entry point used by the five-minute scheduler, so it
    includes normal watchers plus GamesCom, EPIX, ticket, and configured
    hardware observations handled by the unified monitoring pipeline.
    """
    changed = run_monitoring_cycle()
    print(
        f"Watcher cycle completed at {datetime.now(timezone.utc).isoformat()}; "
        f"changes={len(changed)}"
    )
    return changed


if __name__ == "__main__":
    run_cycle()
