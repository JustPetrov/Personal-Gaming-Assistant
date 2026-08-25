from __future__ import annotations

import json
import os
from pathlib import Path


def load_game_watchlist(path: str = "data/config/game_price_watchlist.json") -> tuple[int, ...]:
    """Load only explicitly saved Steam App IDs; never discover games implicitly."""
    configured = os.getenv("GAME_PRICE_WATCH_APP_IDS", "")
    if configured.strip():
        return _parse_csv(configured)

    file = Path(path)
    if not file.exists():
        return ()
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    values = data.get("app_ids", []) if isinstance(data, dict) else data
    return tuple(int(value) for value in values if str(value).isdigit())


def _parse_csv(value: str) -> tuple[int, ...]:
    result: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if item.isdigit():
            result.append(int(item))
    return tuple(dict.fromkeys(result))
