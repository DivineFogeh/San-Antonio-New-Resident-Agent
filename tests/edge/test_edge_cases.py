"""tests/edge/test_edge_cases.py"""

import pytest
from sa_resident_agent.agent.agent import Agent
from sa_resident_agent.agent.intent import classify_intent, Intent
from sa_resident_agent.crawlers.base_crawler import CrawledPage


@pytest.fixture(scope="module")
def agent(temp_chroma_dir, mock_llm, populated_store):
    return Agent(chroma_path=temp_chroma_dir, llm=mock_llm)


# ---------------------------------------------------------------------------
# Input edge cases
# ---------------------------------------------------------------------------

def test_empty_input(agent):
    resp = agent.chat("edge-01", "")
    assert resp.error == "empty_message"


def test_whitespace_only_input(agent):
    resp = agent.chat("edge-02", "     ")
    assert resp.error == "empty_message"


def test_very_long_message(agent):
    long_msg = "What are the CPS Energy rates? " * 100
    resp = agent.chat("edge-03", long_msg)
    assert resp.reply
    assert resp.error is None


def test_special_characters_in_message(agent):
    resp = agent.chat("edge-04", "What's the rate!? @CPS #energy $bill")
    assert resp.reply
    assert resp.error is None


def test_numeric_only_message(agent):
    resp = agent.chat("edge-05", "12345")
    assert resp.reply
    assert resp.error is None


def test_out_of_domain_input(agent):
    """Query completely unrelated to SA utilities should not crash."""
    resp = agent.chat("edge-06", "What is the capital of France?")
    assert resp.reply
    assert resp.error is None


def test_repeated_same_message(agent):
    """Sending the same message multiple times should work consistently."""
    msg = "What are the CPS Energy rates?"
    resp1 = agent.chat("edge-07", msg)
    resp2 = agent.chat("edge-07", msg)
    assert resp1.reply
    assert resp2.reply


def test_sql_injection_like_input(agent):
    """Adversarial input should not crash the system."""
    resp = agent.chat("edge-08", "'; DROP TABLE chunks; --")
    assert resp.error is None


def test_emoji_in_message(agent):
    resp = agent.chat("edge-09", "How do I set up electricity? ⚡🏠")
    assert resp.reply


# ---------------------------------------------------------------------------
# Chunker edge cases
# ---------------------------------------------------------------------------

def test_chunker_handles_unicode(chunker):
    page = CrawledPage(
        url="https://example.com",
        provider="CPS_ENERGY",
        title="Unicode Test",
        text="La energía eléctrica residencial cuesta aproximadamente 8.8 centavos por kWh. " * 5,
        scraped_at="2026-05-01T00:00:00+00:00",
    )
    chunks = chunker.chunk(page)
    assert len(chunks) > 0


def test_chunker_handles_repeated_whitespace(chunker):
    page = CrawledPage(
        url="https://example.com",
        provider="SAWS",
        title="Whitespace Test",
        text="Start    water   service   today.\n\n\n\nCall   SAWS   at   210-704-7297." * 5,
        scraped_at="2026-05-01T00:00:00+00:00",
    )
    chunks = chunker.chunk(page)
    assert len(chunks) > 0


# ---------------------------------------------------------------------------
# Intent edge cases
# ---------------------------------------------------------------------------

def test_intent_mixed_signals(mock_llm):
    """Message that could be QUESTION or FORM_HELP — should return a valid intent."""
    intent = classify_intent(
        "What should I fill in for the address field on the CPS rate form?",
        mock_llm
    )
    assert intent in Intent.__members__.values()


def test_intent_very_short_message(mock_llm):
    intent = classify_intent("rates?", mock_llm)
    assert isinstance(intent, Intent)


def test_intent_all_caps_message(mock_llm):
    intent = classify_intent("WHAT ARE THE CPS ENERGY RATES?", mock_llm)
    assert isinstance(intent, Intent)


# ---------------------------------------------------------------------------
# Session edge cases
# ---------------------------------------------------------------------------

def test_status_on_nonexistent_session(agent):
    """Requesting status for a session that never sent a message."""
    status = agent.status("never-existed-session")
    assert status["turn_count"] == 0
    assert "checklist" in status


def test_reset_nonexistent_session(agent):
    """Resetting a session that never existed should not crash."""
    result = agent.reset("also-never-existed")
    assert result["reset"] is True
