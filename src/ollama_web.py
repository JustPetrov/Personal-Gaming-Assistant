from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import httpx


@dataclass
class WebSource:
    title: str
    url: str
    content: str
    source: str


class WebContext:
    """Small web-retrieval layer used before sending a question to Ollama.

    Ollama is the local model/runtime; it does not magically browse the web.
    This layer retrieves public pages/APIs and passes the resulting context to Ollama.
    """

    def __init__(self, timeout: float = 20.0):
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Personal-Gaming-Assistant/1.0"},
        )

    def close(self):
        self.client.close()

    def fetch(self, urls: Iterable[str]) -> list[WebSource]:
        results: list[WebSource] = []
        for url in urls:
            try:
                response = self.client.get(url)
                response.raise_for_status()
                text = response.text[:20000]
                results.append(WebSource(title=url, url=url, content=text, source=url))
            except Exception as exc:
                results.append(WebSource(title=url, url=url, content=f"Fetch failed: {exc}", source=url))
        return results


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.Client(timeout=120.0)

    def close(self):
        self.client.close()

    def chat_with_web_context(self, question: str, sources: list[WebSource]) -> str:
        context = "\n\n".join(
            f"SOURCE: {source.title}\nURL: {source.url}\nCONTENT:\n{source.content}"
            for source in sources
        )
        prompt = (
            "Answer in Dutch. Use the supplied web context first. "
            "Do not invent prices, stock, dates or links. If the context is insufficient, say so.\n\n"
            f"WEB CONTEXT:\n{context}\n\nQUESTION:\n{question}"
        )
        response = self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")
