from __future__ import annotations

import pytest
from app.core.config import ROOT_DIR, Settings
from pydantic import ValidationError


def _settings(**values: object) -> Settings:
    """Build isolated settings without the developer's local .env overrides."""

    return Settings(_env_file=None, **values)  # pyright: ignore[reportCallIssue]


def test_project_root_contains_demo_fixture() -> None:
    assert (ROOT_DIR / "data" / "fixtures" / "demo.json").exists()


def test_database_url_accepts_supabase_style_scheme() -> None:
    settings = _settings(database_url="postgresql://user:pass@host:5432/postgres")
    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/postgres"


def test_database_url_accepts_legacy_postgres_scheme() -> None:
    settings = _settings(database_url="postgres://user:pass@host:5432/postgres")
    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/postgres"


def test_database_url_keeps_explicit_driver() -> None:
    url = "postgresql+psycopg://user:pass@host:5432/postgres"
    assert _settings(database_url=url).database_url == url


def test_supabase_auth_requires_url_and_anon_key() -> None:
    with pytest.raises(ValidationError, match="SUPABASE_URL and SUPABASE_ANON_KEY"):
        _settings(auth_mode="supabase", demo_mode=False)


def test_supabase_storage_requires_service_role_key() -> None:
    with pytest.raises(ValidationError, match="SUPABASE_SERVICE_ROLE_KEY"):
        _settings(
            supabase_url="https://example.supabase.co",
            supabase_anon_key="anon",
            storage_backend="supabase",
        )


def test_invalid_storage_backend_is_rejected() -> None:
    with pytest.raises(ValidationError, match="STORAGE_BACKEND"):
        _settings(storage_backend="s3")


def test_production_defaults_to_durable_database_storage() -> None:
    settings = _settings(
        app_env="production",
        auth_mode="dev",
        demo_mode=True,
        dev_jwt_secret="test-secret",
    )
    assert settings.storage_backend == "database"


def test_development_defaults_to_local_storage() -> None:
    settings = _settings(app_env="development")
    assert settings.storage_backend == "local"


def test_invalid_runtime_modes_are_rejected() -> None:
    with pytest.raises(ValidationError, match="LLM_MODE"):
        _settings(llm_mode="turbo")
    with pytest.raises(ValidationError, match="DATA_MODE"):
        _settings(data_mode="streaming")
    with pytest.raises(ValidationError, match="EMBEDDING_MODE"):
        _settings(embedding_mode="semantic")


def test_llm_live_ready_requires_a_non_mock_mode_and_a_key() -> None:
    assert _settings(llm_mode="mock", gemini_api_key="key").llm_live_ready is False
    assert _settings(llm_mode="hybrid", gemini_api_key="").llm_live_ready is False
    assert _settings(llm_mode="hybrid", groq_api_key="key").llm_live_ready is True
    assert _settings(llm_mode="live", gemini_api_key="key").llm_live_ready is True


def test_live_connectors_require_live_or_hybrid_data_mode() -> None:
    assert _settings(data_mode="fixture").live_connectors_enabled is False
    assert _settings(data_mode="hybrid").live_connectors_enabled is True
    assert _settings(data_mode="live").live_connectors_enabled is True


def test_repair_attempts_are_bounded() -> None:
    assert _settings().pipeline_max_repair_attempts == 1
    with pytest.raises(ValidationError):
        _settings(pipeline_max_repair_attempts=9)
