from __future__ import annotations

import json
from pathlib import Path

from watchers.price_models import PriceObservation
from watchers.wishlist_adapter import WishlistWatcherAdapter


class FakePrice:
    name = "Example Game"
    eur = "€19,99"
    uah = "₴799"
    url = "https://steamdb.info/app/123/"


class FakeSteam:
    def __init__(self, *_args, **_kwargs):
        self.calls = []

    def get_price(self, app_id):
        self.calls.append(app_id)
        return FakePrice()

    def close(self):
        pass


def test_wishlist_games_are_watched_and_app_id_is_persisted(monkeypatch, tmp_path: Path):
    path = tmp_path / "wishlist.json"
    path.write_text(json.dumps([{"title": "Example Game", "category": "game"}]), encoding="utf-8")

    monkeypatch.setattr("watchers.wishlist_adapter.SteamDBClient", FakeSteam)
    monkeypatch.setattr(WishlistWatcherAdapter, "_resolve_steam_app_id", staticmethod(lambda title: 123))

    observations = WishlistWatcherAdapter(path).fetch()

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved[0]["app_id"] == 123
    assert {item.currency for item in observations} == {"EUR", "UAH"}
    assert all(item.edition.startswith("Wishlist") for item in observations)


def test_empty_or_invalid_wishlist_is_safe(tmp_path: Path):
    path = tmp_path / "wishlist.json"
    path.write_text("{}", encoding="utf-8")
    assert WishlistWatcherAdapter(path).fetch() == []
