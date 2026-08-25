from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from report import late_night_roundup
from storage import JsonHistory
from watchers.price_models import PriceObservation
from watchers.steamdb import SteamDBClient

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "config.yaml"


def load_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def collect_steamdb(app_ids: list[int]) -> list[PriceObservation]:
    client = SteamDBClient()
    now = datetime.now(ZoneInfo("Europe/Amsterdam"))
    results: list[PriceObservation] = []
    try:
        for app_id in app_ids:
            try:
                item = client.get_price(app_id)
                results.append(PriceObservation(
                    product=item.name,
                    platform="Steam",
                    edition=None,
                    price=item.eur,
                    currency="EUR",
                    stock="Available",
                    url=item.url,
                    source="SteamDB",
                    checked_at=now,
                ))
                if item.uah:
                    results.append(PriceObservation(
                        product=item.name,
                        platform="Steam",
                        edition=None,
                        price=item.uah,
                        currency="UAH",
                        stock="Available",
                        url=item.url,
                        source="SteamDB",
                        checked_at=now,
                    ))
            except Exception as exc:
                print(f"SteamDB error for {app_id}: {exc}")
    finally:
        client.close()
    return results


def run_once(app_ids: list[int] | None = None, roundup: bool = False) -> str:
    config = load_config()
    ids = app_ids or config.get("steam_app_ids", [])
    observations = collect_steamdb(ids)
    history = JsonHistory()
    for observation in observations:
        history.append(observation)

    changes = [
        f"{o.product}: {o.price} {o.currency} via {o.source}"
        for o in observations
    ]
    if roundup:
        return late_night_roundup(changes, datetime.now(ZoneInfo("Europe/Amsterdam")))
    return "\n".join(changes) if changes else "Geen live prijsdata opgehaald."


if __name__ == "__main__":
    print(run_once())
