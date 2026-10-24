from __future__ import annotations

import pytest
from app.core.config import ROOT_DIR, Settings
from pydantic import ValidationError


def test_project_root_contains_demo_fixture() -> None:
    assert (ROOT_DIR / "data" / "fixtures" / "demo.json").exists()


def test_database_url_accepts_supabase_style_scheme() -> None:
    settings = Settings(database_url="postgresql://user:pass@host:5432/postgres")
    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/postgres"


def test_database_url_accepts_legacy_postgres_scheme() -> None:
    settings = Settings(database_url="postgres://user:pass@host:5432/postgres")
    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/postgres"


def test_database_url_keeps_explicit_driver() -> None:
    url = "postgresql+psycopg://user:pass@host:5432/postgres"
    assert Settings(database_url=url).database_url == url


def test_supabase_auth_requires_url_and_anon_key() -> None:
    with pytest.raises(ValidationError, match="SUPABASE_URL and SUPABASE_ANON_KEY"):
        Settings(auth_mode="supabase", demo_mode=False)


def test_supabase_storage_requires_service_role_key() -> None:
    with pytest.raises(ValidationError, match="SUPABASE_SERVICE_ROLE_KEY"):
        Settings(
            supabase_url="https://example.supabase.co",
            supabase_anon_key="anon",
            storage_backend="supabase",
        )


def test_invalid_storage_backend_is_rejected() -> None:
    with pytest.raises(ValidationError, match="STORAGE_BACKEND"):
        Settings(storage_backend="s3")
