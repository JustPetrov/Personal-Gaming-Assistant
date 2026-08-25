from src.watchers.discord_price_adapter import DiscordPriceAdapter
from src.watchers.g2g import G2GListing


class ClosableFakeClient:
    def __init__(self):
        self.closed = False

    def search(self, query):
        return [
            G2GListing(
                title=query,
                price="$9.99",
                currency="$",
                stock="Available",
                rating="5.0",
                review_count=10,
                url="https://www.g2g.com/example",
            )
        ]

    def close(self):
        self.closed = True


def test_injected_client_is_not_closed_by_adapter():
    client = ClosableFakeClient()
    DiscordPriceAdapter(client=client).fetch()
    assert client.closed is False


def test_adapter_fetch_closes_owned_client(monkeypatch):
    created = []

    class OwnedClient(ClosableFakeClient):
        def __init__(self):
            super().__init__()
            created.append(self)

    monkeypatch.setattr(
        "src.watchers.discord_price_adapter.G2GClient",
        OwnedClient,
    )
    DiscordPriceAdapter().fetch()
    assert created and created[0].closed is True
