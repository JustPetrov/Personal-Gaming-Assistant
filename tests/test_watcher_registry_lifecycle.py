from src.app.watcher_registry import get_fetchers


class _Dummy:
    def fetch(self):
        return []

    def close(self):
        pass


def test_registry_contains_hardware_and_tweakers_fetchers(monkeypatch):
    monkeypatch.setenv("HARDWARE_WATCH_QUERIES", "RTX 5090")
    monkeypatch.setenv("TWEAKERS_PRICE_HISTORY_URLS", "https://tweakers.net/pricewatch/example")
    monkeypatch.setenv("WISHLIST_WATCH_ENABLED", "false")
    monkeypatch.setenv("DISCORD_PRICE_WATCH_ENABLED", "false")
    monkeypatch.setenv("EPIX_WATCH_ENABLED", "false")
    monkeypatch.setenv("GAMESCOM_TICKET_WATCH_ENABLED", "false")
    monkeypatch.setattr("src.app.watcher_registry.load_game_watchlist", lambda: [])

    fetchers = get_fetchers()
    assert len(fetchers) == 2
    assert all(callable(fetcher) for fetcher in fetchers)
