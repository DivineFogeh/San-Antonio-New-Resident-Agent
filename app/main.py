# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import checklist, services, user, ws
from app.db import engine, Base
from app.cache import init_redis
import uvicorn

app = FastAPI(
    title="SA New Resident Agent API",
    version="1.0.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()

app.include_router(user.router,      prefix="/api/user",      tags=["user"])
app.include_router(checklist.router, prefix="/api/checklist", tags=["checklist"])
app.include_router(services.router,  prefix="/api/services",  tags=["services"])
app.include_router(ws.router,        prefix="/ws",            tags=["websocket"])

@app.get("/")
async def health():
    return {"status": "ok", "service": "SA Resident Agent API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
