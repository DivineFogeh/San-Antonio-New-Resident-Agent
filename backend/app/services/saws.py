# app/services/saws.py — San Antonio Water System integration
import httpx
from app.cache import cache_get, cache_set
import json

SAWS_BASE = "https://www.saws.org"
CACHE_TTL = 3600

async def get_service_info() -> dict:
    cached = await cache_get("saws:service_info")
    if cached:
        return json.loads(cached)

    info = {
        "provider":       "SAWS (San Antonio Water System)",
        "signup_url":     f"{SAWS_BASE}/service/moving/",
        "phone":          "210-704-7297",
        "docs_required":  ["Government-issued ID", "SA service address", "Move-in date"],
        "avg_processing": "1 business day",
        "notes":          "Covers water, wastewater, and recycled water services."
    }
    await cache_set("saws:service_info", json.dumps(info), CACHE_TTL)
    return info

async def submit_enrollment(form_data: dict) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(f"{SAWS_BASE}/api/enrollment", json=form_data)
            resp.raise_for_status()
            return {"status": "success", "confirmation": resp.json().get("confirmation_number")}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": f"SAWS returned {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"status": "error", "detail": str(e)}
