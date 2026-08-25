from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


class OllamaWriter:
    """Generate the user-facing news/update text through a local Ollama API."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1")

    def write(self, facts: str, style: str = "consistent Dutch gaming assistant update") -> str:
        prompt = (
            "Write the final Dutch gaming-assistant news/update from the supplied facts. "
            "Do not invent prices, dates, stock, links, sources or events. Preserve exact values. "
            "Use a concise but informative consistent style. Include only facts that are supplied.\n\n"
            f"Style: {style}\n\nFacts:\n{facts}"
        )
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = str(data.get("response", "")).strip()
            if not text:
                raise RuntimeError("Ollama returned an empty response")
            return text
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            raise RuntimeError(f"Ollama writer unavailable: {exc}") from exc
