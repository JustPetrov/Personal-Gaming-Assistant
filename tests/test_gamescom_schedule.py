from datetime import date

from src.watchers.gamescom_alerts import GamesComAlert, entry_alerts, filter_attended_events, watcher_visibility
from src.watchers.gamescom_schedule import build_gamescom_year


def season():
    return build_gamescom_year(
        2026,
        date(2026, 8, 26),
        date(2026, 8, 30),
        {date(2026, 8, 28), date(2026, 8, 30)},
    )


def test_only_attended_days_are_shown():
    events = [
        GamesComAlert("event", "Friday event", date(2026, 8, 28)),
        GamesComAlert("event", "Saturday event", date(2026, 8, 29)),
    ]
    result = filter_attended_events(events, season(), date(2026, 8, 28))
    assert [event.title for event in result] == ["Friday event"]


def test_entry_alerts_use_attended_days():
    events = [
        GamesComAlert("entry", "Friday entry", date(2026, 8, 28)),
        GamesComAlert("entry", "Saturday entry", date(2026, 8, 29)),
    ]
    assert len(entry_alerts(events, season(), date(2026, 8, 28))) == 1


def test_ticket_hotel_visibility_ends_after_gamescom():
    assert watcher_visibility(season(), date(2026, 8, 30)) is True
    assert watcher_visibility(season(), date(2026, 8, 31)) is False
