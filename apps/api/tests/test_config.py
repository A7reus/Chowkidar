from __future__ import annotations

from app.core.config import ROOT_DIR, Settings


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
