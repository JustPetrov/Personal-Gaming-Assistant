from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import os

import httpx

from web_sources import WebSource, WebResearch


class GamesComWebResearch:
    """Refresh GamesCom data from official/current web sources, then optionally summarize with Ollama."""

    SOURCES = (
        WebSource("GamesCom official", "https://www.gamescom.global/"),
        WebSource("GamesCom news", "https://www.gamescom.global/en/news/"),
    )

    def __init__(self, ollama_url: str | None = None, model: str | None = None):
        self.ollama_url = (ollama_url or os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.research = WebResearch()

    def fetch(self) -> dict:
        documents = []
        for source in self.SOURCES:
            try:
                documents.append({"source": source.name, "url": source.url, "text": self.research.fetch(source)})
            except Exception as exc:
                documents.append({"source": source.name, "url": source.url, "error": str(exc)})

        summary = self._ollama_summary(documents)
        result = {
            "last_synced": datetime.now().astimezone().isoformat(),
            "sources": documents,
            "summary": summary,
        }
        path = Path("data/gamescom_research.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    def _ollama_summary(self, documents: list[dict]) -> str | None:
        context = "\n\n".join(
            f"SOURCE: {d['source']}\nURL: {d['url']}\n{d.get('text', d.get('error', ''))}"
            for d in documents
        )
        prompt = (
            "Using ONLY the supplied web source text, extract current GamesCom facts. "
            "Return concise JSON with year, start_date, end_date, opening_hours, events, "
            "games, exhibitors, announcements and source_urls. Do not invent missing values.\n\n"
            + context
        )
        try:
            with httpx.Client(timeout=90) as client:
                response = client.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                return response.json().get("response")
        except Exception as exc:
            return f"Ollama unavailable: {exc}"
