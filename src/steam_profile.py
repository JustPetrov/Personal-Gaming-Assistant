from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import os

import httpx


class SteamProfileSync:
    """Syncs public Steam profile/game-library data.

    Spending is only populated when an authenticated Steam data source/API is
    configured. The sync never invents spending figures.
    """

    def __init__(self, profile_url: str | None = None, api_key: str | None = None):
        self.profile_url = profile_url or os.getenv("STEAM_PROFILE_URL")
        self.api_key = api_key or os.getenv("STEAM_API_KEY")

    def sync(self, output: str = "data/steam_profile.json") -> dict:
        result = {
            "profile_url": self.profile_url,
            "display_name": None,
            "level": None,
            "games": [],
            "total_spend_eur": None,
            "total_spend_uah": None,
            "last_synced": datetime.now(timezone.utc).isoformat(),
        }
        if not self.api_key or not self.profile_url:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return result

        steam_id = self._extract_steam_id(self.profile_url)
        if not steam_id:
            raise ValueError("Could not determine SteamID64 from STEAM_PROFILE_URL")

        base = "https://api.steampowered.com"
        with httpx.Client(timeout=20) as client:
            summary = client.get(f"{base}/ISteamUser/GetPlayerSummaries/v0002/", params={"key": self.api_key, "steamids": steam_id}).json()
            players = summary.get("response", {}).get("players", [])
            if players:
                player = players[0]
                result["display_name"] = player.get("personaname")
                result["profile_url"] = player.get("profileurl", self.profile_url)

            games = client.get(f"{base}/IPlayerService/GetOwnedGames/v0001/", params={"key": self.api_key, "steamid": steam_id, "include_appinfo": 1, "include_played_free_games": 1, "format": "json"}).json()
            result["games"] = games.get("response", {}).get("games", [])

        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    @staticmethod
    def _extract_steam_id(value: str) -> str | None:
        import re
        match = re.search(r"/profiles/(\d{17})", value)
        return match.group(1) if match else None
