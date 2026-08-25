import json

from src.storage.change_detection import ChangeDetector


def test_timestamp_only_change_is_ignored(tmp_path):
    detector = ChangeDetector(tmp_path / "observations.json")
    first = {
        "type": "game_news",
        "source": "Steam",
        "id": "123",
        "title": "New DLC",
        "timestamp": "2026-08-25T15:00:00Z",
    }
    second = {**first, "timestamp": "2026-08-25T15:05:00Z"}

    assert detector.process([first]) == [first]
    assert detector.process([second]) == []


def test_source_and_type_prevent_unknown_identity_collisions(tmp_path):
    detector = ChangeDetector(tmp_path / "observations.json")
    observations = [
        {"type": "ticket", "source": "GamesCom", "id": "friday", "status": "available"},
        {"type": "ticket", "source": "GamesCom", "id": "saturday", "status": "available"},
    ]

    assert len(detector.process(observations)) == 2
    state = json.loads((tmp_path / "observations.json").read_text(encoding="utf-8"))
    assert len(state) == 2
