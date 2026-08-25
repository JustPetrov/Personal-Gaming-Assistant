from datetime import date

from src.dashboard.gamescom_preferences import post_gamescom_view, select_visit_days
from src.watchers.gamescom_schedule import build_gamescom_year


def test_dashboard_can_select_days_inside_gamescom():
    season = build_gamescom_year(2026, date(2026, 8, 26), date(2026, 8, 30), set())
    state = select_visit_days(season, {date(2026, 8, 28), date(2026, 8, 30)})
    assert state.selected_days == frozenset({date(2026, 8, 28), date(2026, 8, 30)})


def test_dashboard_rejects_days_outside_gamescom():
    season = build_gamescom_year(2026, date(2026, 8, 26), date(2026, 8, 30), set())
    try:
        select_visit_days(season, {date(2026, 9, 1)})
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid GamesCom date to be rejected")


def test_post_gamescom_hides_sections_and_counts_down():
    view = post_gamescom_view(2027, date(2027, 8, 25), date(2026, 8, 31))
    assert view["visible"] is False
    assert view["message"] == "Tot 2027!"
    assert view["countdown_days"] == 359
