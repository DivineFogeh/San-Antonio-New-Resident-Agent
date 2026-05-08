# app/services/cps_energy.py — CPS Energy integration
import httpx
from app.cache import cache_get, cache_set
import json

CPS_BASE  = "https://www.cpsenergy.com"
CACHE_TTL = 3600  # 1 hour

async def get_service_info() -> dict:
    """Return CPS service info for the AI agent and frontend."""
    cached = await cache_get("cps:service_info")
    if cached:
        return json.loads(cached)

    # Static info — kept current by Member 1's web crawler / knowledge base
    info = {
        "provider":        "CPS Energy",
        "signup_url":      f"{CPS_BASE}/en/residential/start-stop-transfer-service",
        "phone":           "210-353-2222",
        "docs_required":   ["Government-issued ID", "Social Security Number", "SA service address"],
        "avg_processing":  "1–2 business days",
        "notes":           "Electric service only. Natural gas is handled separately by CenterPoint."
    }
    await cache_set("cps:service_info", json.dumps(info), CACHE_TTL)
    return info

async def submit_enrollment(form_data: dict) -> dict:
    """Forward validated form data from Member 2's form engine to CPS."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                f"{CPS_BASE}/api/enrollment",
                json=form_data
            )
            resp.raise_for_status()
            return {"status": "success", "confirmation": resp.json().get("confirmation_number")}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": f"CPS returned {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"status": "error", "detail": str(e)}
