from __future__ import annotations

from datetime import datetime, timezone

from app.news_context_builder import build_news_context_from_observations
from storage import JsonHistory


def test_late_night_reconstructs_persisted_day(tmp_path, monkeypatch):
    history_path = tmp_path / "history.json"
    history = JsonHistory(history_path)
    history.append({
        "type": "game_news",
        "source": "Steam",
        "title": "Earlier announcement",
        "checked_at": datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc).isoformat(),
    })
    monkeypatch.setattr("app.news_context_builder.JsonHistory", lambda: JsonHistory(history_path))

    current = [{
        "type": "game_news",
        "source": "Steam",
        "title": "Evening announcement",
        "checked_at": datetime(2026, 8, 25, 20, 0, tzinfo=timezone.utc).isoformat(),
    }]

    context = build_news_context_from_observations(current, edition="late-night")
    titles = [item["title"] for items in context["watcher_observations"].values() for item in items]

    assert "Earlier announcement" in titles
    assert "Evening announcement" in titles


def test_late_night_deduplicates_same_observation(tmp_path, monkeypatch):
    history_path = tmp_path / "history.json"
    history = JsonHistory(history_path)
    duplicate = {
        "type": "game_news",
        "source": "Steam",
        "title": "Same item",
        "checked_at": datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc).isoformat(),
    }
    history.append(duplicate)
    monkeypatch.setattr("app.news_context_builder.JsonHistory", lambda: JsonHistory(history_path))

    context = build_news_context_from_observations([duplicate], edition="late-night")
    items = context["watcher_observations"]["game_news"]

    assert len(items) == 1
