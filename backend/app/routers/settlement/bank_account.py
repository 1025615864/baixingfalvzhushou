from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.settlement import LawyerBankAccount
from ...models.user import User
from ...schemas.settlement import (
    LawyerBankAccountCreate,
    LawyerBankAccountItem,
    LawyerBankAccountListResponse,
    LawyerBankAccountUpdate,
)
from ...services.settlement_service import settlement_service
from ...utils.deps import require_lawyer_verified

router = APIRouter(prefix="", tags=["律师收款账户"])


def _mask_account_no(account_no: str) -> str:
    s = str(account_no or "").strip()
    if len(s) <= 4:
        return "****"
    return f"****{s[-4:]}"


@router.get(
    "/lawyer/bank-accounts",
    response_model=LawyerBankAccountListResponse,
    summary="律师-获取收款账户",
)
async def lawyer_list_bank_accounts(
    current_user: Annotated[User, Depends(require_lawyer_verified)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lawyer = await settlement_service.get_current_lawyer(db, int(current_user.id))
    if lawyer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定律师资料")

    res = await db.execute(
        select(LawyerBankAccount)
        .where(LawyerBankAccount.lawyer_id == int(lawyer.id))
        .order_by(LawyerBankAccount.is_default.desc(), LawyerBankAccount.created_at.desc())
    )
    rows = res.scalars().all()

    items: list[LawyerBankAccountItem] = []
    for r in rows:
        raw_no = settlement_service.decrypt_secret(str(r.account_no))
        items.append(
            LawyerBankAccountItem(
                id=int(r.id),
                lawyer_id=int(r.lawyer_id),
                account_type=str(r.account_type),
                bank_name=str(
                    r.bank_name) if r.bank_name is not None else None,
                account_no_masked=_mask_account_no(str(raw_no)),
                account_holder=str(r.account_holder),
                is_default=bool(r.is_default),
                is_active=bool(r.is_active),
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )

    return LawyerBankAccountListResponse(items=items, total=len(items))


@router.post(
    "/lawyer/bank-accounts",
    response_model=LawyerBankAccountItem,
    summary="律师-添加收款账户",
)
async def lawyer_create_bank_account(
    data: LawyerBankAccountCreate,
    current_user: Annotated[User, Depends(require_lawyer_verified)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lawyer = await settlement_service.get_current_lawyer(db, int(current_user.id))
    if lawyer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定律师资料")

    row = LawyerBankAccount(
        lawyer_id=int(lawyer.id),
        account_type=str(data.account_type or "bank_card"),
        bank_name=(str(data.bank_name).strip() if data.bank_name else None),
        account_no=settlement_service.encrypt_secret(
            str(data.account_no).strip()),
        account_holder=str(data.account_holder).strip(),
        is_default=bool(data.is_default),
        is_active=True,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    if bool(data.is_default):
        _ = await db.execute(
            select(LawyerBankAccount)
            .where(
                LawyerBankAccount.lawyer_id == int(lawyer.id),
                LawyerBankAccount.id != int(row.id),
            )
        )
        await db.execute(
            sa_update(LawyerBankAccount)
            .where(
                LawyerBankAccount.lawyer_id == int(lawyer.id),
                LawyerBankAccount.id != int(row.id),
            )
            .values(is_default=False)
        )
        await db.commit()

    return LawyerBankAccountItem(
        id=int(row.id),
        lawyer_id=int(row.lawyer_id),
        account_type=str(row.account_type),
        bank_name=str(row.bank_name) if row.bank_name is not None else None,
        account_no_masked=_mask_account_no(str(data.account_no)),
        account_holder=str(row.account_holder),
        is_default=bool(row.is_default),
        is_active=bool(row.is_active),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.put(
    "/lawyer/bank-accounts/{account_id}",
    response_model=LawyerBankAccountItem,
    summary="律师-更新收款账户",
)
async def lawyer_update_bank_account(
    account_id: int,
    data: LawyerBankAccountUpdate,
    current_user: Annotated[User, Depends(require_lawyer_verified)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lawyer = await settlement_service.get_current_lawyer(db, int(current_user.id))
    if lawyer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定律师资料")

    res = await db.execute(
        select(LawyerBankAccount).where(
            LawyerBankAccount.id == int(account_id),
            LawyerBankAccount.lawyer_id == int(lawyer.id),
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在")

    if data.bank_name is not None:
        row.bank_name = str(data.bank_name).strip() or None
    if data.account_no is not None:
        row.account_no = settlement_service.encrypt_secret(
            str(data.account_no).strip())
    if data.account_holder is not None:
        row.account_holder = str(data.account_holder).strip()
    if data.is_active is not None:
        row.is_active = bool(data.is_active)
    if data.is_default is not None:
        row.is_default = bool(data.is_default)

    db.add(row)
    await db.commit()
    await db.refresh(row)

    if bool(row.is_default):
        await db.execute(
            sa_update(LawyerBankAccount)
            .where(
                LawyerBankAccount.lawyer_id == int(lawyer.id),
                LawyerBankAccount.id != int(row.id),
            )
            .values(is_default=False)
        )
        await db.commit()

    raw_no = settlement_service.decrypt_secret(str(row.account_no))
    return LawyerBankAccountItem(
        id=int(row.id),
        lawyer_id=int(row.lawyer_id),
        account_type=str(row.account_type),
        bank_name=str(row.bank_name) if row.bank_name is not None else None,
        account_no_masked=_mask_account_no(str(raw_no)),
        account_holder=str(row.account_holder),
        is_default=bool(row.is_default),
        is_active=bool(row.is_active),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.delete("/lawyer/bank-accounts/{account_id}", summary="律师-删除收款账户")
async def lawyer_delete_bank_account(
    account_id: int,
    current_user: Annotated[User, Depends(require_lawyer_verified)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lawyer = await settlement_service.get_current_lawyer(db, int(current_user.id))
    if lawyer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定律师资料")

    res = await db.execute(
        select(LawyerBankAccount).where(
            LawyerBankAccount.id == int(account_id),
            LawyerBankAccount.lawyer_id == int(lawyer.id),
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在")

    await db.delete(row)
    await db.commit()

    return {"message": "删除成功"}


@router.put(
    "/lawyer/bank-accounts/{account_id}/default",
    summary="律师-设为默认收款账户",
)
async def lawyer_set_default_bank_account(
    account_id: int,
    current_user: Annotated[User, Depends(require_lawyer_verified)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lawyer = await settlement_service.get_current_lawyer(db, int(current_user.id))
    if lawyer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定律师资料")

    res = await db.execute(
        select(LawyerBankAccount).where(
            LawyerBankAccount.id == int(account_id),
            LawyerBankAccount.lawyer_id == int(lawyer.id),
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在")

    await db.execute(
        sa_update(LawyerBankAccount)
        .where(LawyerBankAccount.lawyer_id == int(lawyer.id))
        .values(is_default=False)
    )
    await db.execute(
        sa_update(LawyerBankAccount)
        .where(LawyerBankAccount.id == int(row.id))
        .values(is_default=True)
    )
    await db.commit()

    return {"message": "已设为默认"}
