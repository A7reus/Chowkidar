from __future__ import annotations

from datetime import UTC, datetime, timedelta

import app.api.v1.auth as auth_module
import app.core.auth as core_auth_module
import app.core.supabase_auth as supabase_module
import httpx
import jwt
import pytest
import respx
from app.core.auth import Role, UserContext
from app.core.config import Settings
from app.core.supabase_auth import SupabaseAuthError
from app.schemas import PasswordLoginRequest, RefreshTokenRequest
from fastapi import HTTPException


def _supabase_settings() -> Settings:
    return Settings(
        auth_mode="supabase",
        demo_mode=False,
        supabase_url="https://example.supabase.co",
        supabase_anon_key="public-anon-key",
    )


@pytest.mark.asyncio
async def test_password_login_proxies_supabase(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _supabase_settings()
    monkeypatch.setattr(auth_module, "get_settings", lambda: settings)
    monkeypatch.setattr(supabase_module, "get_settings", lambda: settings)
    user = UserContext(
        id="11111111-1111-1111-1111-111111111111",
        email="analyst@example.com",
        name="Analyst",
        role=Role.ANALYST,
        is_demo=False,
    )
    monkeypatch.setattr(auth_module, "decode_supabase_token", lambda _token: user)

    async def _resolve(_session: object, _user: UserContext) -> UserContext:
        return user

    monkeypatch.setattr(auth_module, "resolve_workspace_user", _resolve)

    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(
            "https://example.supabase.co/auth/v1/token?grant_type=password"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "access-token",
                    "refresh_token": "refresh-token",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "expires_at": 1900000000,
                },
            )
        )
        response = await auth_module.login(
            PasswordLoginRequest(email=" Analyst@Example.com ", password="correct horse"),
            None,  # type: ignore[arg-type]
        )

    assert route.called
    assert response.access_token == "access-token"
    assert response.refresh_token == "refresh-token"
    assert response.user.email == "analyst@example.com"
    assert response.user.is_demo is False


@pytest.mark.asyncio
async def test_password_login_maps_invalid_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _supabase_settings()
    monkeypatch.setattr(auth_module, "get_settings", lambda: settings)
    monkeypatch.setattr(supabase_module, "get_settings", lambda: settings)

    with respx.mock(assert_all_called=True) as mock:
        mock.post("https://example.supabase.co/auth/v1/token?grant_type=password").mock(
            return_value=httpx.Response(
                400,
                json={"error_description": "Invalid login credentials"},
            )
        )
        with pytest.raises(HTTPException) as error:
            await auth_module.login(
                PasswordLoginRequest(email="analyst@example.com", password="wrong password"),
                None,  # type: ignore[arg-type]
            )

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_requires_refresh_token(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _supabase_settings()
    monkeypatch.setattr(auth_module, "get_settings", lambda: settings)
    monkeypatch.setattr(supabase_module, "get_settings", lambda: settings)

    with respx.mock(assert_all_called=True) as mock:
        mock.post("https://example.supabase.co/auth/v1/token?grant_type=refresh_token").mock(
            return_value=httpx.Response(400, json={"msg": "Invalid Refresh Token"})
        )
        with pytest.raises(HTTPException) as error:
            await auth_module.refresh(
                RefreshTokenRequest(refresh_token="bad-token-value"),
                None,  # type: ignore[arg-type]
            )

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_supabase_auth_requires_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        supabase_module,
        "get_settings",
        lambda: Settings(supabase_url="", supabase_anon_key=""),
    )
    with pytest.raises(SupabaseAuthError) as error:
        await supabase_module.password_login("user@example.com", "password123")
    assert error.value.status_code == 503


def test_new_publishable_key_uses_only_the_apikey_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        auth_mode="supabase",
        demo_mode=False,
        supabase_url="https://example.supabase.co",
        supabase_anon_key="sb_publishable_example",
    )
    monkeypatch.setattr(supabase_module, "get_settings", lambda: settings)
    headers = supabase_module._headers()
    assert headers["apikey"] == "sb_publishable_example"
    assert "Authorization" not in headers


def test_legacy_anon_key_is_also_sent_as_a_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        auth_mode="supabase",
        demo_mode=False,
        supabase_url="https://example.supabase.co",
        supabase_anon_key="legacy-anon-jwt",
    )
    monkeypatch.setattr(supabase_module, "get_settings", lambda: settings)
    headers = supabase_module._headers()
    assert headers["Authorization"] == "Bearer legacy-anon-jwt"


def test_legacy_hs256_supabase_token_is_verified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        auth_mode="supabase",
        demo_mode=False,
        supabase_url="https://example.supabase.co",
        supabase_anon_key="public-anon-key",
        supabase_jwt_secret="legacy-jwt-secret-0123456789abcdef",
    )
    monkeypatch.setattr(core_auth_module, "get_settings", lambda: settings)
    token = jwt.encode(
        {
            "sub": "11111111-1111-1111-1111-111111111111",
            "email": "analyst@example.com",
            "aud": "authenticated",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "app_metadata": {"role": "admin"},
            "user_metadata": {"full_name": "Analyst"},
        },
        "legacy-jwt-secret-0123456789abcdef",
        algorithm="HS256",
    )
    user = core_auth_module.decode_supabase_token(token)
    assert user.email == "analyst@example.com"
    assert user.is_demo is False
