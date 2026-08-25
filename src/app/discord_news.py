from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen


def send_news(article: str) -> None:
    """Send the generated article to the configured Discord webhook."""
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not configured")
    payload = json.dumps({"content": article[:1900]}).encode("utf-8")
    request = Request(webhook, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=30) as response:
        if response.status >= 300:
            raise RuntimeError(f"Discord webhook returned HTTP {response.status}")
