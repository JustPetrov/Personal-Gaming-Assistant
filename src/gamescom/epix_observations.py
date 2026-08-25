from __future__ import annotations

import os
from urllib.request import Request, urlopen

from gamescom.epix_parser import parse_quests
from gamescom.epix_quest_watch import changed_quests

DEFAULT_URL = "https://www.gamescom.global/en/epix/quests"


def collect_epix_observations() -> list[dict]:
    """Fetch EPIX, parse quests, persist state, and emit only new quests."""
    url = os.getenv("EPIX_QUESTS_URL", DEFAULT_URL)
    request = Request(url, headers={"User-Agent": "Personal-Gaming-Assistant/1.0"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")

    quests = parse_quests(html, url)
    new_quests = changed_quests(quests)
    return [
        {
            "type": "epix_quest_alert",
            "title": quest.title,
            "url": quest.url,
            "fingerprint": quest.fingerprint,
            "message": f"Nieuwe EPIX Quest: {quest.title}",
        }
        for quest in new_quests
    ]
