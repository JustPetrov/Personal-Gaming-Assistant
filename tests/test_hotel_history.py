import json
from decimal import Decimal
from pathlib import Path

from storage.hotel_history import append_hotel_observations, lowest_historical_price


def test_hotel_history_persists_verified_prices(tmp_path: Path):
    path = tmp_path / "hotel_history.json"
    append_hotel_observations([{
        "product": "Hotel A",
        "source": "Booking.com",
        "url": "https://example.test/hotel-a",
        "price_per_night": "80.00",
        "total_price": "160.00",
        "availability": "Available",
        "nights": 2,
        "check_in": "2026-08-20",
        "check_out": "2026-08-22",
    }], path)
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert rows[0]["hotel"] == "Hotel A"
    assert lowest_historical_price("Hotel A", path=path) == Decimal("80.00")
