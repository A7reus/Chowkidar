from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import Role, UserContext
from app.db.models import User


class WorkspaceUserError(RuntimeError):
    """The authenticated identity is not a provisioned workspace member."""


async def resolve_workspace_user(
    session: AsyncSession,
    token_user: UserContext,
) -> UserContext:
    """Map a verified Supabase identity to the local workspace user.

    The local ``users`` table is authoritative for role and display name.
    Supabase app_metadata is deliberately not trusted for authorization.
    """
    result = await session.execute(
        select(User).where(
            or_(
                User.supabase_user_id == token_user.id,
                func.lower(User.email) == token_user.email.strip().lower(),
            )
        )
    )
    db_user = result.scalars().first()
    if db_user is None:
        raise WorkspaceUserError(
            "This account is not provisioned for the Chowkidar workspace"
        )
    if not db_user.is_active:
        raise WorkspaceUserError("This account is disabled")
    try:
        role = Role(db_user.role)
    except ValueError as exc:
        raise WorkspaceUserError("This account has an unsupported role") from exc
    return UserContext(
        id=str(db_user.id),
        email=db_user.email,
        name=db_user.name,
        role=role,
        is_demo=False,
    )
