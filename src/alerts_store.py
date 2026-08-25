from __future__ import annotations

from pathlib import Path
import json

from alerts import detect_price_changes

DATA = Path("data")


def update_alert_state(current: list[dict]) -> list[dict]:
    DATA.mkdir(parents=True, exist_ok=True)
    previous_path = DATA / "prices_previous.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else []
    changes = detect_price_changes(previous, current)
    alerts = [
        {
            "kind": c.kind,
            "item": c.item,
            "before": c.before,
            "after": c.after,
            "url": c.url,
            "source": c.source,
        }
        for c in changes
    ]
    (DATA / "alerts.json").write_text(json.dumps(alerts, ensure_ascii=False, indent=2), encoding="utf-8")
    previous_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    return alerts
