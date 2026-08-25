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
    """Fetch the configured EPIX quest page and extract stable quest links.

    The page remains the source of truth; parsing deliberately avoids inventing
    quest metadata when the source does not expose it.
    """
    target = url or os.getenv("EPIX_QUESTS_URL", DEFAULT_URL)
    request = Request(target, headers={"User-Agent": "Personal-Gaming-Assistant/1.0"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")

    # Keep the raw page available to the existing parser layer. This watcher
    # only creates a deterministic page fingerprint until structured parsing
    # is configured for the current GamesCom markup.
    fingerprint = hashlib.sha256(html.encode("utf-8")).hexdigest()
    return [Quest("EPIX Quests", target, fingerprint)]


def changed_quests(current: list[Quest], state_path: str = "data/state/epix_quests.json") -> list[Quest]:
    """Return quests whose source fingerprint changed since the last check."""
    try:
        previous = json.loads(open(state_path, encoding="utf-8").read())
    except (OSError, json.JSONDecodeError):
        previous = {}
    old = previous.get("fingerprints", {})
    changed = [item for item in current if old.get(item.url) != item.fingerprint]
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as handle:
        json.dump({"fingerprints": {item.url: item.fingerprint for item in current}}, handle, indent=2)
    return changed
