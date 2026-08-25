from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from gamescom.stock_status import StockStatus


@dataclass(frozen=True)
class StockState:
    day: str
    ticket_type: str
    status: str


class StockStateStore:
    """Persist last seen ticket status so alerts fire only on changes."""

    def __init__(self, path: Path = Path("data/state/gamescom_stock.json")) -> None:
        self.path = path

    def load(self) -> dict[tuple[str, str], StockState]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return {
            (str(item["day"]), str(item["ticket_type"])): StockState(**item)
            for item in raw.get("states", [])
            if isinstance(item, dict) and {"day", "ticket_type", "status"} <= item.keys()
        }

    def update(self, states: list[StockState]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"states": [asdict(item) for item in states]}, indent=2),
            encoding="utf-8",
        )


def changed_stock_states(states: list[StockState], store: StockStateStore | None = None) -> list[StockState]:
    """Return only new/changed statuses and persist the current snapshot."""
    store = store or StockStateStore()
    previous = store.load()
    changed = [
        state for state in states
        if previous.get((state.day, state.ticket_type)) is None
        or previous[(state.day, state.ticket_type)].status != state.status
    ]
    store.update(states)
    return changed
