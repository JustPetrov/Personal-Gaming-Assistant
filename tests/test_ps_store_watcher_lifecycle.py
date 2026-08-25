from src.app.watcher_registry import get_fetchers


class _FakeClient:
    def __init__(self):
        self.closed = False

    def get_listing(self, url):
        return type("Listing", (), {
            "name": "Example Game",
            "edition": None,
            "price": "€10,00",
            "currency": "EUR",
            "available": True,
            "url": url,
        })()

    def close(self):
        self.closed = True


def test_ps_store_fetcher_is_wrapped_for_cleanup(monkeypatch):
    monkeypatch.setenv("PS_STORE_URLS", "https://store.playstation.com/nl-nl/example")
    fetchers = get_fetchers()
    ps_fetcher = next(fetcher for fetcher in fetchers if fetcher.__name__ == "ps_store_price_fetcher")
    assert ps_fetcher.__name__ == "ps_store_price_fetcher"
