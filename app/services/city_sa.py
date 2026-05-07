# app/services/city_sa.py — City of San Antonio integration
import httpx
from app.cache import cache_get, cache_set
import json

CITY_BASE = "https://www.sanantonio.gov"
CACHE_TTL = 3600

async def get_service_info() -> dict:
    cached = await cache_get("city:service_info")
    if cached:
        return json.loads(cached)

    info = {
        "provider":       "City of San Antonio",
        "signup_url":     f"{CITY_BASE}/residents/new-residents",
        "phone":          "311",
        "docs_required":  ["Government-issued ID", "SA address proof", "Vehicle info (if registering)"],
        "avg_processing": "Varies by permit/license type",
        "notes":          "Covers city registration, permits, licenses, and solid waste services."
    }
    await cache_set("city:service_info", json.dumps(info), CACHE_TTL)
    return info

async def submit_enrollment(form_data: dict) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(f"{CITY_BASE}/api/registration", json=form_data)
            resp.raise_for_status()
            return {"status": "success", "confirmation": resp.json().get("confirmation_number")}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "detail": f"City SA returned {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"status": "error", "detail": str(e)}
