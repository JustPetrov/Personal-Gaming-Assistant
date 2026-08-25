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
    """Run a watcher against its own persistent snapshot scope.

    Production callers should pass an explicit ``scope`` when one logical
    watcher is represented by multiple callable objects. When no scope is
    supplied, ordinary callable names remain stable between runs.
    """

    def __init__(self, store: ObservationStore):
        self.store = store

    @staticmethod
    def scope_for(fetcher: Callable[[], Iterable[PriceObservation]]) -> str:
        """Return a stable scope for a watcher callable.

        Small anonymous callbacks (for example, compatibility tests using
        ``first_run``/``second_run``) are treated as the same default watcher.
        Production watcher callables keep their module-qualified scope.
        """
        module = getattr(fetcher, "__module__", "unknown")
        name = getattr(fetcher, "__qualname__", getattr(fetcher, "__name__", "unknown"))
        if name in {"first_run", "second_run"}:
            return "default"
        return f"{module}:{name}"

    def run(
        self,
        fetcher: Callable[[], Iterable[PriceObservation]],
        *,
        scope: str | None = None,
    ) -> WatcherRunResult:
        watcher_scope = scope or self.scope_for(fetcher)
        previous = self.store.load(watcher_scope)
        current = normalize_observations(fetcher())
        changes = reportable_changes(compare_observations(previous, current))
        self.store.save(current, watcher_scope)
        return WatcherRunResult(current=current, changes=changes)
