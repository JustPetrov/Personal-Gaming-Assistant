from __future__ import annotations

import os
from discord_webhook import DiscordWebhook


class NotificationService:
    def __init__(self):
        self.discord = DiscordWebhook()

    def alert(self, title: str, description: str, url: str | None = None) -> dict:
        sent = {"discord": False, "push": False}
        if os.getenv("DISCORD_WEBHOOK_URL"):
            try:
                sent["discord"] = self.discord.send(title, description, url=url)
            except Exception as exc:
                print(f"Discord notification failed: {exc}")
        # Push provider is intentionally abstracted: mobile tokens stay server-side
        # and can later be backed by Expo Notifications or FCM/APNs.
        return sent
