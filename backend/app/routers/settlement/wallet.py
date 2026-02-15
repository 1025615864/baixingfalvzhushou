from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.settlement import LawyerWalletResponse
from ...services.settlement_service import settlement_service
from ...utils.deps import require_lawyer_verified

router = APIRouter(prefix="", tags=["律师钱包"])


@router.get("/lawyer/wallet", response_model=LawyerWalletResponse,
            summary="律师-获取钱包")
async def lawyer_get_wallet(
    current_user: Annotated[User, Depends(require_lawyer_verified)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lawyer = await settlement_service.get_current_lawyer(db, int(current_user.id))
    if lawyer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定律师资料")

    wallet = await settlement_service.get_or_create_wallet(db, int(lawyer.id))
    return LawyerWalletResponse.model_validate(wallet)
