from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from watchers.price_models import PriceObservation


class ObservationStore:
    """Small JSON-backed snapshot store suitable for a single VPS process."""

    def __init__(self, path: str | Path = "data/state/price_observations.json"):
        self.path = Path(path)

    def load(self) -> list[PriceObservation]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [self._from_dict(item) for item in data.get("observations", [])]

    def save(self, observations: list[PriceObservation]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "observations": [self._to_dict(item) for item in observations],
        }
        # Atomic replace prevents a VPS restart/write interruption from leaving
        # a partially written snapshot behind.
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as temp:
            json.dump(payload, temp, ensure_ascii=False, indent=2)
            temp.write("\n")
            temp_path = Path(temp.name)
        temp_path.replace(self.path)

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
