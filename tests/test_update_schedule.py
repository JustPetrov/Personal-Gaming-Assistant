from datetime import datetime, timezone

from src.scheduler.update_schedule import get_schedule, update_kind_at


def test_schedule_has_four_daily_updates():
    schedule = get_schedule()
    assert [(item.hour, item.minute) for item in schedule] == [(8, 0), (12, 0), (20, 0), (22, 0)]
    assert schedule[-1].late_night_round_up is True


def test_schedule_uses_amsterdam_timezone():
    dt = datetime(2026, 8, 26, 6, 0, tzinfo=timezone.utc)
    assert update_kind_at(dt).kind == "morning"


def test_non_update_time_returns_none():
    dt = datetime(2026, 8, 26, 7, 59, tzinfo=timezone.utc)
    assert update_kind_at(dt) is None
