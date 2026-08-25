from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


_VOLATILE_FIELDS = {"timestamp", "checked_at", "generated_at", "observed_at"}


class ChangeDetector:
    """Persistent observation fingerprints; only meaningful changes emit."""

    def __init__(self, path: str = "data/state/observations.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state: dict[str, str] = self._load()

    def _load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _identity(observation: dict[str, Any]) -> str:
        source = str(observation.get("source") or "unknown")
        kind = str(observation.get("type") or "other")
        entity = observation.get("id") or observation.get("entity") or observation.get("product") or observation.get("title") or "unknown"
        event = str(observation.get("event") or "state")
        return "|".join((source, kind, str(entity), event))

    @classmethod
    def _fingerprint(cls, observation: dict[str, Any]) -> tuple[str, str]:
        identity = cls._identity(observation)
        stable_payload = {key: value for key, value in observation.items() if key not in _VOLATILE_FIELDS}
        payload = json.dumps(stable_payload, sort_keys=True, ensure_ascii=False, default=str)
        return identity, hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def process(self, observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        changed: list[dict[str, Any]] = []
        for observation in observations:
            if observation.get("type") == "watcher_error":
                continue
            identity, digest = self._fingerprint(observation)
            if self.state.get(identity) != digest:
                changed.append(observation)
                self.state[identity] = digest
        self.path.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")
        return changed
