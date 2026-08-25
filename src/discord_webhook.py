from __future__ import annotations

import os
import httpx


class DiscordWebhook:
    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("DISCORD_WEBHOOK_URL")

    def send(self, title: str, description: str, *, url: str | None = None) -> bool:
        if not self.url:
            return False
        payload = {
            "embeds": [{
                "title": title,
                "description": description[:4000],
                "url": url,
                "footer": {"text": "Personal Gaming Assistant"},
            }]
        }
        response = httpx.post(self.url, json=payload, timeout=15)
        response.raise_for_status()
        return True
