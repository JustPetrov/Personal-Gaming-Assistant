from __future__ import annotations

from ollama_web import WebContext, OllamaClient


DEFAULT_SOURCES = [
    "https://steamdb.info/",
    "https://store.steampowered.com/",
    "https://www.playstation.com/nl-nl/",
    "https://www.tweakers.net/pricewatch/",
    "https://www.bol.com/",
    "https://azerty.nl/",
    "https://www.alternate.nl/",
    "https://www.megekko.nl/",
    "https://www.amazon.nl/",
    "https://www.g2g.com/",
    "https://www.gamescom.global/",
]


def ask_online(question: str, urls: list[str] | None = None, model: str = "llama3.2") -> str:
    web = WebContext()
    ollama = OllamaClient(model=model)
    try:
        sources = web.fetch(urls or DEFAULT_SOURCES)
        return ollama.chat_with_web_context(question, sources)
    finally:
        web.close()
        ollama.close()
