from __future__ import annotations

import os

from discord_webhook import DiscordWebhook
from notifications_api import send_push


class NotificationService:
    def __init__(self):
        self.discord = DiscordWebhook()

    def alert(self, title: str, description: str, url: str | None = None) -> dict:
        sent = {"discord": False, "push": 0}
        if os.getenv("DISCORD_WEBHOOK_URL"):
            try:
                sent["discord"] = self.discord.send(title, description, url=url)
            except Exception as exc:
                print(f"Discord notification failed: {exc}")
        try:
            sent["push"] = send_push(title, description, url=url)
        except Exception as exc:
            print(f"Push notification failed: {exc}")
        return sent
