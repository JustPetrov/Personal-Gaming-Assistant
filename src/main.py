from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "config.yaml"


def load_config() -> dict:
    with CONFIG.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def current_times(timezone_name: str) -> dict:
    local = datetime.now().astimezone()
    dutch = datetime.now(ZoneInfo(timezone_name))
    return {
        "local_time": local.strftime("%H:%M"),
        "local_date": local.strftime("%Y-%m-%d"),
        "local_timezone": str(local.tzinfo),
        "dutch_time": dutch.strftime("%H:%M"),
        "dutch_date": dutch.strftime("%Y-%m-%d"),
        "dutch_timezone": timezone_name,
    }


def build_update(config: dict, roundup: bool = False) -> str:
    times = current_times(config["timezone"])
    title = "Personal Gaming Assistant — Late Night Round Up" if roundup else "Personal Gaming Assistant — Update"
    lines = [
        f"# 🎮 {title}",
        "",
        "## ℹ️ Informatie",
        f"- 📍 Lokale locatie: configureerbaar via VPS/runtime location provider",
        f"- 🕐 Lokale tijd: **{times['local_time']}** ({times['local_timezone']})",
        f"- 📅 Lokale datum: **{times['local_date']}**",
        f"- 🇳🇱 Nederlandse tijd: **{times['dutch_time']}** ({times['dutch_timezone']})",
        f"- 📅 Nederlandse datum: **{times['dutch_date']}**",
        "",
        "Watchers will be populated by their dedicated modules.",
    ]
    return "\n".join(lines)


def main() -> None:
    config = load_config()
    print(build_update(config))


if __name__ == "__main__":
    main()
