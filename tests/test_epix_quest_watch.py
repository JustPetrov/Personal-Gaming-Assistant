from pathlib import Path

from gamescom.epix_quest_watch import Quest, changed_quests


def test_changed_quests_only_reports_new_or_changed_quest(tmp_path: Path):
    state = tmp_path / "epix.json"
    first = [Quest("Quest A", "https://example.test/a", "fp-a")]
    assert changed_quests(first, str(state)) == first
    assert changed_quests(first, str(state)) == []

    changed = [Quest("Quest A Updated", "https://example.test/a", "fp-a2")]
    assert changed_quests(changed, str(state)) == changed


def test_unrelated_quest_does_not_realert_existing_quest(tmp_path: Path):
    state = tmp_path / "epix.json"
    first = [
        Quest("Quest A", "https://example.test/a", "fp-a"),
        Quest("Quest B", "https://example.test/b", "fp-b"),
    ]
    assert len(changed_quests(first, str(state))) == 2
    second = [
        Quest("Quest A", "https://example.test/a", "fp-a"),
        Quest("Quest B", "https://example.test/b", "fp-b"),
        Quest("Quest C", "https://example.test/c", "fp-c"),
    ]
    assert changed_quests(second, str(state)) == [second[-1]]
