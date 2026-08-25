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
    """Run a watcher against a persistent snapshot scope."""

    def __init__(self, store: ObservationStore):
        self.store = store

    @staticmethod
    def scope_for(fetcher: Callable[[], Iterable[PriceObservation]]) -> str:
        """Return a stable scope for an explicitly identified watcher callable."""
        module = getattr(fetcher, "__module__", "unknown")
        name = getattr(fetcher, "__qualname__", getattr(fetcher, "__name__", "unknown"))
        return f"{module}:{name}"

    def run(
        self,
        fetcher: Callable[[], Iterable[PriceObservation]],
        *,
        scope: str | None = None,
    ) -> WatcherRunResult:
        """Run a fetcher against a stable snapshot.

        Without an explicit scope, runs intentionally share ``default`` so a
        sequence of callback objects can represent successive observations of
        one logical watcher. Production callers that need independent watcher
        state should provide an explicit ``scope``.
        """
        watcher_scope = scope or "default"
        previous = self.store.load(watcher_scope)
        current = normalize_observations(fetcher())
        changes = reportable_changes(compare_observations(previous, current))
        self.store.save(current, watcher_scope)
        return WatcherRunResult(current=current, changes=changes)
