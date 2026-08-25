from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from pathlib import Path
import json
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


EPIX_URL = "https://www.gamescom.global/en/epix/quests"


@dataclass(frozen=True)
class EpixQuest:
    title: str
    url: str
    description: str | None = None


class EpixQuestClient:
    """Fetch EPIX quests from the official gamescom quest page."""

    def __init__(self, timeout: float = 20.0):
        self.client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Personal-Gaming-Assistant/1.0"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def fetch(self) -> list[EpixQuest]:
        response = self.client.get(EPIX_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        quests: dict[str, EpixQuest] = {}

        for link in soup.find_all("a", href=True):
            text = " ".join(link.stripped_strings)
            href = urljoin(EPIX_URL, link["href"])
            lower = text.lower()
            if not text or "quest" not in lower:
                continue
            if href.rstrip("/") == EPIX_URL.rstrip("/"):
                continue
            quests[href] = EpixQuest(title=text, url=href)

        return sorted(quests.values(), key=lambda quest: quest.title.casefold())


class EpixQuestState:
    """Persist quest URLs so alerts only fire for newly discovered quests."""

    def __init__(self, path: str | Path = "data/state/epix_quests.json"):
        self.path = Path(path)

    def load(self) -> set[str]:
        if not self.path.exists():
            return set()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return set(data.get("urls", []))

    def save(self, quests: list[EpixQuest]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"urls": sorted({quest.url for quest in quests})}, indent=2),
            encoding="utf-8",
        )

    def new_quests(self, quests: list[EpixQuest]) -> list[EpixQuest]:
        previous = self.load()
        new = [quest for quest in quests if quest.url not in previous]
        self.save(quests)
        return new
