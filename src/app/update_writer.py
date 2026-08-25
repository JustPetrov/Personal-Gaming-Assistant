from __future__ import annotations

import json
from typing import Any

from ai.ollama_writer import OllamaWriter


def facts_for_ollama(changes: list[dict[str, Any]]) -> str:
    """Serialize changed observations without allowing the model to invent facts."""
    return json.dumps(changes, ensure_ascii=False, indent=2, default=str)


def write_update(changes: list[dict[str, Any]], *, style: str = "compact Dutch gaming assistant update") -> str | None:
    if not changes:
        return None
    return OllamaWriter().write(facts_for_ollama(changes), style=style)
