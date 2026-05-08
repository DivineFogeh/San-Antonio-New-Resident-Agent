# app/api/routes/services.py — CPS, SAWS, City SA info + form submission
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import cps_energy, saws, city_sa
from app.services import agent as agent_service
from app.schemas import FormSubmitRequest, FormSubmitResponse

router = APIRouter()

class AgentRequest(BaseModel):
    session_id: str
    message: str

class ResetRequest(BaseModel):
    session_id: str

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

@router.post("/agent/chat")
async def agent_chat(payload: AgentRequest):
    return await agent_service.chat(payload.session_id, payload.message)

@router.post("/agent/simulate")
async def agent_simulate(payload: AgentRequest):
    return await agent_service.simulate(payload.session_id, payload.message)

@router.get("/agent/status/{session_id}")
async def agent_status(session_id: str):
    return await agent_service.get_session_status(session_id)

@router.post("/agent/reset")
async def agent_reset(payload: ResetRequest):
    return await agent_service.reset_session(payload.session_id)