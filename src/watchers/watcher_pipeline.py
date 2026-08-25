from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .change_detection import ObservationChange, compare_observations, reportable_changes
from .price_models import PriceObservation
from .price_observations import normalize_observations
from src.storage.observation_store import ObservationStore


@dataclass
class WatcherRunResult:
    current: list[PriceObservation]
    changes: list[ObservationChange]


class WatcherPipeline:
    """Run a watcher, compare it with persistent state, then save the snapshot."""

    def __init__(self, store: ObservationStore):
        self.store = store

    def run(self, fetcher: Callable[[], Iterable[PriceObservation]]) -> WatcherRunResult:
        previous = self.store.load()
        current = normalize_observations(fetcher())
        changes = reportable_changes(compare_observations(previous, current))
        self.store.save(current)
        return WatcherRunResult(current=current, changes=changes)
