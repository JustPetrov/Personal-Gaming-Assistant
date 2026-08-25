from src.watchers.hardware_retailer_adapter import HardwareRetailerAdapter
from src.watchers.retailers import RetailerResult, RETAILER_SEARCH_URLS


class FakeClient:
    def search(self, retailer, query):
        return RetailerResult(
            retailer=retailer,
            query=query,
            price="€499,00",
            stock="Op voorraad",
            url=RETAILER_SEARCH_URLS[retailer].format(q=query),
            source=retailer,
        )


def test_adapter_covers_all_configured_retailers():
    adapter = HardwareRetailerAdapter(["RTX 5090"], client=FakeClient())
    observations = adapter.fetch()
    assert len(observations) == 6
    assert {item.edition for item in observations} == set(RETAILER_SEARCH_URLS)
    assert all(item.platform == "Hardware" for item in observations)
    assert all(item.price == "€499,00" for item in observations)
    assert all(item.stock == "Op voorraad" for item in observations)
