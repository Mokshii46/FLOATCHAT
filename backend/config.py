"""
Central app configuration. Reads from environment variables (via .env),
so every other module imports `settings` from here instead of calling
os.environ directly.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg2://floatchat:floatchat@localhost:5432/floatchat"

    # LLM
    llm_provider: str = "anthropic"
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Vector store
    vector_db_path: str = "./data/vectorstore"
    vector_db_backend: str = "chroma"

    # ARGO
    argo_region: str = "indian_ocean"
    argo_lookback_years: int = 3

    # Voice
    stt_provider: str = "whisper"
    tts_provider: str = "none"

    # App
    app_env: str = "development"
    backend_port: int = 8000
    frontend_port: int = 5173
    default_mode: str = "citizen"          # "citizen" | "researcher" — USP 6
    default_language: str = "en"           # USP 2

    # Query safety (used by nl2sql/sql_validator.py)
    max_result_rows: int = 5000
    query_timeout_seconds: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()