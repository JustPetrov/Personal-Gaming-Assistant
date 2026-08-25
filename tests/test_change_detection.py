from datetime import datetime, timezone

from src.watchers.change_detection import ChangeType, compare_observations, reportable_changes
from src.watchers.price_observations import observation_from_values


NOW = datetime(2026, 8, 26, 8, 0, tzinfo=timezone.utc)


def make(**kwargs):
    return observation_from_values(
        product="Test Game",
        platform="Steam",
        edition="Deluxe",
        source="SteamDB",
        checked_at=NOW,
        **kwargs,
    )


def test_new_item_is_detected():
    changes = compare_observations([], [make(price="€10", currency="EUR")])
    assert changes[0].change_type == ChangeType.NEW


def test_price_change_is_detected():
    previous = make(price="€10", currency="EUR")
    current = make(price="€8", currency="EUR")
    changes = compare_observations([previous], [current])
    assert changes[0].change_type == ChangeType.PRICE_CHANGED


def test_stock_change_is_detected():
    previous = make(price="€10", currency="EUR", stock="Out of stock")
    current = make(price="€10", currency="EUR", stock="In stock")
    changes = compare_observations([previous], [current])
    assert changes[0].change_type == ChangeType.STOCK_CHANGED


def test_removed_item_is_detected_but_can_be_filtered():
    previous = make(price="€10", currency="EUR")
    changes = compare_observations([previous], [])
    assert changes[0].change_type == ChangeType.REMOVED
    assert reportable_changes(changes)[0].change_type == ChangeType.REMOVED


def test_unchanged_items_are_not_reportable():
    previous = make(price="€10", currency="EUR", stock="In stock")
    current = make(price="€10", currency="EUR", stock="In stock")
    changes = compare_observations([previous], [current])
    assert changes[0].change_type == ChangeType.UNCHANGED
    assert reportable_changes(changes) == []
