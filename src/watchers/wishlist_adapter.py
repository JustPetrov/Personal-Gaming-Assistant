from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from urllib.parse import quote_plus
import re

import httpx

from .price_models import PriceObservation
from .price_observations import observation_from_values
from .retailer_aggregator import RetailerAggregator
from .steamdb import SteamDBClient


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "data"
WISHLIST_PATH = DATA / "wishlist.json"


class WishlistWatcherAdapter:
    """Turn the persistent wishlist into five-minute price observations."""

    def __init__(self, wishlist_path: Path = WISHLIST_PATH):
        self.wishlist_path = wishlist_path

    def fetch(self) -> list[PriceObservation]:
        items = self._load_items()
        if not items:
            return []

        observations: list[PriceObservation] = []
        changed = False
        game_ids: list[int] = []
        physical: list[tuple[str, str]] = []

        for item in items:
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            category = str(item.get("category") or ("game" if item.get("platform") else "hardware"))
            if category not in {"game", "hardware", "gear"}:
                category = "game"
                item["category"] = category
                changed = True

            if category == "game":
                app_id = self._coerce_app_id(item.get("app_id"))
                if app_id is None:
                    app_id = self._resolve_steam_app_id(title)
                    if app_id is not None:
                        item["app_id"] = app_id
                        changed = True
                if app_id is not None:
                    game_ids.append(app_id)
            else:
                physical.append((title, "Hardware" if category == "hardware" else "Gear"))

        if changed:
            self._save_items(items)

        now = datetime.now().astimezone()
        client = SteamDBClient()
        try:
            for app_id in sorted(set(game_ids)):
                price = client.get_price(app_id)
                observations.append(observation_from_values(
                    product=price.name,
                    platform="Steam",
                    edition="Wishlist",
                    price=price.eur,
                    currency="EUR" if price.eur else None,
                    stock="Available" if price.eur or price.uah else "Unavailable",
                    url=price.url,
                    source="SteamDB wishlist",
                    checked_at=now,
                ))
                if price.uah:
                    observations.append(observation_from_values(
                        product=price.name,
                        platform="Steam",
                        edition="Wishlist UAH",
                        price=price.uah,
                        currency="UAH",
                        stock="Available",
                        url=price.url,
                        source="SteamDB wishlist",
                        checked_at=now,
                    ))
        finally:
            client.close()

        if physical:
            retailer = RetailerAggregator()
            try:
                for title, platform in physical:
                    for row in retailer.search_all(title):
                        row.platform = platform
                        row.edition = "Wishlist"
                        observations.append(row)
            finally:
                retailer.close()

        return observations

    def _load_items(self) -> list[dict]:
        try:
            data = json.loads(self.wishlist_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def _save_items(self, items: list[dict]) -> None:
        self.wishlist_path.parent.mkdir(parents=True, exist_ok=True)
        self.wishlist_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _coerce_app_id(value: object) -> int | None:
        try:
            value = int(value) if value is not None else None
            return value if value and value > 0 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _resolve_steam_app_id(title: str) -> int | None:
        url = f"https://store.steampowered.com/search/?term={quote_plus(title)}"
        try:
            with httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent": "Personal-Gaming-Assistant/1.0"}) as client:
                response = client.get(url)
                response.raise_for_status()
            match = re.search(r"/app/(\d+)/", response.text)
            return int(match.group(1)) if match else None
        except (httpx.HTTPError, ValueError):
            return None
