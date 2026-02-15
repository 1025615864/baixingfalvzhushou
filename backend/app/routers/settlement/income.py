from __future__ import annotations

import csv
import io
from collections.abc import AsyncIterator, Mapping
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.lawfirm import LawyerConsultation
from ...models.settlement import LawyerIncomeRecord
from ...models.user import User
from ...schemas.settlement import LawyerIncomeRecordItem, LawyerIncomeRecordListResponse
from ...services.settlement_service import settlement_service
from ...utils.deps import require_lawyer_verified

router = APIRouter(prefix="", tags=["律师收入"])


def _mask_account_no(account_no: str) -> str:
    s = str(account_no or "").strip()
    if len(s) <= 4:
        return "****"
    return f"****{s[-4:]}"


async def _generate_csv_stream(
        fieldnames: list[str], rows_iter: AsyncIterator[Mapping[str, object]]):
    header_out = io.StringIO()
    _ = header_out.write("\ufeff")
    header_writer = csv.DictWriter(
        header_out,
        fieldnames=fieldnames,
        extrasaction="ignore",
        lineterminator="\n")
    header_writer.writeheader()
    yield header_out.getvalue()

    async for row in rows_iter:
        processed: dict[str, object] = {}
        for k, v in row.items():
            if isinstance(v, datetime):
                processed[k] = v.strftime("%Y-%m-%d %H:%M:%S")
            else:
                processed[k] = v

        out = io.StringIO()
        writer = csv.DictWriter(
            out,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n")
        writer.writerow(processed)
        yield out.getvalue()


@router.get(
    "/lawyer/income-records",
    response_model=LawyerIncomeRecordListResponse,
    summary="律师-获取收入记录",
)
async def lawyer_list_income_records(
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

    q = select(LawyerIncomeRecord).where(
        LawyerIncomeRecord.lawyer_id == int(lawyer.id))
    cq = select(func.count(LawyerIncomeRecord.id)).where(
        LawyerIncomeRecord.lawyer_id == int(lawyer.id))

    if status_filter:
        q = q.where(LawyerIncomeRecord.status == str(status_filter).strip())
        cq = cq.where(LawyerIncomeRecord.status == str(status_filter).strip())

    total = int((await db.execute(cq)).scalar() or 0)
    res = await db.execute(
        q.order_by(
            LawyerIncomeRecord.created_at.desc()).offset(
            (page - 1) * page_size).limit(page_size)
    )

    records = res.scalars().all()
    consultation_ids = [int(x.consultation_id)
                        for x in records if x.consultation_id is not None]
    subject_by_id: dict[int, str] = {}
    if consultation_ids:
        sub_res = await db.execute(
            select(LawyerConsultation.id, LawyerConsultation.subject).where(
                LawyerConsultation.id.in_(consultation_ids)
            )
        )
        for cid, subj in sub_res.all():
            if isinstance(cid, int) and isinstance(subj, str):
                subject_by_id[int(cid)] = subj

    items: list[LawyerIncomeRecordItem] = []
    for r in records:
        item = LawyerIncomeRecordItem.model_validate(r)
        subj = subject_by_id.get(
            int(r.consultation_id)) if r.consultation_id is not None else None
        items.append(item.model_copy(update={"consultation_subject": subj}))

    return LawyerIncomeRecordListResponse(
        items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/lawyer/income-records/export",
    summary="律师-导出收入记录",
)
async def lawyer_export_income_records(
    current_user: Annotated[User, Depends(require_lawyer_verified)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
):
    lawyer = await settlement_service.get_current_lawyer(db, int(current_user.id))
    if lawyer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定律师资料")

    fieldnames = [
        "id",
        "consultation_id",
        "consultation_subject",
        "order_no",
        "user_paid_amount",
        "platform_fee",
        "lawyer_income",
        "withdrawn_amount",
        "status",
        "settle_time",
        "created_at",
    ]

    filename = f"income_records_{int(lawyer.id)}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    exists_stmt = select(LawyerIncomeRecord.id).where(
        LawyerIncomeRecord.lawyer_id == int(lawyer.id))
    if status_filter:
        exists_stmt = exists_stmt.where(
            LawyerIncomeRecord.status == str(status_filter).strip())
    has_record = (await db.execute(exists_stmt.limit(1))).scalar_one_or_none()
    # 无收入记录时返回空内容，避免仅输出表头
    if has_record is None:
        return StreamingResponse(
            iter(()),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    async def row_generator():
        batch_size = 1000
        offset = 0
        while True:
            stmt = (
                select(
                    LawyerIncomeRecord,
                    LawyerConsultation.subject) .outerjoin(
                    LawyerConsultation,
                    LawyerConsultation.id == LawyerIncomeRecord.consultation_id) .where(
                    LawyerIncomeRecord.lawyer_id == int(
                        lawyer.id)))
            if status_filter:
                stmt = stmt.where(LawyerIncomeRecord.status ==
                                  str(status_filter).strip())

            stmt = (
                stmt.order_by(
                    LawyerIncomeRecord.created_at.desc(),
                    LawyerIncomeRecord.id.desc())
                .offset(offset)
                .limit(batch_size)
            )

            res = await db.execute(stmt)
            rows = res.all()
            if not rows:
                break

            for record, subject in rows:
                yield {
                    "id": int(record.id),
                    "consultation_id": int(record.consultation_id)
                    if record.consultation_id is not None
                    else "",
                    "consultation_subject": str(subject) if isinstance(subject, str) else "",
                    "order_no": str(record.order_no or ""),
                    "user_paid_amount": float(record.user_paid_amount or 0.0),
                    "platform_fee": float(record.platform_fee or 0.0),
                    "lawyer_income": float(record.lawyer_income or 0.0),
                    "withdrawn_amount": float(record.withdrawn_amount or 0.0),
                    "status": str(record.status or ""),
                    "settle_time": record.settle_time,
                    "created_at": record.created_at,
                }

            offset += batch_size

    return StreamingResponse(
        _generate_csv_stream(fieldnames, row_generator()),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
