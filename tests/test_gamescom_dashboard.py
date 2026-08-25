from datetime import date

from src.dashboard.gamescom_preferences import post_gamescom_view, select_visit_days
from src.watchers.gamescom_schedule import build_gamescom_year


def test_dashboard_can_select_days_inside_gamescom():
    season = build_gamescom_year(2026, date(2026, 8, 26), date(2026, 8, 30), set())
    state = select_visit_days(season, {date(2026, 8, 28), date(2026, 8, 30)})
    assert state.selected_days == frozenset({date(2026, 8, 28), date(2026, 8, 30)})


def test_dashboard_can_select_preferred_day():
    season = build_gamescom_year(2026, date(2026, 8, 26), date(2026, 8, 30), set())
    state = select_visit_days(
        season,
        {date(2026, 8, 28), date(2026, 8, 30)},
        preferred_day=date(2026, 8, 28),
    )
    assert state.preferred_day == date(2026, 8, 28)


def test_preferred_day_must_be_selected():
    season = build_gamescom_year(2026, date(2026, 8, 26), date(2026, 8, 30), set())
    try:
        select_visit_days(season, {date(2026, 8, 28)}, preferred_day=date(2026, 8, 29))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected preferred day to be selected")


def test_dashboard_rejects_days_outside_gamescom():
    season = build_gamescom_year(2026, date(2026, 8, 26), date(2026, 8, 30), set())
    try:
        select_visit_days(season, {date(2026, 9, 1)})
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid GamesCom date to be rejected")


def test_post_gamescom_hides_sections_and_enables_next_year_preference():
    view = post_gamescom_view(2027, date(2027, 8, 25), date(2026, 8, 31))
    assert view["visible"] is False
    assert view["message"] == "Tot 2027!"
    assert view["preferred_day_selection_enabled"] is True
