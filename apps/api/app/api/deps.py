from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    Role,
    UserContext,
    decode_dev_token,
    decode_supabase_token,
    demo_user_for_role,
)
from app.core.config import get_settings
from app.db.session import get_session
from app.services.users import WorkspaceUserError, resolve_workspace_user

bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    x_demo_role: Annotated[str | None, Header(alias="X-Demo-Role")] = None,
) -> UserContext:
    settings = get_settings()
    token = credentials.credentials if credentials else None
    if not token and x_demo_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if settings.auth_mode == "dev":
        if not settings.demo_enabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Demo access is disabled",
            )
        if token:
            try:
                return decode_dev_token(token)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired demo token",
                ) from exc
        try:
            return demo_user_for_role(x_demo_role or Role.VIEWER.value)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

    if settings.auth_mode == "supabase":
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Supabase bearer token required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            token_user = decode_supabase_token(token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        try:
            return await resolve_workspace_user(session, token_user)
        except WorkspaceUserError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported AUTH_MODE: {settings.auth_mode}",
    )


CurrentUser = Annotated[UserContext, Depends(get_current_user)]


def require_roles(*allowed: Role):
    async def dependency(user: CurrentUser) -> UserContext:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' is not allowed for this action",
            )
        return user

    return dependency


AdminUser = Annotated[UserContext, Depends(require_roles(Role.ADMIN))]
AnalystUser = Annotated[UserContext, Depends(require_roles(Role.ADMIN, Role.ANALYST))]
ApproverUser = Annotated[UserContext, Depends(require_roles(Role.ADMIN, Role.APPROVER))]


def require_internal_key(
    x_internal_key: Annotated[str | None, Header(alias="X-Internal-Key")] = None,
) -> bool:
    settings = get_settings()
    if not x_internal_key or x_internal_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal automation key",
        )
    return True


def optional_token_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserContext | None:
    token = credentials.credentials if credentials else None
    if not token:
        return None
    try:
        return decode_dev_token(token)
    except Exception:
        return None
