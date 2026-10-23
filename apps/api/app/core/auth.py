from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from pydantic import BaseModel

from app.core.config import get_settings


class Role(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    APPROVER = "approver"
    VIEWER = "viewer"


class UserContext(BaseModel):
    id: str
    email: str
    name: str
    role: Role
    is_demo: bool = False


DEMO_USERS: dict[Role, UserContext] = {
    Role.ADMIN: UserContext(
        id="00000000-0000-0000-0000-000000000001",
        email="admin@chowkidar.demo",
        name="Ayesha Rahman",
        role=Role.ADMIN,
        is_demo=True,
    ),
    Role.ANALYST: UserContext(
        id="00000000-0000-0000-0000-000000000002",
        email="analyst@chowkidar.demo",
        name="Rafiq Hasan",
        role=Role.ANALYST,
        is_demo=True,
    ),
    Role.APPROVER: UserContext(
        id="00000000-0000-0000-0000-000000000003",
        email="approver@chowkidar.demo",
        name="Nusrat Jahan",
        role=Role.APPROVER,
        is_demo=True,
    ),
    Role.VIEWER: UserContext(
        id="00000000-0000-0000-0000-000000000004",
        email="viewer@chowkidar.demo",
        name="Imran Chowdhury",
        role=Role.VIEWER,
        is_demo=True,
    ),
}


def create_dev_token(user: UserContext) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "is_demo": True,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=12)).timestamp()),
        "iss": "chowkidar-dev",
    }
    return jwt.encode(payload, settings.dev_jwt_secret, algorithm="HS256")


def decode_dev_token(token: str) -> UserContext:
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.dev_jwt_secret,
        algorithms=["HS256"],
        issuer="chowkidar-dev",
        options={"require": ["exp", "sub"]},
    )
    return UserContext(
        id=str(payload["sub"]),
        email=str(payload.get("email", "")),
        name=str(payload.get("name", "")),
        role=Role(str(payload.get("role", "viewer"))),
        is_demo=bool(payload.get("is_demo", True)),
    )


def decode_supabase_token(token: str) -> UserContext:
    settings = get_settings()
    if not settings.supabase_url:
        raise ValueError("SUPABASE_URL is required when AUTH_MODE=supabase")
    jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    signing_key = jwt.PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256", "ES256"],
        audience=settings.supabase_jwt_audience,
        options={"require": ["exp", "sub"]},
    )
    app_metadata = payload.get("app_metadata") or {}
    user_metadata = payload.get("user_metadata") or {}
    role_value = app_metadata.get("role") or user_metadata.get("role") or "viewer"
    try:
        role = Role(str(role_value))
    except ValueError:
        role = Role.VIEWER
    email = str(payload.get("email") or "")
    return UserContext(
        id=str(payload["sub"]),
        email=email,
        name=str(user_metadata.get("full_name") or email.split("@")[0] or "User"),
        role=role,
        is_demo=False,
    )


def parse_bearer_token(header: str | None) -> str | None:
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def demo_user_for_role(role: str) -> UserContext:
    try:
        return DEMO_USERS[Role(role)]
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Unknown demo role: {role}") from exc


def user_id_uuid(user: UserContext) -> uuid.UUID:
    try:
        return uuid.UUID(user.id)
    except ValueError:
        return uuid.uuid5(uuid.NAMESPACE_URL, user.email or user.id)
