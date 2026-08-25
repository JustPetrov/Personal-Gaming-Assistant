from __future__ import annotations

from watchers.price_models import PriceObservation
from watchers.steamdb_adapter import SteamDBAdapter


class FakeClient:
    def __init__(self):
        self.closed = False

    def get_price(self, app_id):
        class Price:
            name = "Test Game"
            eur = "9.99"
            uah = "399"
            url = "https://steamdb.info/app/1/"

        return Price()

    def close(self):
        self.closed = True


def test_adapter_closes_owned_client():
    client = FakeClient()
    adapter = SteamDBAdapter([1], client=client)
    adapter.fetch()
    adapter.close()
    assert client.closed is False


def test_adapter_closes_its_owned_client(monkeypatch):
    created = []

    class OwnedFakeClient(FakeClient):
        pass

    def factory():
        client = OwnedFakeClient()
        created.append(client)
        return client

    monkeypatch.setattr("watchers.steamdb_adapter.SteamDBClient", factory)
    adapter = SteamDBAdapter([1])
    adapter.fetch()
    adapter.close()
    assert created[0].closed is True
