from datetime import datetime, timezone

from src.storage.observation_store import ObservationStore
from src.watchers.price_observations import observation_from_values
from src.watchers.watcher_pipeline import WatcherPipeline


NOW = datetime(2026, 8, 26, 8, 0, tzinfo=timezone.utc)


def test_pipeline_compares_then_persists(tmp_path):
    store = ObservationStore(tmp_path / "state.json")
    pipeline = WatcherPipeline(store)

    def first_run():
        return [observation_from_values(
            product="Test Game", platform="Steam", edition="Deluxe",
            price="€10", currency="EUR", stock="In stock",
            source="SteamDB", checked_at=NOW,
        )]

    first = pipeline.run(first_run)
    assert len(first.changes) == 1
    assert first.changes[0].change_type.value == "new"

    def second_run():
        return [observation_from_values(
            product="Test Game", platform="Steam", edition="Deluxe",
            price="€8", currency="EUR", stock="In stock",
            source="SteamDB", checked_at=NOW,
        )]

    second = pipeline.run(second_run)
    assert len(second.changes) == 1
    assert second.changes[0].change_type.value == "price_changed"
    assert store.load()[0].price == "€8"
