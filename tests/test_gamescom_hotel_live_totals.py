from datetime import date
from decimal import Decimal

from src.watchers.gamescom_hotel_live import HotelOffer


def test_hotel_offer_calculates_nights_and_total():
    offer = HotelOffer(
        hotel="Test Hotel",
        check_in=date(2026, 8, 26),
        check_out=date(2026, 8, 29),
        price="€120,00",
        currency="EUR",
        availability="Available",
        url="https://example.test/hotel",
        source="Booking.com",
    )

    assert offer.nights == 3
    assert offer.total_price == Decimal("360.00")


def test_hotel_offer_without_price_has_no_total():
    offer = HotelOffer(
        hotel="Test Hotel",
        check_in=date(2026, 8, 26),
        check_out=date(2026, 8, 29),
        price=None,
        currency="EUR",
        availability="Unknown",
        url="https://example.test/hotel",
        source="Trivago",
    )

    assert offer.nights == 3
    assert offer.total_price is None
