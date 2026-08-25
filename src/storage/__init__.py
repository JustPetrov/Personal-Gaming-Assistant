from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path


class JsonHistory:
    """Backward-compatible JSON history API for the storage package."""

    def __init__(self, path: str = "data/history.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def append(self, item) -> None:
        rows = self.load()
        value = asdict(item) if is_dataclass(item) else item
        value = self._json_safe(value)
        rows.append(value)
        self.path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

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
