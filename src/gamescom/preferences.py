from __future__ import annotations

import json
from pathlib import Path


PREFERENCES_FILE = Path("data/config/gamescom_preferences.json")


def save_preferred_day(day: str, *, path: Path = PREFERENCES_FILE) -> None:
    if day not in {"Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}:
        raise ValueError("Invalid GamesCom preferred day")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"preferred_day": day}, indent=2), encoding="utf-8")


def load_preferred_day(*, path: Path = PREFERENCES_FILE) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = data.get("preferred_day") if isinstance(data, dict) else None
    return value if value in {"Wednesday", "Thursday", "Friday", "Saturday", "Sunday"} else None
