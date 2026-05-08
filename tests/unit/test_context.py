"""tests/unit/test_context.py"""

from sa_resident_agent.agent.context import ChecklistStatus


def test_new_session_has_empty_history(context_manager):
    state = context_manager.get_or_create("sess-01")
    assert state.history == []


def test_new_session_checklist_all_not_started(context_manager):
    checklist = context_manager.get_checklist("sess-02")
    for status in checklist.values():
        assert status == ChecklistStatus.NOT_STARTED


def test_turn_count_starts_at_zero(context_manager):
    assert context_manager.get_turn_count("sess-03") == 0


def test_turn_count_increments(context_manager):
    context_manager.add_turn("sess-04", "Hello", "Hi there!")
    assert context_manager.get_turn_count("sess-04") == 1
    context_manager.add_turn("sess-04", "What are rates?", "The rate is 8.8 cents/kWh.")
    assert context_manager.get_turn_count("sess-04") == 2


def test_history_stores_turns(context_manager):
    context_manager.add_turn("sess-05", "User message", "Agent reply")
    history = context_manager.get_history("sess-05")
    assert len(history) == 2
    assert history[0]["role"]    == "user"
    assert history[0]["content"] == "User message"
    assert history[1]["role"]    == "assistant"
    assert history[1]["content"] == "Agent reply"


def test_checklist_advances_on_form_help(context_manager):
    context_manager.advance_checklist("sess-06", "CPS_ENERGY")
    checklist = context_manager.get_checklist("sess-06")
    assert checklist["CPS_ENERGY"] == ChecklistStatus.IN_PROGRESS


def test_checklist_not_started_to_in_progress(context_manager):
    context_manager.advance_checklist("sess-07", "SAWS")
    assert context_manager.get_checklist("sess-07")["SAWS"] == ChecklistStatus.IN_PROGRESS


def test_mark_complete(context_manager):
    context_manager.advance_checklist("sess-08", "CITY_SA")
    context_manager.mark_complete("sess-08", "CITY_SA")
    assert context_manager.get_checklist("sess-08")["CITY_SA"] == ChecklistStatus.COMPLETE


def test_reset_clears_history(context_manager):
    context_manager.add_turn("sess-09", "msg", "reply")
    context_manager.reset("sess-09")
    assert context_manager.get_history("sess-09") == []


def test_reset_clears_checklist(context_manager):
    context_manager.advance_checklist("sess-10", "CPS_ENERGY")
    context_manager.reset("sess-10")
    checklist = context_manager.get_checklist("sess-10")
    for status in checklist.values():
        assert status == ChecklistStatus.NOT_STARTED


def test_reset_clears_turn_count(context_manager):
    context_manager.add_turn("sess-11", "msg", "reply")
    context_manager.reset("sess-11")
    assert context_manager.get_turn_count("sess-11") == 0


def test_status_returns_checklist(context_manager):
    checklist = context_manager.get_checklist("sess-12")
    assert set(checklist.keys()) == {"CPS_ENERGY", "SAWS", "CITY_SA"}


def test_history_trimmed_to_max_turns(context_manager):
    """History should not grow unboundedly — capped at MAX_HISTORY_TURNS * 2 messages."""
    from sa_resident_agent.agent.context import MAX_HISTORY_TURNS
    sid = "sess-trim"
    for i in range(MAX_HISTORY_TURNS + 5):
        context_manager.add_turn(sid, f"msg {i}", f"reply {i}")
    history = context_manager.get_history(sid)
    assert len(history) <= MAX_HISTORY_TURNS * 2
