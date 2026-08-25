from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path


class JsonHistory:
    """Backward-compatible JSON history API for the storage package."""

    def __init__(self, path: str = "data/history.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return value if isinstance(value, list) else []

    def append(self, item) -> None:
        rows = self.load()
        value = asdict(item) if is_dataclass(item) else item
        value = self._json_safe(value)
        rows.append(value)
        self.path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def for_date(self, day: str, *, timestamp_fields: tuple[str, ...] = ("checked_at", "timestamp", "created_at")) -> list[dict]:
        """Return history observations whose timestamp falls on the given ISO date."""
        result: list[dict] = []
        for row in self.load():
            if not isinstance(row, dict):
                continue
            for field in timestamp_fields:
                raw = row.get(field)
                if not raw:
                    continue
                try:
                    timestamp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                except ValueError:
                    continue
                if timestamp.astimezone(timezone.utc).date().isoformat() == day:
                    result.append(row)
                    break
        return result

    @staticmethod
    def _json_safe(value):
        if isinstance(value, dict):
            return {k: JsonHistory._json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [JsonHistory._json_safe(v) for v in value]
        if isinstance(value, datetime):
            return value.isoformat()
        return value


__all__ = ["JsonHistory"]
