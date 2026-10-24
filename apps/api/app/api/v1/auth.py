from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import CurrentUser, SessionDep, bearer_scheme
from app.core.auth import (
    DEMO_USERS,
    Role,
    UserContext,
    create_dev_token,
    decode_supabase_token,
    demo_user_for_role,
)
from app.core.config import get_settings
from app.core.ratelimit import rate_limit
from app.core.supabase_auth import (
    SupabaseAuthError,
    password_login,
    refresh_session,
    revoke_session,
)
from app.schemas import (
    AuthConfigOut,
    DemoLoginRequest,
    PasswordLoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserOut,
)
from app.services.users import WorkspaceUserError, resolve_workspace_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user: UserContext) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_demo=user.is_demo,
    )


async def _supabase_token_response(
    session: SessionDep,
    payload: dict[str, Any],
) -> TokenResponse:
    access_token = str(payload.get("access_token") or "")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Authentication service returned an invalid session",
        )
    try:
        token_user = decode_supabase_token(access_token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase returned a token this API could not verify",
        ) from exc
    try:
        user = await resolve_workspace_user(session, token_user)
    except WorkspaceUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return TokenResponse(
        access_token=access_token,
        refresh_token=payload.get("refresh_token"),
        expires_in=payload.get("expires_in"),
        expires_at=payload.get("expires_at"),
        user=_user_out(user),
    )


def _supabase_http_error(exc: SupabaseAuthError) -> HTTPException:
    headers: dict[str, str] = {}
    if exc.status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"
    if exc.status_code == 429 and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.message,
        headers=headers or None,
    )


@router.get("/config", response_model=AuthConfigOut)
async def auth_config() -> AuthConfigOut:
    settings = get_settings()
    demo_users = (
        [_user_out(user) for user in DEMO_USERS.values()] if settings.demo_enabled else []
    )
    return AuthConfigOut(
        auth_mode=settings.auth_mode,
        demo_mode=settings.demo_enabled,
        password_auth=settings.supabase_auth_enabled,
        demo_users=demo_users,
    )


@router.get("/demo-users", response_model=list[UserOut])
async def list_demo_users() -> list[UserOut]:
    settings = get_settings()
    if not settings.demo_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo accounts are not enabled",
        )
    return [_user_out(user) for user in DEMO_USERS.values()]


@router.post(
    "/demo-login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit("auth-demo-login", "auth"))],
)
async def demo_login(payload: DemoLoginRequest) -> TokenResponse:
    settings = get_settings()
    if not settings.demo_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is disabled",
        )
    try:
        user = demo_user_for_role(payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    token = create_dev_token(user)
    return TokenResponse(access_token=token, user=_user_out(user))


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit("auth-login", "auth"))],
)
async def login(payload: PasswordLoginRequest, session: SessionDep) -> TokenResponse:
    settings = get_settings()
    if not settings.supabase_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Password login is not enabled on this deployment",
        )
    email = payload.email.strip()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid email address",
        )
    try:
        result = await password_login(email, payload.password)
    except SupabaseAuthError as exc:
        raise _supabase_http_error(exc) from exc
    return await _supabase_token_response(session, result)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit("auth-refresh", "auth"))],
)
async def refresh(payload: RefreshTokenRequest, session: SessionDep) -> TokenResponse:
    settings = get_settings()
    if not settings.supabase_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session refresh is not enabled on this deployment",
        )
    try:
        result = await refresh_session(payload.refresh_token)
    except SupabaseAuthError as exc:
        raise _supabase_http_error(exc) from exc
    return await _supabase_token_response(session, result)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> None:
    settings = get_settings()
    if settings.supabase_auth_enabled and credentials:
        await revoke_session(credentials.credentials)


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return _user_out(user)


@router.get("/roles", response_model=list[str])
async def roles() -> list[str]:
    return [role.value for role in Role]
