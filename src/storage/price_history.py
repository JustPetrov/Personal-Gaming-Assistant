from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path


@dataclass(frozen=True)
class PriceSnapshot:
    item_id: str
    price: float
    currency: str
    stock: str | None
    source: str
    url: str | None
    timestamp: str
    category: str


class PriceHistory:
    """Append-only price history used by market analytics and watchers."""

    def __init__(self, path: str = "data/state/price_history.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, snapshots: list[PriceSnapshot]) -> None:
        rows = self._load()
        rows.extend(asdict(item) for item in snapshots)
        self.path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    def recent(self, item_id: str, days: int = 14) -> list[PriceSnapshot]:
        rows = self._load()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result: list[PriceSnapshot] = []
        for row in rows:
            if row.get("item_id") != item_id:
                continue
            try:
                timestamp = datetime.fromisoformat(row["timestamp"])
            except (KeyError, ValueError):
                continue
            if timestamp >= cutoff:
                result.append(PriceSnapshot(**row))
        return result

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (OSError, json.JSONDecodeError):
            return []
