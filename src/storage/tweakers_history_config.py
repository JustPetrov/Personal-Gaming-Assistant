from __future__ import annotations

import os


def tweakers_history_urls() -> tuple[str, ...]:
    """Configured Tweakers product pages to sample every monitoring cycle."""
    return tuple(
        url.strip()
        for url in os.getenv("TWEAKERS_PRICE_HISTORY_URLS", "").split(",")
        if url.strip()
    )
