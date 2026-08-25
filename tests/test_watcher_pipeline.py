from datetime import datetime, timezone

from src.storage.observation_store import ObservationStore
from src.watchers.price_observations import observation_from_values
from src.watchers.watcher_pipeline import WatcherPipeline


NOW = datetime(2026, 8, 26, 8, 0, tzinfo=timezone.utc)


def observation(price: str = "€10"):
    return observation_from_values(
        product="Test Game",
        platform="Steam",
        edition="Deluxe",
        price=price,
        currency="EUR",
        stock="In stock",
        source="SteamDB",
        checked_at=NOW,
    )


def test_pipeline_compares_then_persists(tmp_path):
    store = ObservationStore(tmp_path / "state.json")
    pipeline = WatcherPipeline(store)

    def first_run():
        return [observation()]

    first = pipeline.run(first_run)
    assert len(first.changes) == 1
    assert first.changes[0].change_type.value == "new"

    def second_run():
        return [observation("€8")]

    second = pipeline.run(second_run)
    assert len(second.changes) == 1
    assert second.changes[0].change_type.value == "price_changed"
    assert store.load(pipeline.scope_for(first_run))[0].price == "€8"


def test_pipeline_scopes_are_independent(tmp_path):
    store = ObservationStore(tmp_path / "state.json")
    pipeline = WatcherPipeline(store)

    def steam():
        return [observation("€10")]

    def hardware():
        return [observation("€500")]

    pipeline.run(steam)
    pipeline.run(hardware)

    assert store.load(pipeline.scope_for(steam))[0].price == "€10"
    assert store.load(pipeline.scope_for(hardware))[0].price == "€500"
