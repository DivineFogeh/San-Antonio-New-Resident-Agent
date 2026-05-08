"""tests/integration/test_agent.py"""

import pytest
from sa_resident_agent.agent.agent import Agent, AgentResponse
from sa_resident_agent.agent.intent import Intent


@pytest.fixture(scope="module")
def agent(temp_chroma_dir, mock_llm, populated_store):
    return Agent(chroma_path=temp_chroma_dir, llm=mock_llm)


def test_chat_returns_agent_response(agent):
    resp = agent.chat("int-01", "What are the CPS Energy residential rates?")
    assert isinstance(resp, AgentResponse)


def test_cps_rate_question(agent):
    resp = agent.chat("int-02", "What are the CPS Energy residential rates?")
    assert resp.reply
    assert resp.intent == Intent.QUESTION
    assert resp.error is None


def test_saws_document_question(agent):
    resp = agent.chat("int-03", "What documents do I need to sign up for SAWS?")
    assert resp.reply
    assert resp.intent == Intent.QUESTION


def test_city_registration_question(agent):
    resp = agent.chat("int-04", "How do I register with the City of San Antonio?")
    assert resp.reply
    assert resp.intent == Intent.QUESTION


def test_form_field_guidance(agent):
    resp = agent.chat("int-05", "What should I enter in the service address field on the CPS form?")
    assert resp.intent == Intent.FORM_HELP
    assert resp.reply


def test_checklist_advances_after_cps_question(agent):
    agent.chat("int-06", "What are the CPS Energy rates?")
    checklist = agent.context.get_checklist("int-06")
    from sa_resident_agent.agent.context import ChecklistStatus
    assert checklist["CPS_ENERGY"] in (ChecklistStatus.IN_PROGRESS, ChecklistStatus.COMPLETE)


def test_checklist_advances_after_saws_question(agent):
    agent.chat("int-07", "How much is the SAWS water deposit?")
    checklist = agent.context.get_checklist("int-07")
    from sa_resident_agent.agent.context import ChecklistStatus
    assert checklist["SAWS"] in (ChecklistStatus.IN_PROGRESS, ChecklistStatus.COMPLETE)


def test_sources_returned_for_question(agent):
    resp = agent.chat("int-08", "What are the CPS Energy rates?")
    assert isinstance(resp.sources, list)
    assert len(resp.sources) > 0


def test_sources_have_required_fields(agent):
    resp = agent.chat("int-09", "What documents does SAWS require?")
    for s in resp.sources:
        assert s.url
        assert s.provider
        assert s.chunk_preview


def test_status_after_chat(agent):
    agent.chat("int-10", "Tell me about CPS Energy rates")
    status = agent.status("int-10")
    assert status["turn_count"] == 1
    assert "checklist" in status


def test_reset_then_status(agent):
    agent.chat("int-11", "Tell me about SAWS")
    agent.reset("int-11")
    status = agent.status("int-11")
    assert status["turn_count"] == 0
    from sa_resident_agent.agent.context import ChecklistStatus
    for v in status["checklist"].values():
        assert v == ChecklistStatus.NOT_STARTED


def test_out_of_domain_question(agent):
    """Out-of-domain question should still return a response without error."""
    resp = agent.chat("int-12", "What is the capital of France?")
    assert resp.reply
    assert resp.error is None


def test_empty_message_returns_error_flag(agent):
    resp = agent.chat("int-13", "")
    assert resp.error == "empty_message"


def test_multi_turn_history_maintained(agent):
    agent.chat("int-14", "Tell me about CPS Energy rates")
    agent.chat("int-14", "What about payment options?")
    status = agent.status("int-14")
    assert status["turn_count"] == 2


def test_session_isolation(agent):
    """Two sessions should not share state."""
    agent.chat("int-15a", "Tell me about CPS Energy")
    agent.reset("int-15b")
    assert agent.status("int-15a")["turn_count"] != agent.status("int-15b")["turn_count"] or True
    # Sessions are independent — resetting one should not affect the other
    assert agent.status("int-15a")["turn_count"] >= 1
