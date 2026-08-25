from __future__ import annotations

import argparse
from datetime import datetime, timezone

from app.discord_news import send_news
from app.news_context_builder import build_news_context_from_observations
from app.ollama_news import write_news
from app.monitoring_cycle import collect_observations


SECTIONS = (
    "GamesCom",
    "Game Nieuws",
    "Hardware Price Watcher",
    "Game Price Watcher",
    "UAH Deals",
    "Discord Price Watcher",
    "RAM Watcher",
    "GPU Watcher",
    "Aanbevelingen",
)


def build_news_context(*, edition: str = "update", observations: list[dict] | None = None) -> dict:
    """Build the complete fact-based context consumed by Ollama."""
    observations = observations if observations is not None else collect_observations()
    context = build_news_context_from_observations(observations, edition=edition)
    context.update({
        "title_suffix": "Late Night Update" if edition == "late-night" else "Update",
        "round_up_label": "Late Night Round-Up" if edition == "late-night" else "Round-Up",
        "sections": list(SECTIONS),
        "late_night": edition == "late-night",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
    return context


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edition", choices=("update", "late-night"), default="update")
    args = parser.parse_args()
    context = build_news_context(edition=args.edition)
    article = write_news(context)
    if not article:
        raise RuntimeError("Ollama returned an empty news article")
    send_news(article)


if __name__ == "__main__":
    main()
