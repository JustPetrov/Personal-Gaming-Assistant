from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from urllib.request import Request, urlopen


DEFAULT_URL = "https://www.gamescom.global/en/epix/quests"


@dataclass(frozen=True)
class Quest:
    title: str
    url: str
    fingerprint: str


def fetch_quests(url: str | None = None) -> list[Quest]:
    """Fetch EPIX quests with a stable fingerprint per quest.

    Only quest identity (title + URL) participates in the fingerprint, so
    unrelated page changes cannot create false alerts.
    """
    target = url or os.getenv("EPIX_QUESTS_URL", DEFAULT_URL)
    request = Request(target, headers={"User-Agent": "Personal-Gaming-Assistant/1.0"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")

    # Import lazily to avoid a parser -> Quest import cycle at module load time.
    from gamescom.epix_parser import parse_quests

    return parse_quests(html, target)


def changed_quests(current: list[Quest], state_path: str = "data/state/epix_quests.json") -> list[Quest]:
    """Return quests whose stable identity changed since the last check."""
    try:
        previous = json.loads(open(state_path, encoding="utf-8").read())
    except (OSError, json.JSONDecodeError, TypeError):
        previous = {}

    old = previous.get("fingerprints", {}) if isinstance(previous, dict) else {}
    changed = [item for item in current if old.get(item.url) != item.fingerprint]

    directory = os.path.dirname(state_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as handle:
        json.dump(
            {"fingerprints": {item.url: item.fingerprint for item in current}},
            handle,
            indent=2,
        )
    return changed
