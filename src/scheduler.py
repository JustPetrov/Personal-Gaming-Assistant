from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from main import build_update, load_config
from run_all_watchers import run_all


def run_update(roundup: bool = False) -> None:
    config = load_config()
    result = run_all(roundup=roundup)
    print(build_update(config, roundup=roundup), flush=True)
    print(f"Full watcher run completed: {result['update']}", flush=True)


def main() -> None:
    config = load_config()
    scheduler = BlockingScheduler(timezone=config["timezone"])
    for time_string in config["update_times"]:
        hour, minute = map(int, time_string.split(":"))
        scheduler.add_job(
            run_update,
            CronTrigger(hour=hour, minute=minute, timezone=config["timezone"]),
            id=f"update-{time_string.replace(':', '')}",
            replace_existing=True,
            kwargs={"roundup": time_string == config["late_night_roundup_at"]},
            max_instances=1,
            coalesce=True,
        )
    scheduler.start()


if __name__ == "__main__":
    main()
