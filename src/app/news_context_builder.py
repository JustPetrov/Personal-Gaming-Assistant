from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo
import os

from app.game_price_news import build_game_price_news
from app.market_alert_observations import market_alert_observations
from storage import JsonHistory
from storage.price_history import PriceHistory


def _observation_fingerprint(item: dict[str, Any]) -> str:
    """Build a stable fingerprint without using volatile timestamps."""
    parts = (
        item.get("type"),
        item.get("source"),
        item.get("id") or item.get("product") or item.get("title"),
        item.get("platform"),
        item.get("edition"),
        item.get("price"),
        item.get("currency"),
        item.get("stock"),
        item.get("status"),
        item.get("url"),
    )
    return "|".join("" if value is None else str(value) for value in parts)


def _local_date() -> str:
    timezone_name = os.getenv("TIMEZONE", "Europe/Amsterdam")
    return datetime.now(ZoneInfo(timezone_name)).date().isoformat()


def _observation_day(observations: list[dict[str, Any]]) -> str:
    """Return the local calendar day represented by the current observations.

    This is important for late-night reconstruction: the persisted history can
    contain the requested day's data even when the test/worker is running on a
    different calendar day.
    """
    timezone_name = os.getenv("TIMEZONE", "Europe/Amsterdam")
    zone = ZoneInfo(timezone_name)
    for item in reversed(observations):
        for field in ("checked_at", "timestamp", "observed_at", "created_at"):
            value = item.get(field)
            if not value:
                continue
            try:
                parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(zone).date().isoformat()
            except ValueError:
                continue
    return _local_date()


def _merge_daily_observations(observations: list[dict[str, Any]], day: str) -> list[dict[str, Any]]:
    """Merge current observations with persisted observations from the same day."""
    history_rows = JsonHistory().for_date(day)
    merged = history_rows + list(observations)
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in merged:
        fingerprint = _observation_fingerprint(item)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        result.append(item)
    return result


def build_news_context_from_observations(
    observations: list[dict[str, Any]],
    *,
    edition: str = "update",
    ram_item_ids: list[str] | None = None,
    gpu_item_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build one fact-only payload for the Ollama news writer.

    Late-night editions intentionally reconstruct the current local day from
    persistent observation history so the 22:00 round-up covers the whole day.
    """
    ram_item_ids = ram_item_ids or []
    gpu_item_ids = gpu_item_ids or []
    if edition == "late-night":
        observations = _merge_daily_observations(observations, _observation_day(observations))

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
        "observation_count": len(observations),
        "watcher_observations": by_type,
        "game_price_watcher": [item.__dict__ for item in game_prices],
        "market_alerts": alerts,
        "data_policy": "Gebruik uitsluitend aangeleverde feiten; ontbrekende data is onbekend.",
    }
