"""tests/unit/test_intent.py"""

from sa_resident_agent.agent.intent import Intent, classify_intent


def test_question_classification(mock_llm):
    intent = classify_intent("What are the CPS Energy residential rates?", mock_llm)
    assert intent == Intent.QUESTION


def test_form_help_classification(mock_llm):
    intent = classify_intent("What should I enter in the service address field?", mock_llm)
    assert intent == Intent.FORM_HELP


def test_status_classification(mock_llm):
    intent = classify_intent("What is my current setup progress?", mock_llm)
    assert intent == Intent.STATUS


def test_empty_message_defaults_to_question(mock_llm):
    intent = classify_intent("", mock_llm)
    assert intent == Intent.QUESTION


def test_whitespace_message_defaults_to_question(mock_llm):
    intent = classify_intent("   ", mock_llm)
    assert intent == Intent.QUESTION


def test_intent_is_enum_value(mock_llm):
    intent = classify_intent("How much does SAWS charge per month?", mock_llm)
    assert isinstance(intent, Intent)


def test_invalid_llm_response_defaults_to_question(mock_llm, monkeypatch):
    """If LLM returns garbage, intent should fall back to QUESTION."""
    monkeypatch.setattr(mock_llm, "chat", lambda *a, **kw: "GARBAGE_LABEL")
    intent = classify_intent("some question", mock_llm)
    assert intent == Intent.QUESTION


def test_llm_error_defaults_to_question(mock_llm, monkeypatch):
    """If LLM raises an exception, intent should fall back to QUESTION."""
    def raise_error(*a, **kw):
        raise ConnectionError("LLM down")
    monkeypatch.setattr(mock_llm, "chat", raise_error)
    intent = classify_intent("some question", mock_llm)
    assert intent == Intent.QUESTION
