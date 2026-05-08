"""tests/unit/test_routes.py"""

import pytest
from fastapi.testclient import TestClient

from sa_resident_agent.api.app import create_app
from sa_resident_agent.api.routes import set_agent
from sa_resident_agent.agent.agent import Agent


@pytest.fixture(scope="module")
def client(temp_chroma_dir, mock_llm, populated_store):
    """TestClient with a real Agent backed by mock LLM and populated ChromaDB."""
    agent = Agent(chroma_path=temp_chroma_dir, llm=mock_llm)
    set_agent(agent)
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_response_fields(client):
    resp = client.get("/health")
    data = resp.json()
    assert "status"        in data
    assert "chroma_docs"   in data
    assert "llm_reachable" in data


def test_health_chroma_docs_positive(client):
    resp = client.get("/health")
    assert resp.json()["chroma_docs"] > 0


def test_chat_returns_200(client):
    resp = client.post("/chat", json={"session_id": "t-01", "message": "What are CPS Energy rates?"})
    assert resp.status_code == 200


def test_chat_response_fields(client):
    resp = client.post("/chat", json={"session_id": "t-02", "message": "How do I start SAWS service?"})
    data = resp.json()
    assert "session_id" in data
    assert "reply"      in data
    assert "intent"     in data
    assert "sources"    in data
    assert "checklist"  in data


def test_chat_reply_not_empty(client):
    resp = client.post("/chat", json={"session_id": "t-03", "message": "What documents do I need?"})
    assert len(resp.json()["reply"]) > 0


def test_chat_intent_is_valid(client):
    resp = client.post("/chat", json={"session_id": "t-04", "message": "What are the rates?"})
    assert resp.json()["intent"] in ("QUESTION", "FORM_HELP", "STATUS")


def test_empty_message_returns_422(client):
    resp = client.post("/chat", json={"session_id": "t-05", "message": ""})
    assert resp.status_code == 422


def test_missing_session_id_returns_422(client):
    resp = client.post("/chat", json={"message": "Hello"})
    assert resp.status_code == 422


def test_missing_message_returns_422(client):
    resp = client.post("/chat", json={"session_id": "t-06"})
    assert resp.status_code == 422


def test_status_returns_200(client):
    client.post("/chat", json={"session_id": "t-07", "message": "Tell me about CPS Energy"})
    resp = client.get("/status/t-07")
    assert resp.status_code == 200


def test_status_response_fields(client):
    client.post("/chat", json={"session_id": "t-08", "message": "Tell me about SAWS"})
    resp = client.get("/status/t-08")
    data = resp.json()
    assert "session_id"  in data
    assert "checklist"   in data
    assert "turn_count"  in data


def test_status_turn_count_increments(client):
    client.post("/chat", json={"session_id": "t-09", "message": "Question 1"})
    client.post("/chat", json={"session_id": "t-09", "message": "Question 2"})
    resp = client.get("/status/t-09")
    assert resp.json()["turn_count"] == 2


def test_reset_returns_200(client):
    resp = client.post("/reset", json={"session_id": "t-10"})
    assert resp.status_code == 200


def test_reset_response_has_reset_true(client):
    resp = client.post("/reset", json={"session_id": "t-11"})
    assert resp.json()["reset"] is True


def test_reset_clears_turn_count(client):
    client.post("/chat", json={"session_id": "t-12", "message": "Hello"})
    client.post("/reset", json={"session_id": "t-12"})
    resp = client.get("/status/t-12")
    assert resp.json()["turn_count"] == 0


def test_checklist_values_are_valid_strings(client):
    resp = client.post("/chat", json={"session_id": "t-13", "message": "CPS Energy rates"})
    checklist = resp.json()["checklist"]
    valid = {"NOT_STARTED", "IN_PROGRESS", "COMPLETE"}
    for v in checklist.values():
        assert v in valid
