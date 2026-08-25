from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import os

import httpx


@dataclass
class WebSource:
    title: str
    url: str
    content: str
    source: str


class WebContext:
    """Retrieve public web context before asking the local Ollama model.

    Ollama is the local model/runtime. It does not itself provide unrestricted
    web browsing, so this layer performs the network retrieval and passes the
    retrieved context to Ollama.
    """

    def __init__(self, timeout: float = 20.0):
        self.client = httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "Personal-Gaming-Assistant/1.0"})

    def close(self):
        self.client.close()

    def fetch(self, urls: Iterable[str]) -> list[WebSource]:
        results: list[WebSource] = []
        for url in urls:
            try:
                response = self.client.get(url)
                response.raise_for_status()
                results.append(WebSource(title=url, url=url, content=response.text[:20000], source=url))
            except Exception as exc:
                results.append(WebSource(title=url, url=url, content=f"Fetch failed: {exc}", source=url))
        return results


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.client = httpx.Client(timeout=120.0)

    def close(self):
        self.client.close()

    def chat_with_web_context(self, question: str, sources: list[WebSource]) -> str:
        context = "\n\n".join(f"SOURCE: {s.title}\nURL: {s.url}\nCONTENT:\n{s.content}" for s in sources)
        prompt = (
            "Answer in Dutch. Use the supplied web context first. "
            "Never invent prices, stock, dates or links. Cite the relevant source URLs in the answer. "
            "If the supplied sources do not contain enough evidence, say so.\n\n"
            f"WEB CONTEXT:\n{context}\n\nQUESTION:\n{question}"
        )
        response = self.client.post(f"{self.base_url}/api/chat", json={"model": self.model, "stream": False, "messages": [{"role": "user", "content": prompt}]})
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")
