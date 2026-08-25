from datetime import datetime, timedelta, timezone

from src.watchers.preorder_alerts import PreorderItem, upcoming_bonus_alerts


def test_uses_bonus_deadline_for_21_day_warning():
    now = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
    item = PreorderItem(
        item_id="game-1",
        title="Game 1",
        release_at=now + timedelta(days=60),
        bonus="Steelbook",
        url="https://example.test/game-1",
        bonus_deadline=now + timedelta(days=10),
    )

    alerts = upcoming_bonus_alerts([item], now=now)

    assert len(alerts) == 1
    assert alerts[0]["bonus_deadline"].startswith("2026-09-04")
    assert alerts[0]["days_remaining"] == 10


def test_does_not_alert_after_bonus_deadline():
    now = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
    item = PreorderItem(
        item_id="game-2",
        title="Game 2",
        release_at=now + timedelta(days=10),
        bonus="Skin",
        url=None,
        bonus_deadline=now - timedelta(minutes=1),
    )

    assert upcoming_bonus_alerts([item], now=now) == []


def test_inactive_or_missing_bonus_is_ignored():
    now = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
    inactive = PreorderItem(
        item_id="game-3",
        title="Game 3",
        release_at=now + timedelta(days=5),
        bonus="Skin",
        url=None,
        active=False,
    )
    no_bonus = PreorderItem(
        item_id="game-4",
        title="Game 4",
        release_at=now + timedelta(days=5),
        bonus=None,
        url=None,
    )

    assert upcoming_bonus_alerts([inactive, no_bonus], now=now) == []
