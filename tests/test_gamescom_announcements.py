from datetime import datetime, timezone

from src.watchers.gamescom_announcements import AnnouncementState, detect_announcement_changes


def state(tickets=False, epix=False):
    return AnnouncementState(tickets, epix, datetime(2026, 8, 25, tzinfo=timezone.utc))


def test_ticket_sales_start_creates_one_alert():
    changes = detect_announcement_changes(state(), state(tickets=True))
    assert len(changes) == 1
    assert changes[0].kind == "ticket_sales"


def test_epix_start_creates_one_alert():
    changes = detect_announcement_changes(state(), state(epix=True))
    assert len(changes) == 1
    assert changes[0].kind == "epix_start"


def test_no_repeat_alert_when_already_open():
    assert detect_announcement_changes(state(tickets=True, epix=True), state(tickets=True, epix=True)) == []
