from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from storage.price_history import PriceHistory, PriceSnapshot


def persist_price_observations(observations: list[dict[str, Any]], history: PriceHistory | None = None) -> int:
    """Persist valid price observations from one watcher cycle."""
    history = history or PriceHistory()
    snapshots: list[PriceSnapshot] = []
    now = datetime.now(timezone.utc).isoformat()
    for item in observations:
        price = item.get("price")
        if price is None:
            continue
        try:
            numeric_price = float(str(price).replace("€", "").replace(",", ".").strip())
        except ValueError:
            continue
        currency = str(item.get("currency") or "EUR")
        snapshots.append(PriceSnapshot(
            item_id=str(item.get("id") or item.get("product") or item.get("title") or "unknown"),
            price=numeric_price,
            currency=currency,
            stock=item.get("stock"),
            source=str(item.get("source") or "unknown"),
            url=item.get("url"),
            timestamp=now,
            category=str(item.get("category") or item.get("platform") or "unknown"),
        ))
    history.append(snapshots)
    return len(snapshots)
