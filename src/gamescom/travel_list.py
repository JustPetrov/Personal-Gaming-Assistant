from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4


DEFAULT_TRAVEL_TASKS = (
    "Standplanning maken",
    "Beurshallen / locaties bepalen",
    "Persoonlijke must-visits toevoegen",
    "EPIX Quest locaties toevoegen",
    "Eten/drinken plannen",
)

STORE_PATH = Path("data/state/gamescom_travel_list.json")
PRIORITIES = {"low", "normal", "high"}


@dataclass
class TravelTask:
    title: str
    completed: bool = False
    priority: str = "normal"
    note: str | None = None
    day: str | None = None
    location: str | None = None
    task_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("Travel task title cannot be empty")
        if self.priority not in PRIORITIES:
            raise ValueError("Travel task priority must be low, normal or high")


def _write(tasks: list[TravelTask], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "tasks": [asdict(task) for task in tasks],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_travel_list(*, path: Path = STORE_PATH) -> list[TravelTask]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    raw_tasks = payload.get("tasks", []) if isinstance(payload, dict) else []
    return [TravelTask(**item) for item in raw_tasks if isinstance(item, dict)]


def save_travel_list(tasks: list[TravelTask], *, path: Path = STORE_PATH) -> None:
    _write(tasks, path)


def build_travel_list(tasks: list[str] | None = None, *, path: Path | None = None) -> list[TravelTask]:
    """Return persisted GamesCom travel tasks, optionally creating defaults."""
    target = path or STORE_PATH
    existing = load_travel_list(path=target)
    if existing:
        return existing
    created = [TravelTask(title) for title in (tasks or DEFAULT_TRAVEL_TASKS)]
    save_travel_list(created, path=target)
    return created


def add_task(
    title: str,
    *,
    priority: str = "normal",
    note: str | None = None,
    day: str | None = None,
    location: str | None = None,
    path: Path = STORE_PATH,
) -> TravelTask:
    tasks = load_travel_list(path=path)
    task = TravelTask(title, priority=priority, note=note, day=day, location=location)
    tasks.append(task)
    save_travel_list(tasks, path=path)
    return task


def update_task(task_id: str, *, path: Path = STORE_PATH, **changes) -> TravelTask:
    tasks = load_travel_list(path=path)
    for task in tasks:
        if task.task_id != task_id:
            continue
        allowed = {"title", "completed", "priority", "note", "day", "location"}
        for key, value in changes.items():
            if key in allowed:
                setattr(task, key, value)
        if not task.title.strip():
            raise ValueError("Travel task title cannot be empty")
        if task.priority not in PRIORITIES:
            raise ValueError("Travel task priority must be low, normal or high")
        task.title = task.title.strip()
        task.updated_at = datetime.now(timezone.utc).isoformat()
        save_travel_list(tasks, path=path)
        return task
    raise KeyError(f"Unknown travel task: {task_id}")


def remove_task(task_id: str, *, path: Path = STORE_PATH) -> None:
    tasks = load_travel_list(path=path)
    filtered = [task for task in tasks if task.task_id != task_id]
    if len(filtered) == len(tasks):
        raise KeyError(f"Unknown travel task: {task_id}")
    save_travel_list(filtered, path=path)


def set_completed(task_id: str, completed: bool = True, *, path: Path = STORE_PATH) -> TravelTask:
    return update_task(task_id, completed=completed, path=path)
