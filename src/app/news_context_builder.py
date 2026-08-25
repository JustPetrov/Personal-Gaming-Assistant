from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.game_price_news import build_game_price_news
from app.market_alert_observations import market_alert_observations
from storage.price_history import PriceHistory


def build_news_context_from_observations(
    observations: list[dict[str, Any]],
    *,
    edition: str = "update",
    ram_item_ids: list[str] | None = None,
    gpu_item_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build one fact-only payload for the Ollama news writer."""
    ram_item_ids = ram_item_ids or []
    gpu_item_ids = gpu_item_ids or []
    history = PriceHistory()
    game_prices = build_game_price_news(observations)
    alerts = market_alert_observations(history, ram_item_ids=ram_item_ids, gpu_item_ids=gpu_item_ids)

    by_type: dict[str, list[dict[str, Any]]] = {}
    for item in observations:
        kind = str(item.get("type") or "other")
        by_type.setdefault(kind, []).append(item)

    return {
        "edition": "late-night" if edition == "late-night" else "update",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "watcher_observations": by_type,
        "game_price_watcher": [item.__dict__ for item in game_prices],
        "market_alerts": alerts,
        "data_policy": "Gebruik uitsluitend aangeleverde feiten; ontbrekende data is onbekend.",
    }
