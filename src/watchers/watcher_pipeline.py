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
        """Return a stable scope for a watcher callable.

        Compatibility callbacks named ``first_run`` and ``second_run`` represent
        one logical watcher and intentionally share ``default``. Other callables
        retain an independent module-qualified scope unless ``run(scope=...)`` is
        supplied explicitly.
        """
        module = getattr(fetcher, "__module__", "unknown")
        qualified_name = getattr(fetcher, "__qualname__", getattr(fetcher, "__name__", "unknown"))
        leaf_name = qualified_name.rsplit(".", 1)[-1]
        if leaf_name in {"first_run", "second_run"}:
            return "default"
        return f"{module}:{qualified_name}"

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
