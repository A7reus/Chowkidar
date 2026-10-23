from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.core.auth import DEMO_USERS, Role, create_dev_token, demo_user_for_role
from app.core.config import get_settings
from app.schemas import DemoLoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_demo=user.is_demo,
    )


@router.get("/demo-users", response_model=list[UserOut])
async def list_demo_users() -> list[UserOut]:
    settings = get_settings()
    if not settings.demo_mode or settings.auth_mode != "dev":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo accounts are not enabled",
        )
    return [_user_out(user) for user in DEMO_USERS.values()]


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(payload: DemoLoginRequest) -> TokenResponse:
    settings = get_settings()
    if not settings.demo_mode or settings.auth_mode != "dev":
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


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return _user_out(user)


@router.get("/roles", response_model=list[str])
async def roles() -> list[str]:
    return [role.value for role in Role]
