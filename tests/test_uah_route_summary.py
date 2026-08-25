from decimal import Decimal

from src.watchers.uah_deals import GiftCardOffer, build_uah_route_summary


def test_build_uah_route_summary_picks_cheapest_offer_and_sums_verified_routes():
    prices = [
        {"app_id": 1, "title": "Game A", "uah_price": 500, "eur_price": 12},
        {"app_id": 2, "title": "Game B", "uah_price": 900, "eur_price": 20},
    ]
    offers = {
        1: [
            GiftCardOffer(500, Decimal("15"), "EUR", "Seller A", "4.9", 100, Decimal("1"), "https://example/a1"),
            GiftCardOffer(500, Decimal("14"), "EUR", "Seller B", "4.8", 80, Decimal("0"), "https://example/a2"),
        ],
        2: [
            GiftCardOffer(1000, Decimal("28"), "EUR", "Seller C", "4.7", 70, Decimal("2"), "https://example/b1"),
        ],
    }

    summary = build_uah_route_summary(prices, offers, [500, 1000])

    assert summary.games_considered == 2
    assert summary.games_with_verified_route == 2
    assert summary.total_cost == Decimal("44")
    assert summary.routes[0].seller == "Seller B"
    assert summary.routes[1].required_card_uah == 1000


def test_unverified_game_is_not_estimated():
    prices = [{"app_id": 3, "title": "Game C", "uah_price": 700, "eur_price": 18}]
    summary = build_uah_route_summary(prices, {}, [500, 1000])

    assert summary.games_considered == 1
    assert summary.games_with_verified_route == 0
    assert summary.total_cost == Decimal("0")
    assert summary.routes == ()
