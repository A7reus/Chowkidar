from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep
from app.db.models import Supplier
from app.schemas import SupplierOut
from app.services.serializers import supplier_out

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
async def suppliers(session: SessionDep, _user: CurrentUser) -> list[SupplierOut]:
    rows = list(
        (await session.execute(select(Supplier).order_by(Supplier.tier, Supplier.name)))
        .scalars()
        .all()
    )
    return [supplier_out(row) for row in rows]
