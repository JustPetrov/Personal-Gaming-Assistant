from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen


def write_news(context: dict) -> str:
    """Ask the configured Ollama model to write the supplied news context.

    The model is instructed to summarize only supplied facts and to mark
    unavailable data rather than inventing prices, ticket stock or quests.
    """
    edition = context.get("edition", "update")
    prompt = (
        "Schrijf een Nederlands gaming-nieuwsbericht op basis van uitsluitend "
        "de aangeleverde feiten. Verzin geen prijzen, voorraad, quests, data "
        "of nieuws. Vermeld ontbrekende data als onbekend. Gebruik de vaste "
        "secties uit context. Ieder nieuwsitem krijgt een korte Round-Up. "
        "Bij late-night is de Round-Up uitgebreider en vat die de gehele dag samen.\n\n"
        f"EDITIE: {edition}\n"
        f"CONTEXT:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    )
    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    request = Request(f"{base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    return str(data.get("response", "")).strip()
