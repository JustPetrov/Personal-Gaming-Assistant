from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from watchers.price_models import PriceObservation


class ObservationStore:
    """Persistent watcher snapshots, partitioned by watcher scope.

    Each watcher gets its own snapshot inside one JSON file. This prevents a
    five-minute cycle from overwriting the previous watcher's state.
    """

    def __init__(self, path: str | Path = "data/state/price_observations.json"):
        self.path = Path(path)

    def load(self, scope: str = "default") -> list[PriceObservation]:
        payload = self._load_payload()
        scopes = payload.get("scopes")
        if isinstance(scopes, dict):
            return [self._from_dict(item) for item in scopes.get(scope, [])]

        # Backwards compatibility with the original single-snapshot format.
        return [self._from_dict(item) for item in payload.get("observations", [])]

    def save(self, observations: list[PriceObservation], scope: str = "default") -> None:
        payload = self._load_payload()
        scopes = payload.get("scopes")
        if not isinstance(scopes, dict):
            legacy = payload.get("observations", [])
            scopes = {"default": legacy} if legacy else {}

        scopes[scope] = [self._to_dict(item) for item in observations]
        output = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "scopes": scopes,
        }

        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic replace prevents a VPS restart/write interruption from leaving
        # a partially written snapshot behind.
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as temp:
            json.dump(output, temp, ensure_ascii=False, indent=2)
            temp.write("\n")
            temp_path = Path(temp.name)
        temp_path.replace(self.path)

    def _load_payload(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _to_dict(observation: PriceObservation) -> dict:
        data = asdict(observation)
        data["checked_at"] = observation.checked_at.isoformat()
        return data

    @staticmethod
    def _from_dict(data: dict) -> PriceObservation:
        checked_at = datetime.fromisoformat(data["checked_at"])
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=timezone.utc)
        return PriceObservation(
            product=data["product"],
            platform=data["platform"],
            edition=data.get("edition"),
            price=data.get("price"),
            currency=data.get("currency"),
            stock=data.get("stock"),
            url=data.get("url"),
            source=data["source"],
            checked_at=checked_at,
        )
