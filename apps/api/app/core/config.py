from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
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
    supabase_jwt_secret: str = ""
    supabase_jwt_audience: str = "authenticated"
    supabase_storage_bucket: str = "chowkidar-documents"
    supabase_auth_timeout_seconds: int = 15
    rate_limit_enabled: bool = True
    auth_rate_limit_per_minute: int = 10
    mutation_rate_limit_per_minute: int = 30
    storage_backend: str = "local"  # local | database | supabase
    report_storage_bucket: str = "chowkidar-reports"

    llm_mode: str = "mock"  # mock | live | hybrid
    data_mode: str = "fixture"  # fixture | live | hybrid
    embedding_mode: str = "mock"  # mock | live
    embedding_dim: int = 1024
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    gemini_api_key: str = ""
    groq_api_key: str = ""
    gemini_flash_model: str = "gemini/gemini-3.5-flash"
    gemini_pro_model: str = "gemini/gemini-3.5-flash"
    groq_model: str = "groq/openai/gpt-oss-120b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "ollama/qwen2.5:7b"
    ollama_enabled: bool = False
    llm_prefer_local: bool = False
    llm_timeout_seconds: int = 25
    llm_provider_cooldown_seconds: int = 90

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "chowkidar-dev"
    neo4j_database: str = "neo4j"

    internal_api_key: str = "change-me-internal"
    enable_scheduler: bool = False
    scheduler_interval_minutes: int = 60
    scheduler_run_on_start: bool = False
    n8n_api_url: str = "http://localhost:5678"

    live_connector_timeout_seconds: int = 25
    live_connector_max_records: int = 10
    live_connector_user_agent: str = (
        "Chowkidar/0.1 (compliance-risk pilot; +https://github.com/A7reus/Chowkidar)"
    )

    sentry_dsn: str = ""
    posthog_key: str = ""
    posthog_host: str = "https://us.i.posthog.com"
    phoenix_enabled: bool = False
    phoenix_collector_endpoint: str = "http://localhost:6006"

    local_storage_dir: str = "./storage"
    report_storage_dir: str = "./storage/reports"
    upload_storage_dir: str = "./storage/uploads"

    pipeline_max_signals: int = Field(default=20, ge=1, le=100)
    pipeline_live_max_signals: int = Field(default=6, ge=1, le=30)
    pipeline_max_repair_attempts: int = Field(default=1, ge=0, le=3)

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return "postgresql+psycopg://" + value.removeprefix("postgres://")
            if value.startswith("postgresql://"):
                return "postgresql+psycopg://" + value.removeprefix("postgresql://")
        return value

    @model_validator(mode="after")
    def _validate_runtime_modes(self) -> Settings:
        if self.auth_mode not in {"dev", "supabase"}:
            raise ValueError("AUTH_MODE must be 'dev' or 'supabase'")
        if self.llm_mode not in {"mock", "live", "hybrid"}:
            raise ValueError("LLM_MODE must be 'mock', 'live', or 'hybrid'")
        if self.data_mode not in {"fixture", "live", "hybrid"}:
            raise ValueError("DATA_MODE must be 'fixture', 'live', or 'hybrid'")
        if self.embedding_mode not in {"mock", "live"}:
            raise ValueError("EMBEDDING_MODE must be 'mock' or 'live'")
        if self.storage_backend not in {"local", "database", "supabase"}:
            raise ValueError("STORAGE_BACKEND must be local, database, or supabase")
        if self.auth_mode == "supabase" and (
            not self.supabase_url or not self.supabase_anon_key
        ):
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY are required when AUTH_MODE=supabase"
            )
        if self.storage_backend == "supabase" and (
            not self.supabase_url or not self.supabase_service_role_key
        ):
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required "
                "when STORAGE_BACKEND=supabase"
            )
        # Hosted production has no persistent disk. If the operator did not
        # choose a backend explicitly, use Postgres so reports survive restarts.
        if self.is_production and "storage_backend" not in self.model_fields_set:
            self.storage_backend = "database"
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def demo_enabled(self) -> bool:
        """Demo access only exists in the dev auth adapter with demo mode on."""
        return self.auth_mode == "dev" and self.demo_mode

    @property
    def supabase_auth_enabled(self) -> bool:
        return self.auth_mode == "supabase"

    @property
    def llm_live_ready(self) -> bool:
        """True when a live/hybrid LLM path has at least one usable provider."""
        if self.llm_mode == "mock":
            return False
        return bool(self.gemini_api_key or self.groq_api_key or self.ollama_enabled)

    @property
    def live_connectors_enabled(self) -> bool:
        return self.data_mode in {"live", "hybrid"}

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
