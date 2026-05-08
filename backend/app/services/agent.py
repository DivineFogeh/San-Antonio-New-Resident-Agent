# app/services/agent.py — connects your backend to the crawler/AI agent API
import httpx
import os

AGENT_BASE_URL = os.getenv("AGENT_URL", "http://host.docker.internal:8001")

async def chat(session_id: str, message: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{AGENT_BASE_URL}/chat",
                json={"session_id": session_id, "message": message}
            )
            resp.raise_for_status()
            return {"status": "success", "data": resp.json()}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": f"Agent returned {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"status": "error", "detail": str(e)}

async def simulate(session_id: str, message: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{AGENT_BASE_URL}/simulate",
                json={"session_id": session_id, "message": message}
            )
            resp.raise_for_status()
            return {"status": "success", "data": resp.json()}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": f"Agent returned {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"status": "error", "detail": str(e)}

async def get_session_status(session_id: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{AGENT_BASE_URL}/status/{session_id}")
            resp.raise_for_status()
            return {"status": "success", "data": resp.json()}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": f"Agent returned {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"status": "error", "detail": str(e)}

async def reset_session(session_id: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{AGENT_BASE_URL}/reset",
                json={"session_id": session_id}
            )
            resp.raise_for_status()
            return {"status": "success", "data": resp.json()}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": f"Agent returned {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"status": "error", "detail": str(e)}

async def health_check() -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{AGENT_BASE_URL}/health")
            resp.raise_for_status()
            return {"status": "success", "data": resp.json()}
        except Exception as e:
            return {"status": "error", "detail": str(e)}