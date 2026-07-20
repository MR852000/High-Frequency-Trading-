"""
Centralized application configuration.

All values are read from environment variables (or a local `.env` file in
development). Nothing is hard-coded so the same image can run locally,
in CI, and in production simply by swapping environment variables.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App metadata ---
    APP_NAME: str = "HFT Backtesting & Signal Engine"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # --- Database (PostgreSQL) ---
    DATABASE_URL: str = (
        "postgresql+asyncpg://hft_user:hft_password@db:5432/hft_engine"
    )

    # --- Cache / pub-sub (Redis) ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- Security ---
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
