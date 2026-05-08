"""
tests/user_stories/test_us01.py through test_us08.py combined.
Each story maps directly to STORIES.md acceptance criteria.
"""

import pytest
from fastapi.testclient import TestClient
from sa_resident_agent.api.app import create_app
from sa_resident_agent.api.routes import set_agent
from sa_resident_agent.agent.agent import Agent


@pytest.fixture(scope="module")
def client(temp_chroma_dir, mock_llm, populated_store):
    agent = Agent(chroma_path=temp_chroma_dir, llm=mock_llm)
    set_agent(agent)
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# US-01: Ask about CPS Energy rates
# ---------------------------------------------------------------------------

def test_us01_cps_rate_question(client):
    resp = client.post("/chat", json={
        "session_id": "us01",
        "message": "What are the current CPS Energy residential rates?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "QUESTION"
    assert len(data["reply"]) > 0
    providers = [s["provider"] for s in data["sources"]]
    assert "CPS_ENERGY" in providers


# ---------------------------------------------------------------------------
# US-02: Ask about SAWS water service requirements
# ---------------------------------------------------------------------------

def test_us02_saws_document_question(client):
    resp = client.post("/chat", json={
        "session_id": "us02",
        "message": "What documents do I need to sign up for SAWS?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "QUESTION"
    assert len(data["reply"]) > 0
    providers = [s["provider"] for s in data["sources"]]
    assert "SAWS" in providers


# ---------------------------------------------------------------------------
# US-03: Ask about City of San Antonio permits
# ---------------------------------------------------------------------------

def test_us03_city_registration_question(client):
    resp = client.post("/chat", json={
        "session_id": "us03",
        "message": "How do I register with the City of San Antonio as a new resident?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "QUESTION"
    assert len(data["reply"]) > 0


# ---------------------------------------------------------------------------
# US-04: Get form field guidance
# ---------------------------------------------------------------------------

def test_us04_form_field_guidance(client):
    resp = client.post("/chat", json={
        "session_id": "us04",
        "message": "What should I enter for the service address field on the CPS Energy form?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "FORM_HELP"
    assert len(data["reply"]) > 0
    valid_statuses = {"NOT_STARTED", "IN_PROGRESS", "COMPLETE"}
    assert data["checklist"]["CPS_ENERGY"] in valid_statuses


# ---------------------------------------------------------------------------
# US-05: Check setup progress checklist
# ---------------------------------------------------------------------------

def test_us05_checklist_status(client):
    # Send at least one message first
    client.post("/chat", json={"session_id": "us05", "message": "Tell me about CPS Energy rates"})
    resp = client.get("/status/us05")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["checklist"].keys()) == {"CPS_ENERGY", "SAWS", "CITY_SA"}
    valid = {"NOT_STARTED", "IN_PROGRESS", "COMPLETE"}
    for v in data["checklist"].values():
        assert v in valid
    assert data["turn_count"] >= 1


# ---------------------------------------------------------------------------
# US-06: Reset session and start over
# ---------------------------------------------------------------------------

def test_us06_session_reset(client):
    client.post("/chat", json={"session_id": "us06", "message": "Tell me about SAWS"})
    reset_resp = client.post("/reset", json={"session_id": "us06"})
    assert reset_resp.status_code == 200
    assert reset_resp.json()["reset"] is True

    status_resp = client.get("/status/us06")
    data = status_resp.json()
    for v in data["checklist"].values():
        assert v == "NOT_STARTED"
    assert data["turn_count"] == 0


# ---------------------------------------------------------------------------
# US-07: Handle unanswerable question gracefully
# ---------------------------------------------------------------------------

def test_us07_unanswerable_question(client):
    resp = client.post("/chat", json={
        "session_id": "us07",
        "message": "What is the capital of France?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["reply"]) > 0
    # Should not hallucinate — reply should not confidently assert "Paris" as utility info
    assert data.get("error") is None


# ---------------------------------------------------------------------------
# US-08: Handle empty message input
# ---------------------------------------------------------------------------

def test_us08_empty_message_validation(client):
    resp = client.post("/chat", json={"session_id": "us08", "message": ""})
    assert resp.status_code == 422
