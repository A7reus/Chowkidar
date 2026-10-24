"""Provision the four Chowkidar workspace accounts in Supabase Auth.

This is a one-time production cutover helper. It:
  1. creates (or updates) four confirmed Supabase Auth users;
  2. maps their Supabase UUIDs onto the local ``users`` rows that authorize
     role-based access; and
  3. writes generated passwords to a gitignored local file.

Run it with the Supabase service-role key and the production DATABASE_URL:

    cd apps/api
    SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... DATABASE_URL=... \
      uv run python -m scripts.provision_supabase_users

Never commit the generated credentials file or paste the service-role key into
the repository. The script prints only a redacted summary.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx
from app.core.auth import Role
from app.core.config import ROOT_DIR, get_settings
from app.db.models import User
from app.db.session import AsyncSessionLocal, engine
from sqlalchemy import select


@dataclass(frozen=True)
class ProvisionedUser:
    role: Role
    email: str
    name: str
    password: str


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _password(role: Role) -> str:
    key = f"CHOWKIDAR_{role.value.upper()}_PASSWORD"
    return os.getenv(key, "").strip() or secrets.token_urlsafe(24)


def _users() -> list[ProvisionedUser]:
    return [
        ProvisionedUser(
            role=Role.ADMIN,
            email=_env("CHOWKIDAR_ADMIN_EMAIL", "admin@chowkidar.app").lower(),
            name=_env("CHOWKIDAR_ADMIN_NAME", "Ayesha Rahman"),
            password=_password(Role.ADMIN),
        ),
        ProvisionedUser(
            role=Role.ANALYST,
            email=_env("CHOWKIDAR_ANALYST_EMAIL", "analyst@chowkidar.app").lower(),
            name=_env("CHOWKIDAR_ANALYST_NAME", "Rafiq Hasan"),
            password=_password(Role.ANALYST),
        ),
        ProvisionedUser(
            role=Role.APPROVER,
            email=_env("CHOWKIDAR_APPROVER_EMAIL", "approver@chowkidar.app").lower(),
            name=_env("CHOWKIDAR_APPROVER_NAME", "Nusrat Jahan"),
            password=_password(Role.APPROVER),
        ),
        ProvisionedUser(
            role=Role.VIEWER,
            email=_env("CHOWKIDAR_VIEWER_EMAIL", "viewer@chowkidar.app").lower(),
            name=_env("CHOWKIDAR_VIEWER_NAME", "Imran Chowdhury"),
            password=_password(Role.VIEWER),
        ),
    ]


def _admin_headers(service_key: str) -> dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }


async def _find_user(
    client: httpx.AsyncClient, base_url: str, service_key: str, email: str
) -> dict | None:
    page = 1
    while True:
        response = await client.get(
            f"{base_url}/auth/v1/admin/users",
            headers=_admin_headers(service_key),
            params={"page": page, "per_page": 1000},
        )
        response.raise_for_status()
        body = response.json()
        users = body.get("users", []) if isinstance(body, dict) else []
        for user in users:
            if str(user.get("email", "")).lower() == email:
                return user
        if len(users) < 1000:
            return None
        page += 1


async def _upsert_supabase_user(
    client: httpx.AsyncClient,
    base_url: str,
    service_key: str,
    account: ProvisionedUser,
) -> str:
    existing = await _find_user(client, base_url, service_key, account.email)
    payload = {
        "email": account.email,
        "password": account.password,
        "email_confirm": True,
        "app_metadata": {"role": account.role.value},
        "user_metadata": {"full_name": account.name},
    }
    if existing:
        user_id = str(existing["id"])
        response = await client.put(
            f"{base_url}/auth/v1/admin/users/{user_id}",
            headers=_admin_headers(service_key),
            json=payload,
        )
        response.raise_for_status()
        return user_id

    response = await client.post(
        f"{base_url}/auth/v1/admin/users",
        headers=_admin_headers(service_key),
        json=payload,
    )
    if response.status_code in {400, 422}:
        # The user may have been created between the list and create calls.
        existing = await _find_user(client, base_url, service_key, account.email)
        if existing:
            return str(existing["id"])
    response.raise_for_status()
    return str(response.json()["id"])


async def _map_local_user(account: ProvisionedUser, supabase_user_id: str) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == account.email))
        db_user = result.scalars().first()
        if db_user is None:
            # Reuse the seeded workspace row for the role so existing audit and
            # approval references remain valid during a pilot cutover.
            result = await session.execute(
                select(User).where(User.role == account.role.value).order_by(User.created_at)
            )
            db_user = result.scalars().first()
        if db_user is None:
            db_user = User(
                email=account.email,
                name=account.name,
                role=account.role.value,
                is_active=True,
            )
            session.add(db_user)
        db_user.email = account.email
        db_user.name = account.name
        db_user.role = account.role.value
        db_user.supabase_user_id = supabase_user_id
        db_user.is_active = True
        await session.commit()
        return str(db_user.id)


def _write_credentials(accounts: list[ProvisionedUser]) -> Path:
    path = ROOT_DIR / "docs" / "private" / "supabase-credentials.local.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Chowkidar Supabase Auth credentials",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "These are pilot accounts. Treat this file as a secret. Do not commit it.",
        "",
        "| Role | Email | Password |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| {account.role.value} | {account.email} | `{account.password}` |"
        for account in accounts
    )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    with contextlib.suppress(OSError):
        path.chmod(0o600)
    return path


async def main() -> None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    base_url = settings.supabase_url.rstrip("/")
    accounts = _users()
    async with httpx.AsyncClient(timeout=30) as client:
        for account in accounts:
            supabase_user_id = await _upsert_supabase_user(
                client, base_url, settings.supabase_service_role_key, account
            )
            local_user_id = await _map_local_user(account, supabase_user_id)
            print(
                f"{account.role.value:8s} {account.email:30s} "
                f"supabase={supabase_user_id} local={local_user_id}"
            )
    credentials_path = _write_credentials(accounts)
    print(f"\nCredentials written to {credentials_path.relative_to(ROOT_DIR)}")
    print("Set AUTH_MODE=supabase and DEMO_MODE=false on the API after this completes.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
