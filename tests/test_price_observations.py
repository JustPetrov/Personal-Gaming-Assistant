from datetime import datetime, timezone

from src.watchers.price_observations import (
    normalize_observations,
    observation_dict,
    observation_from_values,
    observation_key,
)


def test_observation_has_timezone_aware_timestamp():
    observation = observation_from_values(
        product="Minecraft Dungeons II",
        platform="Steam",
        edition="Deluxe Edition",
        price="€29,99",
        currency="EUR",
        stock="Pre-order",
        url="https://store.steampowered.com/",
        source="SteamDB",
    )
    assert observation.checked_at.tzinfo is not None
    assert observation.source == "SteamDB"


def test_observation_key_is_stable():
    observation = observation_from_values(
        product="GTA VI",
        platform="PS5",
        edition="Ultimate Edition",
        source="PlayStation Store",
        checked_at=datetime(2026, 8, 26, tzinfo=timezone.utc),
    )
    assert observation_key(observation) == ("GTA VI", "PS5", "Ultimate Edition")


def test_normalize_observations_is_deterministic():
    second = observation_from_values(product="B", platform="Steam", source="SteamDB")
    first = observation_from_values(product="A", platform="Steam", source="SteamDB")
    assert [item.product for item in normalize_observations([second, first])] == ["A", "B"]


def test_observation_dict_serializes_timestamp():
    observation = observation_from_values(product="Test", platform="Steam", source="SteamDB")
    data = observation_dict(observation)
    assert isinstance(data["checked_at"], str)
    assert "T" in data["checked_at"]
