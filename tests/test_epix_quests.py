from src.watchers.epix_quests import EpixQuest, EpixQuestState


def test_new_quests_are_detected_and_saved(tmp_path):
    state = EpixQuestState(tmp_path / "epix.json")
    quests = [EpixQuest("Quest A", "https://example.test/a")]
    assert state.new_quests(quests) == quests
    assert state.new_quests(quests) == []


def test_only_new_quest_is_returned(tmp_path):
    state = EpixQuestState(tmp_path / "epix.json")
    state.save([EpixQuest("Quest A", "https://example.test/a")])
    new = EpixQuest("Quest B", "https://example.test/b")
    assert state.new_quests([
        EpixQuest("Quest A", "https://example.test/a"),
        new,
    ]) == [new]
