from __future__ import annotations

from config.game_price_watchlist import load_game_watchlist
from watchers.preorder_alerts import PreorderItem


def filter_preorder_items(items: list[PreorderItem]) -> list[PreorderItem]:
    """Keep pre-order monitoring scoped to the saved Game Price Watcher IDs."""
    watched = set(load_game_watchlist())
    return [item for item in items if item.item_id.isdigit() and int(item.item_id) in watched]
