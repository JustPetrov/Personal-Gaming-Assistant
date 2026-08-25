from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json

import yaml

from storage import JsonHistory
from watchers.price_models import PriceObservation
from watchers.retailer_aggregator import RetailerAggregator
from watchers.steamdb import SteamDBClient

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "config.yaml"
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def save_json(name: str, value) -> None:
    (DATA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def collect_steamdb(app_ids: list[int], now: datetime) -> list[PriceObservation]:
    if not app_ids:
        return []
    client = SteamDBClient()
    results: list[PriceObservation] = []
    try:
        for app_id in app_ids:
            try:
                item = client.get_price(app_id)
                for price, currency in ((item.eur, "EUR"), (item.uah, "UAH")):
                    if price:
                        results.append(PriceObservation(item.name, "Steam", None, price, currency, "Available", item.url, "SteamDB", now))
            except Exception as exc:
                print(f"SteamDB error for {app_id}: {exc}")
    finally:
        client.close()
    return results


def collect_hardware(products: list[str]) -> list[PriceObservation]:
    if not products:
        return []
    client = RetailerAggregator()
    try:
        return [row for product in products for row in client.search_all(product)]
    finally:
        client.close()


def run_once(roundup: bool = False) -> dict:
    config = load_config()
    now = datetime.now(ZoneInfo(config.get("timezone", "Europe/Amsterdam")))
    observations = collect_steamdb(config.get("steam_app_ids", []), now)
    observations.extend(collect_hardware(config.get("hardware_products", [])))

    history = JsonHistory()
    for observation in observations:
        history.append(observation)

    rows = [{
        "product": o.product, "platform": o.platform, "edition": o.edition,
        "price": o.price, "currency": o.currency, "stock": o.stock,
        "url": o.url, "source": o.source, "checked_at": o.checked_at.isoformat()
    } for o in observations]
    save_json("prices.json", rows)

    update = {
        "timestamp": now.isoformat(),
        "type": "late_night_roundup" if roundup else "scheduled",
        "status": "completed",
        "items_checked": len(rows),
    }
    path = DATA / "updates.json"
    updates = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    updates.append(update)
    save_json("updates.json", updates[-100:])
    return {"update": update, "prices": rows}


if __name__ == "__main__":
    print(json.dumps(run_once(), ensure_ascii=False, indent=2))
