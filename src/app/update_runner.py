from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime

from output.update_generator import UpdateContext, render_late_night_round_up, render_update
from scheduler.update_schedule import ScheduledUpdate
from watchers.price_models import PriceObservation
from watchers.watcher_pipeline import WatcherPipeline

WatcherFetcher = Callable[[], Iterable[PriceObservation]]


class UpdateRunner:
    """Orchestrates all registered price watchers for one scheduled update."""

    def __init__(self, pipeline: WatcherPipeline, fetchers: Iterable[WatcherFetcher]):
        self.pipeline = pipeline
        self.fetchers = tuple(fetchers)

    def run(
        self,
        scheduled: ScheduledUpdate,
        context: UpdateContext,
    ) -> str:
        all_changes = []
        for fetcher in self.fetchers:
            result = self.pipeline.run(fetcher)
            all_changes.extend(result.changes)

        output = render_update(context, all_changes)
        if scheduled.late_night_round_up:
            output += "\n\n" + render_late_night_round_up(context, all_changes)
        return output
