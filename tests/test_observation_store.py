from datetime import datetime, timezone

from src.storage.observation_store import ObservationStore
from src.watchers.price_observations import observation_from_values


def test_store_round_trip(tmp_path):
    path = tmp_path / "state" / "observations.json"
    store = ObservationStore(path)
    observation = observation_from_values(
        product="Minecraft Dungeons II",
        platform="Steam",
        edition="Deluxe Edition",
        price="€29,99",
        currency="EUR",
        stock="Pre-order",
        url="https://store.steampowered.com/app/1912410/",
        source="SteamDB",
        checked_at=datetime(2026, 8, 26, 8, 0, tzinfo=timezone.utc),
    )

    store.save([observation])
    loaded = store.load()

    assert len(loaded) == 1
    assert loaded[0] == observation


def test_missing_store_is_empty(tmp_path):
    assert ObservationStore(tmp_path / "missing.json").load() == []
