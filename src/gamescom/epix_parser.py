from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

from gamescom.epix_quest_watch import Quest
import hashlib


class _QuestParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.in_link = False
        self.href = ""
        self.text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.in_link = True
            self.href = urljoin(self.base_url, href)
            self.text = []

    def handle_data(self, data: str) -> None:
        if self.in_link:
            self.text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.in_link:
            title = " ".join(part for part in self.text if part).strip()
            if title:
                self.links.append((title, self.href))
            self.in_link = False


def parse_quests(html: str, base_url: str) -> list[Quest]:
    parser = _QuestParser(base_url)
    parser.feed(html)
    quests: list[Quest] = []
    seen: set[str] = set()
    for title, url in parser.links:
        haystack = f"{title} {url}".lower()
        if "quest" not in haystack or url in seen:
            continue
        seen.add(url)
        quests.append(Quest(title, url, hashlib.sha256(f"{title}|{url}".encode()).hexdigest()))
    return quests
