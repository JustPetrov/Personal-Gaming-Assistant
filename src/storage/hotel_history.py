from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any


DEFAULT_PATH = Path("data/state/hotel_history.json")


def append_hotel_observations(
    observations: list[dict[str, Any]],
    path: Path = DEFAULT_PATH,
) -> None:
    """Persist verified hotel observations for historical price comparisons."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    except (OSError, json.JSONDecodeError):
        existing = []
    if not isinstance(existing, list):
        existing = []

    checked_at = datetime.now(timezone.utc).isoformat()
    for item in observations:
        if not item.get("url"):
            continue
        existing.append({
            "checked_at": checked_at,
            "hotel": item.get("product"),
            "source": item.get("source"),
            "url": item.get("url"),
            "price_per_night": item.get("price_per_night"),
            "total_price": item.get("total_price"),
            "currency": item.get("currency") or ("EUR" if item.get("price_per_night") else None),
            "availability": item.get("availability"),
            "nights": item.get("nights"),
            "check_in": item.get("check_in"),
            "check_out": item.get("check_out"),
        })

    path.write_text(json.dumps(existing[-5000:], indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def lowest_historical_price(
    hotel: str,
    *,
    path: Path = DEFAULT_PATH,
) -> Decimal | None:
    """Return the lowest recorded nightly EUR price for one hotel."""
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    values: list[Decimal] = []
    for row in rows if isinstance(rows, list) else []:
        if row.get("hotel") != hotel or row.get("price_per_night") is None:
            continue
        try:
            values.append(Decimal(str(row["price_per_night"])))
        except Exception:
            continue
    return min(values) if values else None
