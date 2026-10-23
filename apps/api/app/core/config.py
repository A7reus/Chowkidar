from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    """Find the repository root locally and the app root inside a container."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "data" / "fixtures" / "demo.json").exists():
            return parent
    for parent in here.parents:
        if (parent / "pnpm-workspace.yaml").exists():
            return parent
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return here.parent


ROOT_DIR = _project_root()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    app_name: str = "Chowkidar"
    api_url: str = "http://localhost:8000"
    web_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://chowkidar:chowkidar@localhost:5432/chowkidar"
    test_database_url: str = (
        "postgresql+psycopg://chowkidar:chowkidar@localhost:5432/chowkidar_test"
    )

    auth_mode: str = "dev"
    dev_jwt_secret: str = "change-me"
    demo_mode: bool = True
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_audience: str = "authenticated"
    supabase_storage_bucket: str = "chowkidar-documents"

    llm_mode: str = "mock"
    data_mode: str = "fixture"
    embedding_mode: str = "mock"
    embedding_dim: int = 1024
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    gemini_api_key: str = ""
    groq_api_key: str = ""
    gemini_flash_model: str = "gemini/gemini-3.8-flash"
    gemini_pro_model: str = "gemini/gemini-pro-latest"
    groq_model: str = "groq/openai/gpt-oss-120b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "ollama/qwen2.5:7b"
    llm_timeout_seconds: int = 45

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "chowkidar-dev"
    neo4j_database: str = "neo4j"

    internal_api_key: str = "change-me-internal"
    enable_scheduler: bool = False
    n8n_api_url: str = "http://localhost:5678"

    sentry_dsn: str = ""
    posthog_key: str = ""
    posthog_host: str = "https://us.i.posthog.com"
    phoenix_enabled: bool = False
    phoenix_collector_endpoint: str = "http://localhost:6006"

    local_storage_dir: str = "./storage"
    report_storage_dir: str = "./storage/reports"
    upload_storage_dir: str = "./storage/uploads"

    pipeline_max_signals: int = Field(default=20, ge=1, le=100)

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return "postgresql+psycopg://" + value.removeprefix("postgres://")
            if value.startswith("postgresql://"):
                return "postgresql+psycopg://" + value.removeprefix("postgresql://")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
