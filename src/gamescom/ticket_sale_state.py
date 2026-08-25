from __future__ import annotations

import json
from pathlib import Path

STATE_PATH = Path("data/state/gamescom_ticket_sale.json")


def load_notified(*, path: Path = STATE_PATH) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(data.get("notified", False)) if isinstance(data, dict) else False


def mark_notified(*, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"notified": True}, indent=2), encoding="utf-8")
