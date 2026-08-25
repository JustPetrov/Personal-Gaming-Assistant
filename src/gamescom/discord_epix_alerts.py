from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen


def send_epix_alerts(observations: list[dict]) -> list[str]:
    """Send newly detected EPIX quest observations to the configured Discord webhook."""
    alerts = [item for item in observations if item.get("type") == "epix_quest_alert"]
    if not alerts:
        return []
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not configured")

    messages: list[str] = []
    for alert in alerts:
        title = str(alert.get("title", "EPIX Quest"))
        url = str(alert.get("url", ""))
        message = f"🟣 EPIX Quest Alert\nNieuwe EPIX Quest: {title}"
        if url:
            message += f"\n{url}"
        payload = json.dumps({"content": message}).encode("utf-8")
        request = Request(webhook, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=30) as response:
            if response.status >= 300:
                raise RuntimeError(f"Discord webhook returned HTTP {response.status}")
        messages.append(message)
    return messages
