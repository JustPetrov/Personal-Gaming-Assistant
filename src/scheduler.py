from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from main import build_update, load_config


def run_update(roundup: bool = False) -> None:
    config = load_config()
    print(build_update(config, roundup=roundup), flush=True)


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
        )

    scheduler.start()


if __name__ == "__main__":
    main()
