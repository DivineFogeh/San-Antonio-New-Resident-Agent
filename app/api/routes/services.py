# app/api/routes/services.py — CPS, SAWS, City SA info + form submission
from fastapi import APIRouter, HTTPException
from app.services import cps_energy, saws, city_sa
from app.schemas import FormSubmitRequest, FormSubmitResponse

router = APIRouter()

@router.get("/cps")
async def get_cps_info():
    return await cps_energy.get_service_info()

@router.get("/saws")
async def get_saws_info():
    return await saws.get_service_info()

@router.get("/city")
async def get_city_info():
    return await city_sa.get_service_info()

@router.post("/submit/{service}", response_model=FormSubmitResponse)
async def submit_form(service: str, payload: FormSubmitRequest):
    """Route validated form data to the correct service integration."""
    handlers = {
        "cps":  cps_energy.submit_enrollment,
        "saws": saws.submit_enrollment,
        "city": city_sa.submit_enrollment,
    }
    handler = handlers.get(service)
    if not handler:
        raise HTTPException(400, f"Unknown service: {service}")

    result = await handler(payload.form_data)
    return FormSubmitResponse(**result)
