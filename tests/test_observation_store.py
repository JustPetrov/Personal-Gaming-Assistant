from datetime import datetime, timezone

from src.storage.observation_store import ObservationStore
from src.watchers.price_observations import observation_from_values


def make(product: str, source: str = "SteamDB"):
    return observation_from_values(
        product=product,
        platform="Steam",
        edition="Deluxe Edition",
        price="€29,99",
        currency="EUR",
        stock="Pre-order",
        url="https://store.steampowered.com/app/1912410/",
        source=source,
        checked_at=datetime(2026, 8, 26, 8, 0, tzinfo=timezone.utc),
    )


def test_store_round_trip(tmp_path):
    path = tmp_path / "state" / "observations.json"
    store = ObservationStore(path)
    observation = make("Minecraft Dungeons II")

    store.save([observation], scope="steam")
    loaded = store.load("steam")

    assert loaded == [observation]


def test_missing_store_is_empty(tmp_path):
    assert ObservationStore(tmp_path / "missing.json").load() == []


def test_scopes_do_not_overwrite_each_other(tmp_path):
    store = ObservationStore(tmp_path / "state" / "observations.json")
    steam = make("Steam Game", "SteamDB")
    hardware = make("GPU", "Tweakers")

    store.save([steam], scope="steam")
    store.save([hardware], scope="hardware")

    assert store.load("steam") == [steam]
    assert store.load("hardware") == [hardware]


def test_legacy_single_snapshot_is_read_as_default(tmp_path):
    path = tmp_path / "state" / "observations.json"
    path.parent.mkdir(parents=True)
    observation = make("Legacy Game")
    import json
    path.write_text(
        json.dumps({"observations": [store_payload(observation)]}),
        encoding="utf-8",
    )

    assert ObservationStore(path).load() == [observation]


def store_payload(observation):
    return {
        "product": observation.product,
        "platform": observation.platform,
        "edition": observation.edition,
        "price": observation.price,
        "currency": observation.currency,
        "stock": observation.stock,
        "url": observation.url,
        "source": observation.source,
        "checked_at": observation.checked_at.isoformat(),
    }
