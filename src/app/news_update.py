from __future__ import annotations

import argparse
from datetime import datetime, timezone


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


def build_news_context(*, edition: str = "update") -> dict:
    """Return the stable structure consumed by the Ollama news writer."""
    normalized = "late-night" if edition == "late-night" else "update"
    return {
        "edition": normalized,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title_suffix": "Late Night Update" if normalized == "late-night" else "Update",
        "round_up_label": "Late Night Round-Up" if normalized == "late-night" else "Round-Up",
        "sections": list(SECTIONS),
        "late_night": normalized == "late-night",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edition", choices=("update", "late-night"), default="update")
    args = parser.parse_args()
    context = build_news_context(edition=args.edition)
    print(context)


if __name__ == "__main__":
    main()
