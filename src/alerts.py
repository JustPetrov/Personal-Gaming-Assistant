from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Change:
    kind: str
    item: str
    before: str | None
    after: str | None
    url: str | None = None
    source: str | None = None


def detect_price_changes(previous: Iterable[dict], current: Iterable[dict]) -> list[Change]:
    old = {(x.get("product"), x.get("currency"), x.get("source")): x for x in previous}
    changes: list[Change] = []
    for item in current:
        key = (item.get("product"), item.get("currency"), item.get("source"))
        prior = old.get(key)
        if not prior:
            continue
        if prior.get("price") != item.get("price"):
            changes.append(Change("price", item.get("product", ""), prior.get("price"), item.get("price"), item.get("url"), item.get("source")))
        if prior.get("stock") != item.get("stock"):
            changes.append(Change("stock", item.get("product", ""), prior.get("stock"), item.get("stock"), item.get("url"), item.get("source")))
    return changes
