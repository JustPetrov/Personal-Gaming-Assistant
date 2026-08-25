from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .price_models import PriceObservation
from .price_observations import observation_key


class ChangeType(str, Enum):
    NEW = "new"
    PRICE_CHANGED = "price_changed"
    STOCK_CHANGED = "stock_changed"
    LINK_CHANGED = "link_changed"
    SOURCE_CHANGED = "source_changed"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class ObservationChange:
    change_type: ChangeType
    current: PriceObservation | None
    previous: PriceObservation | None


def compare_observations(
    previous: Iterable[PriceObservation],
    current: Iterable[PriceObservation],
) -> list[ObservationChange]:
    """Compare two watcher snapshots by stable product/platform/edition identity."""
    previous_map = {observation_key(item): item for item in previous}
    current_map = {observation_key(item): item for item in current}
    changes: list[ObservationChange] = []

    for key in sorted(current_map):
        current_item = current_map[key]
        previous_item = previous_map.get(key)
        if previous_item is None:
            changes.append(ObservationChange(ChangeType.NEW, current_item, None))
            continue
        if current_item.price != previous_item.price or current_item.currency != previous_item.currency:
            changes.append(ObservationChange(ChangeType.PRICE_CHANGED, current_item, previous_item))
            continue
        if current_item.stock != previous_item.stock:
            changes.append(ObservationChange(ChangeType.STOCK_CHANGED, current_item, previous_item))
            continue
        if current_item.url != previous_item.url:
            changes.append(ObservationChange(ChangeType.LINK_CHANGED, current_item, previous_item))
            continue
        if current_item.source != previous_item.source:
            changes.append(ObservationChange(ChangeType.SOURCE_CHANGED, current_item, previous_item))
            continue
        changes.append(ObservationChange(ChangeType.UNCHANGED, current_item, previous_item))

    for key in sorted(set(previous_map) - set(current_map)):
        changes.append(ObservationChange(ChangeType.REMOVED, None, previous_map[key]))

    return changes


def reportable_changes(changes: Iterable[ObservationChange]) -> list[ObservationChange]:
    """Return changes intended for user-facing updates; unchanged items are omitted."""
    return [change for change in changes if change.change_type != ChangeType.UNCHANGED]
