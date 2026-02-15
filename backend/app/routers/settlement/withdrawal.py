from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.lawfirm import Lawyer, LawyerConsultation
from ...models.settlement import WithdrawalRequest
from ...models.user import User
from ...schemas.settlement import WithdrawalCreateRequest, WithdrawalItem, WithdrawalListResponse
from ...services.settlement_service import settlement_service
from ...utils.deps import require_lawyer_verified

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["律师提现"])


def _mask_account_no(account_no: str) -> str:
    s = str(account_no or "").strip()
    if len(s) <= 4:
        return "****"
    return f"****{s[-4:]}"


def _mask_account_info(raw: str) -> str:
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            masked = obj.get("masked")
            if isinstance(masked, dict) and isinstance(
                    masked.get("account_no"), str):
                obj["account_no"] = str(masked.get("account_no") or "")
            elif isinstance(obj.get("account_no"), str):
                raw_no = settlement_service.decrypt_secret(
                    str(obj.get("account_no") or ""))
                obj["account_no"] = _mask_account_no(raw_no)
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        logger.exception("Failed to mask account info")
        return "***"


@router.get(
    "/lawyer/withdrawals",
    response_model=WithdrawalListResponse,
    summary="律师-提现记录",
)
async def lawyer_list_withdrawals(
    current_user: Annotated[User, Depends(require_lawyer_verified)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    lawyer = await settlement_service.get_current_lawyer(db, int(current_user.id))
    if lawyer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定律师资料")

    q = select(WithdrawalRequest).where(
        WithdrawalRequest.lawyer_id == int(lawyer.id))
    cq = select(func.count(WithdrawalRequest.id)).where(
        WithdrawalRequest.lawyer_id == int(lawyer.id))

    if status_filter:
        q = q.where(WithdrawalRequest.status == str(status_filter).strip())
        cq = cq.where(WithdrawalRequest.status == str(status_filter).strip())

    total = int((await db.execute(cq)).scalar() or 0)
    res = await db.execute(
        q.order_by(
            WithdrawalRequest.created_at.desc()).offset(
            (page - 1) * page_size).limit(page_size)
    )

    rows = res.scalars().all()

    lawyer_ids = sorted({int(x.lawyer_id)
                        for x in rows if x.lawyer_id is not None})
    lawyer_name_by_id: dict[int, str] = {}
    lawyer_rating_by_id: dict[int, float] = {}
    lawyer_completed_by_id: dict[int, int] = {}
    if lawyer_ids:
        lr = await db.execute(select(Lawyer).where(Lawyer.id.in_(lawyer_ids)))
        for l in lr.scalars().all():
            lid = int(l.id)
            lawyer_name_by_id[lid] = str(getattr(l, "name", "") or "")
            lawyer_rating_by_id[lid] = float(getattr(l, "rating", 0.0) or 0.0)

        cnt_res = await db.execute(
            select(
                LawyerConsultation.lawyer_id,
                func.count(
                    LawyerConsultation.id))
            .where(
                LawyerConsultation.lawyer_id.in_(lawyer_ids),
                LawyerConsultation.status == "completed",
            )
            .group_by(LawyerConsultation.lawyer_id)
        )
        for lid, cnt in cnt_res.all():
            if lid is None:
                continue
            lawyer_completed_by_id[int(lid)] = int(cnt or 0)

    items: list[WithdrawalItem] = []
    for w in rows:
        lid = int(w.lawyer_id)
        rating = float(lawyer_rating_by_id.get(lid, 0.0))
        completed = int(lawyer_completed_by_id.get(lid, 0))
        platform_fee_rate = settlement_service.choose_platform_fee_rate(
            lid, rating, completed)

        items.append(
            WithdrawalItem(
                id=int(w.id),
                request_no=str(w.request_no),
                lawyer_id=int(w.lawyer_id),
                lawyer_name=str(lawyer_name_by_id.get(lid) or "") or None,
                lawyer_rating=rating,
                lawyer_completed_count=completed,
                platform_fee_rate=float(platform_fee_rate),
                amount=float(w.amount),
                fee=float(w.fee),
                actual_amount=float(w.actual_amount),
                withdraw_method=str(w.withdraw_method),
                account_info_masked=_mask_account_info(str(w.account_info)),
                status=str(w.status),
                reject_reason=str(
                    w.reject_reason) if w.reject_reason is not None else None,
                admin_id=int(w.admin_id) if w.admin_id is not None else None,
                reviewed_at=w.reviewed_at,
                completed_at=w.completed_at,
                remark=str(w.remark) if w.remark is not None else None,
                created_at=w.created_at,
                updated_at=w.updated_at,
            )
        )

    return WithdrawalListResponse(
        items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/lawyer/withdrawals/{withdrawal_id}",
    response_model=WithdrawalItem,
    summary="律师-提现详情",
)
async def lawyer_get_withdrawal(
    withdrawal_id: int,
    current_user: Annotated[User, Depends(require_lawyer_verified)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lawyer = await settlement_service.get_current_lawyer(db, int(current_user.id))
    if lawyer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定律师资料")

    res = await db.execute(
        select(WithdrawalRequest).where(
            WithdrawalRequest.id == int(withdrawal_id),
            WithdrawalRequest.lawyer_id == int(lawyer.id),
        )
    )
    w = res.scalar_one_or_none()
    if w is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提现申请不存在")

    return WithdrawalItem(
        id=int(w.id),
        request_no=str(w.request_no),
        lawyer_id=int(w.lawyer_id),
        amount=float(w.amount),
        fee=float(w.fee),
        actual_amount=float(w.actual_amount),
        withdraw_method=str(w.withdraw_method),
        account_info_masked=_mask_account_info(str(w.account_info)),
        status=str(w.status),
        reject_reason=str(
            w.reject_reason) if w.reject_reason is not None else None,
        admin_id=int(w.admin_id) if w.admin_id is not None else None,
        reviewed_at=w.reviewed_at,
        completed_at=w.completed_at,
        remark=str(w.remark) if w.remark is not None else None,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


@router.post(
    "/lawyer/withdrawals",
    response_model=WithdrawalItem,
    summary="律师-提交提现申请",
)
async def lawyer_create_withdrawal(
    data: WithdrawalCreateRequest,
    current_user: Annotated[User, Depends(require_lawyer_verified)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lawyer = await settlement_service.get_current_lawyer(db, int(current_user.id))
    if lawyer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定律师资料")

    wr = await settlement_service.create_withdrawal_request(
        db,
        lawyer_id=int(lawyer.id),
        amount=float(data.amount),
        withdraw_method=str(data.withdraw_method),
        bank_account_id=int(data.bank_account_id),
    )

    return WithdrawalItem(
        id=int(wr.id),
        request_no=str(wr.request_no),
        lawyer_id=int(wr.lawyer_id),
        amount=float(wr.amount),
        fee=float(wr.fee),
        actual_amount=float(wr.actual_amount),
        withdraw_method=str(wr.withdraw_method),
        account_info_masked=_mask_account_info(str(wr.account_info)),
        status=str(wr.status),
        reject_reason=str(
            wr.reject_reason) if wr.reject_reason is not None else None,
        admin_id=int(wr.admin_id) if wr.admin_id is not None else None,
        reviewed_at=wr.reviewed_at,
        completed_at=wr.completed_at,
        remark=str(wr.remark) if wr.remark is not None else None,
        created_at=wr.created_at,
        updated_at=wr.updated_at,
    )
