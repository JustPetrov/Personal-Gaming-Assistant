from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen

from gamescom.discord_stock_alerts import collect_discord_stock_alerts
from gamescom.ticket_filter import filter_ticket_alerts


def send_selected_stock_alerts(statuses: list[dict], selections: list[dict]) -> list[str]:
    """Filter selected tickets, deduplicate their stock states, and send changes."""
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    filtered = filter_ticket_alerts(statuses, selections)
    messages = collect_discord_stock_alerts(filtered)
    if not messages:
        return []
    if not webhook:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not configured")

    for message in messages:
        payload = json.dumps({"content": f"🎟️ GamesCom Ticket Alert\n{message}"}).encode("utf-8")
        request = Request(webhook, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=30) as response:
            if response.status >= 300:
                raise RuntimeError(f"Discord webhook returned HTTP {response.status}")
    return messages
