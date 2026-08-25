from src.output.update_generator import UpdateContext, render_late_night_round_up, render_update
from src.watchers.change_detection import ChangeType, ObservationChange
from src.watchers.price_observations import observation_from_values


def test_render_update_has_consistent_header_and_change():
    current = observation_from_values(
        product="Test Game", platform="Steam", edition="Deluxe",
        price="€8", currency="EUR", stock="In stock", source="SteamDB"
    )
    previous = observation_from_values(
        product="Test Game", platform="Steam", edition="Deluxe",
        price="€10", currency="EUR", stock="In stock", source="SteamDB"
    )
    change = ObservationChange(ChangeType.PRICE_CHANGED, current, previous)
    context = UpdateContext("Personal Gaming Assistant", "Amsterdam", "08:00", "26-08-2026", "08:00", "26-08-2026")
    output = render_update(context, [change])
    assert "Lokale locatie" in output
    assert "€10 → **€8**" in output


def test_late_night_round_up_is_compact():
    context = UpdateContext("Personal Gaming Assistant", "Amsterdam", "22:00", "26-08-2026", "22:00", "26-08-2026")
    output = render_late_night_round_up(context, [])
    assert "Late Night Round Up" in output
    assert "20:00-update" in output
