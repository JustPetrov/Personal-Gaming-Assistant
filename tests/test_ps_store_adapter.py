from src.watchers.ps_store import PlayStationListing
from src.watchers.ps_store_adapter import PlayStationStoreAdapter


class FakeClient:
    def get_listing(self, url):
        return PlayStationListing(
            name="GTA VI",
            edition="Ultimate Edition",
            price="€99,99",
            currency="EUR",
            available=True,
            url=url,
        )


def test_adapter_emits_ps5_observation():
    adapter = PlayStationStoreAdapter(["https://store.playstation.com/nl-nl/example"], client=FakeClient())
    observations = adapter.fetch()
    assert len(observations) == 1
    item = observations[0]
    assert item.product == "GTA VI"
    assert item.platform == "PS5"
    assert item.edition == "Ultimate Edition"
    assert item.price == "€99,99"
    assert item.currency == "EUR"
    assert item.stock == "Available"
    assert item.source == "PlayStation Store"
