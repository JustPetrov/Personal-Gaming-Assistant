from decimal import Decimal

from src.watchers.uah_deals import GiftCardOffer, find_best_uah_offer, parse_uah_amount, required_gift_card_amount


def test_required_card_uses_smallest_covering_denomination():
    assert required_gift_card_amount(899, [500, 1000, 1500]) == 1000


def test_best_offer_includes_fees():
    offers = [
        GiftCardOffer(1000, Decimal("12.00"), "EUR", "Seller A", "4.9", 100, Decimal("1.00"), "https://example/a"),
        GiftCardOffer(1000, Decimal("11.50"), "EUR", "Seller B", "4.8", 200, Decimal("2.00"), "https://example/b"),
    ]
    result = find_best_uah_offer(899, offers, [500, 1000, 1500])
    assert result is not None
    assert result.offer.seller == "Seller A"
    assert result.total_cost == Decimal("13.00")


def test_parse_uah_amount():
    assert parse_uah_amount("899₴") == 899
    assert parse_uah_amount("1 000 UAH") == 1000
