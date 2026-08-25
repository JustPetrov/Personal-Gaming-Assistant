from datetime import datetime, timezone

from src.app.update_runner import UpdateRunner
from src.output.update_generator import UpdateContext
from src.scheduler.update_schedule import ScheduledUpdate
from src.storage.observation_store import ObservationStore
from src.watchers.price_observations import observation_from_values
from src.watchers.watcher_pipeline import WatcherPipeline


def test_runner_executes_watchers_and_adds_late_night_summary(tmp_path):
    store = ObservationStore(tmp_path / "state.json")
    pipeline = WatcherPipeline(store)
    checked = datetime(2026, 8, 26, 20, 0, tzinfo=timezone.utc)

    def fetcher():
        return [observation_from_values(
            product="Test Game", platform="Steam", edition="Deluxe",
            price="€9,99", currency="EUR", stock="In stock",
            source="SteamDB", checked_at=checked,
        )]

    runner = UpdateRunner(pipeline, [fetcher])
    scheduled = ScheduledUpdate(22, 0, "late_night", late_night_round_up=True)
    context = UpdateContext("Personal Gaming Assistant", "Amsterdam", "22:00", "26-08-2026", "22:00", "26-08-2026")
    output = runner.run(scheduled, context)

    assert "Test Game" in output
    assert "Late Night Round Up" in output
