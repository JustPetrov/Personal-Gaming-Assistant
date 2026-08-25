from pathlib import Path

from storage.change_detection import ChangeDetector


def test_new_observation_gets_priority_and_change_metadata(tmp_path: Path):
    detector = ChangeDetector(str(tmp_path / "state.json"))
    changed = detector.process([{
        "type": "gamescom_ticket_status",
        "source": "gamescom",
        "product": "Friday",
        "stock": "Available",
    }])
    assert changed[0]["change"] == "new"
    assert changed[0]["priority"] == "HIGH"
    assert changed[0]["observation_key"] == "gamescom|gamescom_ticket_status|Friday|state"


def test_repeated_observation_is_deduplicated(tmp_path: Path):
    detector = ChangeDetector(str(tmp_path / "state.json"))
    observation = {"type": "price", "source": "SteamDB", "product": "Game", "price": "9.99", "checked_at": "one"}
    assert len(detector.process([observation])) == 1
    observation["checked_at"] = "two"
    assert detector.process([observation]) == []


def test_explicit_priority_wins(tmp_path: Path):
    detector = ChangeDetector(str(tmp_path / "state.json"))
    changed = detector.process([{
        "type": "price",
        "source": "SteamDB",
        "product": "Game",
        "price": "1.99",
        "priority": "CRITICAL",
    }])
    assert changed[0]["priority"] == "CRITICAL"
