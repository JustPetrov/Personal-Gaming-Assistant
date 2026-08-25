from src.watchers.steamdb_adapter import SteamDBAdapter
from src.watchers.steamdb import SteamPrice


class FakeClient:
    def get_price(self, app_id):
        return SteamPrice(app_id, "Test Game", "€9,99", "899₴", f"https://steamdb.info/app/{app_id}/")


def test_adapter_emits_eur_and_uah_observations():
    adapter = SteamDBAdapter([123], client=FakeClient())
    observations = adapter.fetch()
    assert len(observations) == 2
    assert {(item.currency, item.price) for item in observations} == {("EUR", "€9,99"), ("UAH", "899₴")}
    assert all(item.source == "SteamDB" for item in observations)
