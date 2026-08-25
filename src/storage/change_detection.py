from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ChangeDetector:
    """Persistent observation fingerprints; only changed/new observations emit."""

    def __init__(self, path: str = "data/state/observations.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state: dict[str, str] = self._load()

    def _load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def _fingerprint(observation: dict[str, Any]) -> tuple[str, str]:
        identity = str(observation.get("id") or observation.get("product") or observation.get("title") or "unknown")
        payload = json.dumps(observation, sort_keys=True, ensure_ascii=False, default=str)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return identity, digest

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
