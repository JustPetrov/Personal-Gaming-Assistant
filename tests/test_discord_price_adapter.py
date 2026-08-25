from src.watchers.discord_price_adapter import DiscordPriceAdapter
from src.watchers.g2g import G2GListing


def test_boost_price_is_multiplied_by_14():
    assert DiscordPriceAdapter._scaled_price("$0.35", 14) == "$4,90"


def test_nitro_price_is_not_multiplied():
    assert DiscordPriceAdapter._scaled_price("$9.99", 1) == "$9.99"


class FakeClient:
    def search(self, query):
        return [G2GListing(
            title=query,
            price="$0.35" if "Boost" in query else "$9.99",
            currency="$",
            stock="Available",
            rating="5.0",
            review_count=10,
            url="https://www.g2g.com/example",
        )]


def test_adapter_covers_all_discord_products():
    observations = DiscordPriceAdapter(client=FakeClient()).fetch()
    assert {item.product for item in observations} == {"Server Boost", "Nitro", "Nitro Basic"}
    assert sum(item.product == "Server Boost" for item in observations) == 2
