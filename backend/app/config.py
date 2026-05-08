# app/config.py — Environment settings via pydantic-settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://sa_user:sa_pass@localhost:5432/sa_agent"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "change-me-in-production"

    class Config:
        env_file = ".env"

settings = Settings()
