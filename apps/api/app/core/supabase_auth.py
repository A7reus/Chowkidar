from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class SupabaseAuthError(RuntimeError):
    """A user-safe error returned by the Supabase Auth adapter."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after


def _auth_url(path: str) -> str:
    settings = get_settings()
    if not settings.supabase_url:
        raise SupabaseAuthError(
            "Supabase Auth is not configured on this deployment.",
            status_code=503,
        )
    if not settings.supabase_anon_key:
        raise SupabaseAuthError(
            "Supabase Auth public key is not configured on this deployment.",
            status_code=503,
        )
    return f"{settings.supabase_url.rstrip('/')}/auth/v1/{path.lstrip('/')}"


def _headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "apikey": settings.supabase_anon_key,
        "Authorization": f"Bearer {settings.supabase_anon_key}",
        "Content-Type": "application/json",
    }


def _error_message(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("error_description", "msg", "message", "error"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return "Supabase Auth rejected the request."


async def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=settings.supabase_auth_timeout_seconds) as client:
            response = await client.post(
                _auth_url(path),
                headers=_headers(),
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise SupabaseAuthError(
            "Authentication service is temporarily unavailable.",
            status_code=503,
        ) from exc

    try:
        body = response.json()
    except ValueError:
        body = {}

    if response.status_code in {400, 401, 403, 422}:
        raise SupabaseAuthError(
            "Invalid email or password." if "password" in path else _error_message(body),
            status_code=401,
        )
    if response.status_code == 429:
        retry_after = response.headers.get("retry-after")
        raise SupabaseAuthError(
            "Too many authentication attempts. Try again shortly.",
            status_code=429,
            retry_after=int(retry_after) if retry_after and retry_after.isdigit() else 60,
        )
    if response.status_code >= 500:
        raise SupabaseAuthError(
            "Authentication service is temporarily unavailable.",
            status_code=503,
        )
    if response.status_code >= 400:
        raise SupabaseAuthError(_error_message(body), status_code=response.status_code)
    if not isinstance(body, dict):
        raise SupabaseAuthError("Authentication service returned an invalid response.")
    return body


async def password_login(email: str, password: str) -> dict[str, Any]:
    return await _post(
        "token?grant_type=password",
        {"email": email.strip().lower(), "password": password},
    )


async def refresh_session(refresh_token: str) -> dict[str, Any]:
    return await _post(
        "token?grant_type=refresh_token",
        {"refresh_token": refresh_token},
    )


async def revoke_session(access_token: str) -> None:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=settings.supabase_auth_timeout_seconds) as client:
            await client.post(
                _auth_url("logout"),
                headers={
                    **_headers(),
                    "Authorization": f"Bearer {access_token}",
                },
            )
    except (httpx.HTTPError, SupabaseAuthError):
        # Logout is best-effort. The client clears its local session either way.
        return
