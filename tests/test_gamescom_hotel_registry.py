from datetime import date
from decimal import Decimal

from watchers.gamescom_hotel_live import HotelOffer
from watchers import watcher_registry_gamescom as registry


def test_hotel_dates_require_explicit_configuration(monkeypatch):
    monkeypatch.delenv("GAMESCOM_HOTEL_CHECK_IN", raising=False)
    monkeypatch.delenv("GAMESCOM_HOTEL_CHECK_OUT", raising=False)
    assert registry._hotel_check_dates() is None


def test_hotel_dates_reject_invalid_or_reversed_values(monkeypatch):
    monkeypatch.setenv("GAMESCOM_HOTEL_CHECK_IN", "2026-08-28")
    monkeypatch.setenv("GAMESCOM_HOTEL_CHECK_OUT", "2026-08-28")
    assert registry._hotel_check_dates() is None

    monkeypatch.setenv("GAMESCOM_HOTEL_CHECK_IN", "invalid")
    monkeypatch.setenv("GAMESCOM_HOTEL_CHECK_OUT", "2026-08-30")
    assert registry._hotel_check_dates() is None


def test_live_hotel_offer_is_normalized_with_total_price():
    offer = HotelOffer(
        hotel="Test Hotel",
        check_in=date(2026, 8, 28),
        check_out=date(2026, 8, 31),
        price="€100,00",
        currency="EUR",
        availability="Available",
        url="https://example.test/hotel",
        source="Booking.com",
    )

    recommendation = registry._hotel_to_recommendation(offer)
    assert recommendation.name == "Test Hotel"
    assert recommendation.price_per_night == Decimal("100.00")
    assert offer.nights == 3
    assert offer.total_price == Decimal("300.00")


def test_hotel_fetcher_uses_configured_clients(monkeypatch):
    monkeypatch.setenv("GAMESCOM_HOTEL_CHECK_IN", "2026-08-28")
    monkeypatch.setenv("GAMESCOM_HOTEL_CHECK_OUT", "2026-08-31")

    class FakeClient:
        def fetch(self, check_in, check_out):
            return [HotelOffer(
                hotel="Live Hotel",
                check_in=check_in,
                check_out=check_out,
                price="€120,00",
                currency="EUR",
                availability="Available",
                url="https://example.test/live",
                source="Booking.com",
            )]

    monkeypatch.setattr(
        registry.GamesComHotelLiveClient,
        "configured_clients",
        classmethod(lambda cls: [FakeClient()]),
    )

    rows = list(registry._hotel_recommendation_fetcher())
    assert len(rows) == 1
    assert rows[0]["type"] == "gamescom_hotel_offer"
    assert rows[0]["price_per_night"] == "120.00"
    assert rows[0]["total_price"] == "360.00"
    assert rows[0]["nights"] == 3
    assert rows[0]["source"] == "Booking.com"
