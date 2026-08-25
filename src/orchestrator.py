from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo
import json
import re

import httpx
import yaml
from bs4 import BeautifulSoup

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


def normalize_wishlist(item: dict) -> dict:
    category = item.get("category") or ("game" if item.get("platform") else "hardware")
    if category not in {"game", "hardware", "gear"}:
        category = "game"
    item["category"] = category
    return item


def collect_steamdb(app_ids: list[int], now: datetime) -> list[PriceObservation]:
    if not app_ids:
        return []
    client = SteamDBClient()
    results: list[PriceObservation] = []
    try:
        for app_id in sorted(set(app_ids)):
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


def resolve_steam_app_id(title: str) -> int | None:
    """Resolve a wishlist game name to the first Steam app result."""
    url = f"https://store.steampowered.com/search/?term={quote_plus(title)}"
    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent": "Personal-Gaming-Assistant/1.0"}) as client:
            response = client.get(url)
            response.raise_for_status()
        match = re.search(r"/app/(\d+)/", response.text)
        return int(match.group(1)) if match else None
    except Exception as exc:
        print(f"Steam search error for {title!r}: {exc}")
        return None


def collect_hardware(products: list[str], platform: str = "Hardware") -> list[PriceObservation]:
    if not products:
        return []
    client = RetailerAggregator()
    try:
        rows = []
        for product in products:
            for row in client.search_all(product):
                row.platform = platform
                rows.append(row)
        return rows
    finally:
        client.close()


def collect_wishlist(items: list[dict], now: datetime) -> tuple[list[PriceObservation], list[dict]]:
    """Use wishlist names directly; games are resolved through Steam, hardware/gear through retailers."""
    observations: list[PriceObservation] = []
    changed = False
    game_ids: list[int] = []
    physical_items: list[tuple[str, str]] = []

    for item in items:
        item = normalize_wishlist(item)
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        category = item["category"]
        if category == "game":
            app_id = item.get("app_id")
            if not app_id:
                app_id = resolve_steam_app_id(title)
                if app_id:
                    item["app_id"] = app_id
                    changed = True
            if app_id:
                game_ids.append(int(app_id))
        else:
            physical_items.append((title, "Hardware" if category == "hardware" else "Gear"))

    observations.extend(collect_steamdb(game_ids, now))
    for title, platform in physical_items:
        observations.extend(collect_hardware([title], platform=platform))
    return observations, items if changed else items


def run_once(roundup: bool = False) -> dict:
    config = load_config()
    now = datetime.now(ZoneInfo(config.get("timezone", "Europe/Amsterdam")))

    observations = collect_steamdb(config.get("steam_app_ids", []), now)
    observations.extend(collect_hardware(config.get("hardware_products", []), platform="Hardware"))

    wishlist_path = DATA / "wishlist.json"
    wishlist = json.loads(wishlist_path.read_text(encoding="utf-8")) if wishlist_path.exists() else []
    wishlist_observations, wishlist = collect_wishlist(wishlist, now)
    observations.extend(wishlist_observations)
    if wishlist:
        save_json("wishlist.json", wishlist)

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
        "wishlist_items": len(wishlist),
    }
    path = DATA / "updates.json"
    updates = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    updates.append(update)
    save_json("updates.json", updates[-100:])
    return {"update": update, "prices": rows}


if __name__ == "__main__":
    print(json.dumps(run_once(), ensure_ascii=False, indent=2))
