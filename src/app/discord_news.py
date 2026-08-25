from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen

MAX_CONTENT = 1900


def _chunks(text: str, limit: int = MAX_CONTENT) -> list[str]:
    """Split without cutting a line when possible."""
    chunks: list[str] = []
    remaining = text.strip()
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        cut = remaining.rfind("\n", 0, limit + 1)
        if cut < max(1, limit // 2):
            cut = remaining.rfind(" ", 0, limit + 1)
        if cut < 1:
            cut = limit
        chunks.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    return chunks


def send_news(article: str) -> None:
    """Send the complete generated article to Discord in safe-sized messages."""
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not configured")
    chunks = _chunks(article)
    for index, chunk in enumerate(chunks, start=1):
        prefix = f"**Deel {index}/{len(chunks)}**\n" if len(chunks) > 1 else ""
        payload = json.dumps({"content": prefix + chunk}).encode("utf-8")
        request = Request(
            webhook,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=30) as response:
            if response.status >= 300:
                raise RuntimeError(f"Discord webhook returned HTTP {response.status}")
