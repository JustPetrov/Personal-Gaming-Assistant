from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import json
from pathlib import Path

from gamescom_web_research import GamesComWebResearch
from orchestrator import run_once, load_config

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def run_all(roundup: bool = False) -> dict:
    config = load_config()
    timezone = config.get("timezone", "Europe/Amsterdam")
    now = datetime.now(ZoneInfo(timezone))

    result = run_once(roundup=roundup)

    # GamesCom research is independent: failure must never prevent price updates.
    try:
        gamescom = GamesComWebResearch().fetch()
        result["gamescom"] = gamescom
    except Exception as exc:
        result["gamescom"] = {"error": str(exc), "last_synced": now.isoformat()}

    update_path = DATA / "updates.json"
    updates = json.loads(update_path.read_text(encoding="utf-8")) if update_path.exists() else []
    updates.append({
        "timestamp": now.isoformat(),
        "type": "late_night_roundup" if roundup else "full",
        "status": "completed",
        "items_checked": len(result.get("prices", [])),
        "gamescom_research": "gamescom" in result,
    })
    update_path.write_text(json.dumps(updates[-100:], ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run_all(), ensure_ascii=False, indent=2))
