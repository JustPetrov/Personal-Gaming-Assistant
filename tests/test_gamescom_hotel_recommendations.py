from decimal import Decimal

from src.watchers.gamescom_hotel_recommendations import HotelRecommendation, rank_hotels


def test_rank_returns_best_value_and_cheaper_alternative():
    offers = [
        HotelRecommendation("Motel One Köln-Messe", "best_value", Decimal("120"), 8.6, 450, "https://example.test/one", "Strong location and rating"),
        HotelRecommendation("ibis Budget Koeln Messe", "budget", Decimal("80"), 7.6, 500, "https://example.test/budget", "Cheaper option"),
        HotelRecommendation("Radisson Blu", "premium", Decimal("160"), 8.6, 450, "https://example.test/radisson", "Premium option"),
    ]
    best, cheaper = rank_hotels(offers)
    assert best is not None
    assert cheaper is not None
    assert cheaper.price_per_night < best.price_per_night
