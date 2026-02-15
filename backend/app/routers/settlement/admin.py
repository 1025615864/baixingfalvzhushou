from __future__ import annotations

import csv
import io
import logging
from collections.abc import AsyncIterator, Mapping
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import Integer, cast as sa_cast, func, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.lawfirm import Lawyer, LawyerConsultation
from ...models.payment import PaymentOrder, PaymentStatus
from ...models.settlement import LawyerIncomeRecord, LawyerWallet, WithdrawalRequest
from ...models.user import User
from ...schemas.settlement import (
    AdminSettlementStatsResponse,
    AdminWithdrawalDetailResponse,
    SettlementStatsTopLawyerItem,
    SettlementStatsWalletSummary,
    SettlementStatsWithdrawalSummary,
    WithdrawalAdminActionRequest,
    WithdrawalItem,
    WithdrawalListResponse,
    WithdrawalRejectRequest,
)
from ...services.settlement_service import settlement_service

logger = logging.getLogger(__name__)
from ...utils.deps import require_admin

router = APIRouter(prefix="", tags=["管理员结算"])


# ==================== 结算统计仪表盘 ====================

class DashboardStatsResponse(BaseModel):
    """仪表盘统计数据"""
    # 今日数据
    today_income: float
    today_withdrawal: float
    today_order_count: int
    
    # 累计数据
    total_income: float
    total_withdrawal: float
    total_lawyer_count: int
    total_order_count: int
    
    # 待处理数据
    pending_withdrawal_count: int
    pending_withdrawal_amount: float
    pending_settlement_count: int
    pending_settlement_amount: float
    
    # 钱包统计
    total_wallet_balance: float
    total_frozen_amount: float


class TrendDataResponse(BaseModel):
    """趋势数据"""
    dates: list[str]
    income: list[float]
    withdrawal: list[float]
    orders: list[int]


class PaymentMethodStatsResponse(BaseModel):
    """支付方式统计"""
    methods: list[dict[str, object]]


class TopLawyersResponse(BaseModel):
    """律师收入排行"""
    lawyers: list[dict[str, object]]


@router.get("/admin/settlement/dashboard", response_model=DashboardStatsResponse, summary="管理员-结算统计仪表盘")
async def admin_settlement_dashboard(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取结算统计仪表盘数据"""
    _ = current_user
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 今日收入
    today_income_res = await db.execute(
        select(func.coalesce(func.sum(LawyerIncomeRecord.lawyer_income), 0))
        .where(LawyerIncomeRecord.created_at >= today)
    )
    today_income = float(today_income_res.scalar() or 0)
    
    # 今日提现
    today_withdrawal_res = await db.execute(
        select(func.coalesce(func.sum(WithdrawalRequest.amount), 0))
        .where(
            WithdrawalRequest.created_at >= today,
            WithdrawalRequest.status.in_(["completed", "approved"])
        )
    )
    today_withdrawal = float(today_withdrawal_res.scalar() or 0)
    
    # 今日订单数
    today_order_res = await db.execute(
        select(func.count(PaymentOrder.id))
        .where(
            PaymentOrder.created_at >= today,
            PaymentOrder.status == PaymentStatus.PAID
        )
    )
    today_order_count = int(today_order_res.scalar() or 0)
    
    # 累计收入
    total_income_res = await db.execute(
        select(func.coalesce(func.sum(LawyerIncomeRecord.lawyer_income), 0))
    )
    total_income = float(total_income_res.scalar() or 0)
    
    # 累计提现
    total_withdrawal_res = await db.execute(
        select(func.coalesce(func.sum(WithdrawalRequest.amount), 0))
        .where(WithdrawalRequest.status.in_(["completed", "approved"]))
    )
    total_withdrawal = float(total_withdrawal_res.scalar() or 0)
    
    # 律师总数
    total_lawyer_res = await db.execute(select(func.count(Lawyer.id)))
    total_lawyer_count = int(total_lawyer_res.scalar() or 0)
    
    # 累计订单数
    total_order_res = await db.execute(
        select(func.count(PaymentOrder.id))
        .where(PaymentOrder.status == PaymentStatus.PAID)
    )
    total_order_count = int(total_order_res.scalar() or 0)
    
    # 待处理提现
    pending_withdrawal_res = await db.execute(
        select(
            func.count(WithdrawalRequest.id),
            func.coalesce(func.sum(WithdrawalRequest.amount), 0)
        )
        .where(WithdrawalRequest.status == "pending")
    )
    pending_withdrawal_count, pending_withdrawal_amount = pending_withdrawal_res.first() or (0, 0)
    
    # 待结算收入
    pending_settlement_res = await db.execute(
        select(
            func.count(LawyerIncomeRecord.id),
            func.coalesce(func.sum(LawyerIncomeRecord.lawyer_income), 0)
        )
        .where(LawyerIncomeRecord.status == "pending")
    )
    pending_settlement_count, pending_settlement_amount = pending_settlement_res.first() or (0, 0)
    
    # 钱包统计
    wallet_stats_res = await db.execute(
        select(
            func.coalesce(func.sum(LawyerWallet.available_amount), 0),
            func.coalesce(func.sum(LawyerWallet.frozen_amount), 0)
        )
    )
    total_wallet_balance, total_frozen_amount = wallet_stats_res.first() or (0, 0)
    
    return DashboardStatsResponse(
        today_income=today_income,
        today_withdrawal=today_withdrawal,
        today_order_count=today_order_count,
        total_income=total_income,
        total_withdrawal=total_withdrawal,
        total_lawyer_count=total_lawyer_count,
        total_order_count=total_order_count,
        pending_withdrawal_count=int(pending_withdrawal_count),
        pending_withdrawal_amount=float(pending_withdrawal_amount),
        pending_settlement_count=int(pending_settlement_count),
        pending_settlement_amount=float(pending_settlement_amount),
        total_wallet_balance=float(total_wallet_balance),
        total_frozen_amount=float(total_frozen_amount),
    )


@router.get("/admin/settlement/trends", response_model=TrendDataResponse, summary="管理员-收入趋势")
async def admin_settlement_trends(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: Annotated[int, Query(ge=7, le=90)] = 30,
):
    """获取收入趋势数据"""
    _ = current_user
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # 生成日期列表
    dates = []
    for i in range(days):
        date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
        dates.insert(0, date)
    
    # 查询每日收入
    income_by_date = {}
    income_res = await db.execute(
        select(
            func.date(LawyerIncomeRecord.created_at),
            func.coalesce(func.sum(LawyerIncomeRecord.lawyer_income), 0)
        )
        .where(LawyerIncomeRecord.created_at >= start_date)
        .group_by(func.date(LawyerIncomeRecord.created_at))
    )
    for date, amount in income_res.all():
        income_by_date[str(date)] = float(amount)
    
    # 查询每日提现
    withdrawal_by_date = {}
    withdrawal_res = await db.execute(
        select(
            func.date(WithdrawalRequest.created_at),
            func.coalesce(func.sum(WithdrawalRequest.amount), 0)
        )
        .where(
            WithdrawalRequest.created_at >= start_date,
            WithdrawalRequest.status.in_(["completed", "approved"])
        )
        .group_by(func.date(WithdrawalRequest.created_at))
    )
    for date, amount in withdrawal_res.all():
        withdrawal_by_date[str(date)] = float(amount)
    
    # 查询每日订单数
    orders_by_date = {}
    orders_res = await db.execute(
        select(
            func.date(PaymentOrder.created_at),
            func.count(PaymentOrder.id)
        )
        .where(
            PaymentOrder.created_at >= start_date,
            PaymentOrder.status == PaymentStatus.PAID
        )
        .group_by(func.date(PaymentOrder.created_at))
    )
    for date, count in orders_res.all():
        orders_by_date[str(date)] = int(count)
    
    # 填充数据
    income = [income_by_date.get(d, 0) for d in dates]
    withdrawal = [withdrawal_by_date.get(d, 0) for d in dates]
    orders = [orders_by_date.get(d, 0) for d in dates]
    
    return TrendDataResponse(
        dates=dates,
        income=income,
        withdrawal=withdrawal,
        orders=orders
    )


@router.get("/admin/settlement/payment-methods", response_model=PaymentMethodStatsResponse, summary="管理员-支付方式统计")
async def admin_payment_method_stats(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: Annotated[int, Query(ge=7, le=90)] = 30,
):
    """获取支付方式统计"""
    _ = current_user
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    res = await db.execute(
        select(
            PaymentOrder.payment_method,
            func.count(PaymentOrder.id),
            func.coalesce(func.sum(PaymentOrder.actual_amount), 0)
        )
        .where(
            PaymentOrder.created_at >= start_date,
            PaymentOrder.status == PaymentStatus.PAID
        )
        .group_by(PaymentOrder.payment_method)
    )
    
    methods = []
    for method, count, amount in res.all():
        methods.append({
            "method": method or "unknown",
            "count": int(count),
            "amount": float(amount)
        })
    
    return PaymentMethodStatsResponse(methods=methods)


@router.get("/admin/settlement/top-lawyers", response_model=TopLawyersResponse, summary="管理员-律师收入排行")
async def admin_top_lawyers(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=5, le=50)] = 10,
    days: Annotated[int, Query(ge=7, le=365)] = 30,
):
    """获取律师收入排行"""
    _ = current_user
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # 查询律师收入排行
    res = await db.execute(
        select(
            LawyerIncomeRecord.lawyer_id,
            func.coalesce(func.sum(LawyerIncomeRecord.lawyer_income), 0),
            func.count(LawyerIncomeRecord.id)
        )
        .where(LawyerIncomeRecord.created_at >= start_date)
        .group_by(LawyerIncomeRecord.lawyer_id)
        .order_by(func.sum(LawyerIncomeRecord.lawyer_income).desc())
        .limit(limit)
    )
    
    lawyer_stats = []
    for lawyer_id, income, count in res.all():
        # 获取律师信息
        lawyer_res = await db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = lawyer_res.scalar_one_or_none()
        
        lawyer_stats.append({
            "lawyer_id": int(lawyer_id),
            "name": str(getattr(lawyer, "name", "")) if lawyer else "",
            "income": float(income),
            "order_count": int(count)
        })
    
    return TopLawyersResponse(lawyers=lawyer_stats)


def _mask_account_no(account_no: str) -> str:
    s = str(account_no or "").strip()
    if len(s) <= 4:
        return "****"
    return f"****{s[-4:]}"


def _mask_account_info(raw: str) -> str:
    try:
        import json
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
        logger.exception("Failed to mask account info in admin")
        return "***"


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
    "/admin/withdrawals/export",
    summary="管理员-导出提现记录",
)
async def admin_export_withdrawals(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    keyword: Annotated[str | None, Query()] = None,
):
    """导出提现记录（流式分页读取，避免大数据量内存溢出）"""
    user_id = current_user.id

    q = select(WithdrawalRequest)

    if status_filter:
        q = q.where(WithdrawalRequest.status == str(status_filter).strip())

    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.where(WithdrawalRequest.request_no.ilike(kw))

    async def rows_iter():
        batch_size = 500
        offset = 0
        record_count = 0

        while True:
            result = await db.execute(
                q.order_by(WithdrawalRequest.created_at.desc())
                .offset(offset).limit(batch_size)
            )
            rows = result.scalars().all()
            if not rows:
                break

            # 批量获取律师名称
            lawyer_ids = sorted({int(x.lawyer_id) for x in rows if x.lawyer_id is not None})
            lawyer_name_by_id: dict[int, str] = {}
            if lawyer_ids:
                lr = await db.execute(select(Lawyer).where(Lawyer.id.in_(lawyer_ids)))
                for l in lr.scalars().all():
                    lawyer_name_by_id[int(l.id)] = str(getattr(l, "name", "") or "")

            for w in rows:
                record_count += 1
                yield {
                    "id": int(w.id),
                    "request_no": str(w.request_no),
                    "lawyer_id": int(w.lawyer_id),
                    "lawyer_name": lawyer_name_by_id.get(int(w.lawyer_id), ""),
                    "amount": float(w.amount),
                    "fee": float(w.fee),
                    "actual_amount": float(w.actual_amount),
                    "withdraw_method": str(w.withdraw_method),
                    "account_info_masked": _mask_account_info(str(w.account_info)),
                    "status": str(w.status),
                    "reject_reason": str(w.reject_reason) if w.reject_reason else "",
                    "admin_id": int(w.admin_id) if w.admin_id else "",
                    "reviewed_at": w.reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if w.reviewed_at else "",
                    "completed_at": w.completed_at.strftime("%Y-%m-%d %H:%M:%S") if w.completed_at else "",
                    "remark": str(w.remark) if w.remark else "",
                    "created_at": w.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": w.updated_at.strftime("%Y-%m-%d %H:%M:%S") if w.updated_at else "",
                }

            offset += batch_size

        # 记录审计日志
        logger.info(f"Admin export withdrawals: user_id={user_id}, records={record_count}")

    fieldnames = [
        "id",
        "request_no",
        "lawyer_id",
        "lawyer_name",
        "amount",
        "fee",
        "actual_amount",
        "withdraw_method",
        "account_info_masked",
        "status",
        "reject_reason",
        "admin_id",
        "reviewed_at",
        "completed_at",
        "remark",
        "created_at",
        "updated_at",
    ]

    return StreamingResponse(_generate_csv_stream(
        fieldnames, rows_iter()), media_type="text/csv")


@router.get(
    "/admin/withdrawals",
    response_model=WithdrawalListResponse,
    summary="管理员-提现申请列表",
)
async def admin_list_withdrawals(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    keyword: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    _ = current_user

    q = select(WithdrawalRequest)
    cq = select(func.count(WithdrawalRequest.id))

    if status_filter:
        q = q.where(WithdrawalRequest.status == str(status_filter).strip())
        cq = cq.where(WithdrawalRequest.status == str(status_filter).strip())

    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.where(WithdrawalRequest.request_no.ilike(kw))
        cq = cq.where(WithdrawalRequest.request_no.ilike(kw))

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
                lawyer_rating=float(rating),
                lawyer_completed_count=int(completed),
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


# 由于文件长度限制，这里先创建基础的管理员路由结构
# 实际实现中需要包含所有管理员相关的路由

@router.post("/admin/settlement/run", summary="管理员-执行到期结算")
async def admin_run_settlement(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user
    return await settlement_service.settle_due_income_records(db)


@router.get(
    "/admin/withdrawals/{withdrawal_id}",
    response_model=AdminWithdrawalDetailResponse,
    summary="管理员-提现申请详情",
)
async def admin_get_withdrawal_detail(
    withdrawal_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user
    res = await db.execute(select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id))
    w = res.scalar_one_or_none()
    if w is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提现申请不存在")

    lawyer_res = await db.execute(select(Lawyer).where(Lawyer.id == w.lawyer_id))
    lawyer = lawyer_res.scalar_one_or_none()

    lawyer_name = str(getattr(lawyer, "name", "") or "") if lawyer else ""
    lawyer_rating = float(
        getattr(
            lawyer,
            "rating",
            0.0) or 0.0) if lawyer else 0.0

    completed_res = await db.execute(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == w.lawyer_id,
            LawyerConsultation.status == "completed",
        )
    )
    completed_count = int(completed_res.scalar() or 0)

    platform_fee_rate = settlement_service.choose_platform_fee_rate(
        int(w.lawyer_id), lawyer_rating, completed_count)

    return AdminWithdrawalDetailResponse(
        id=int(w.id),
        request_no=str(w.request_no),
        lawyer_id=int(w.lawyer_id),
        lawyer_name=lawyer_name if lawyer_name else None,
        lawyer_rating=lawyer_rating if lawyer_rating else None,
        lawyer_completed_count=completed_count if completed_count else None,
        platform_fee_rate=float(
            platform_fee_rate) if platform_fee_rate else None,
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
    "/admin/withdrawals/{withdrawal_id}/approve",
    response_model=WithdrawalItem,
    summary="管理员-批准提现申请",
)
async def admin_approve_withdrawal(
    withdrawal_id: int,
    data: WithdrawalAdminActionRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user
    res = await db.execute(select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id))
    w = res.scalar_one_or_none()
    if w is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提现申请不存在")

    if str(w.status).lower() != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待处理的申请可以批准")

    w.status = "approved"
    w.admin_id = int(current_user.id)
    w.reviewed_at = datetime.now(timezone.utc)
    w.remark = data.remark

    await db.commit()
    await db.refresh(w)

    return await _build_withdrawal_item(db, w)


@router.post(
    "/admin/withdrawals/{withdrawal_id}/complete",
    response_model=WithdrawalItem,
    summary="管理员-完成提现",
)
async def admin_complete_withdrawal(
    withdrawal_id: int,
    data: WithdrawalAdminActionRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user
    res = await db.execute(select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id))
    w = res.scalar_one_or_none()
    if w is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提现申请不存在")

    if str(w.status).lower() != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有已批准的申请可以完成")

    w.status = "completed"
    w.completed_at = datetime.now(timezone.utc)
    w.remark = data.remark

    wallet_res = await db.execute(select(LawyerWallet).where(LawyerWallet.lawyer_id == w.lawyer_id))
    wallet = wallet_res.scalar_one_or_none()
    if wallet:
        wallet.frozen_amount = float(
            wallet.frozen_amount or 0) - float(w.amount)
        wallet.withdrawn_amount = float(
            wallet.withdrawn_amount or 0) + float(w.amount)

    await db.commit()
    await db.refresh(w)

    return await _build_withdrawal_item(db, w)


@router.post(
    "/admin/withdrawals/{withdrawal_id}/reject",
    response_model=WithdrawalItem,
    summary="管理员-拒绝提现申请",
)
async def admin_reject_withdrawal(
    withdrawal_id: int,
    data: WithdrawalRejectRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user
    res = await db.execute(select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id))
    w = res.scalar_one_or_none()
    if w is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提现申请不存在")

    if str(w.status).lower() != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待处理的申请可以拒绝")

    w.status = "rejected"
    w.admin_id = int(current_user.id)
    w.reviewed_at = datetime.now(timezone.utc)
    w.reject_reason = data.reject_reason
    w.remark = data.remark

    wallet_res = await db.execute(select(LawyerWallet).where(LawyerWallet.lawyer_id == w.lawyer_id))
    wallet = wallet_res.scalar_one_or_none()
    if wallet:
        wallet.frozen_amount = float(
            wallet.frozen_amount or 0) - float(w.amount)
        wallet.available_amount = float(
            wallet.available_amount or 0) + float(w.amount)

    await db.commit()
    await db.refresh(w)

    return await _build_withdrawal_item(db, w)


@router.post(
    "/admin/withdrawals/{withdrawal_id}/fail",
    response_model=WithdrawalItem,
    summary="管理员-提现失败",
)
async def admin_fail_withdrawal(
    withdrawal_id: int,
    data: WithdrawalAdminActionRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user
    res = await db.execute(select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id))
    w = res.scalar_one_or_none()
    if w is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提现申请不存在")

    if str(w.status).lower() not in ["pending", "approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待处理或已批准的申请可以标记为失败")

    w.status = "failed"
    w.completed_at = datetime.now(timezone.utc)
    w.remark = data.remark

    wallet_res = await db.execute(select(LawyerWallet).where(LawyerWallet.lawyer_id == w.lawyer_id))
    wallet = wallet_res.scalar_one_or_none()
    if wallet:
        wallet.frozen_amount = float(
            wallet.frozen_amount or 0) - float(w.amount)
        wallet.available_amount = float(
            wallet.available_amount or 0) + float(w.amount)

    await db.commit()
    await db.refresh(w)

    return await _build_withdrawal_item(db, w)


@router.get(
    "/admin/income-records/export",
    summary="管理员-导出收入记录",
)
async def admin_export_income_records(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    from_date: Annotated[str | None, Query(alias="from")] = None,
    to_date: Annotated[str | None, Query(alias="to")] = None,
    lawyer_id: Annotated[int | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
):
    """导出收入记录（流式分页读取，避免大数据量内存溢出）"""
    user_id = current_user.id

    q = select(LawyerIncomeRecord)

    if from_date:
        try:
            from dateutil import parser
            dt = parser.parse(from_date)
            q = q.where(LawyerIncomeRecord.created_at >= dt)
        except (ValueError, Exception):
            pass

    if to_date:
        try:
            from dateutil import parser
            dt = parser.parse(to_date)
            q = q.where(LawyerIncomeRecord.created_at <= dt)
        except (ValueError, Exception):
            pass

    if lawyer_id:
        q = q.where(LawyerIncomeRecord.lawyer_id == lawyer_id)

    if status_filter:
        q = q.where(LawyerIncomeRecord.status == str(status_filter).strip())

    async def rows_iter():
        batch_size = 500
        offset = 0
        record_count = 0
        lawyer_name_by_id: dict[int, str] = {}

        while True:
            result = await db.execute(
                q.order_by(LawyerIncomeRecord.created_at.desc())
                .offset(offset).limit(batch_size)
            )
            rows = result.scalars().all()
            if not rows:
                break

            # 批量获取律师名称
            lawyer_ids = sorted({int(x.lawyer_id) for x in rows if x.lawyer_id is not None})
            if lawyer_ids:
                lr = await db.execute(select(Lawyer).where(Lawyer.id.in_(lawyer_ids)))
                for l in lr.scalars().all():
                    lawyer_name_by_id[int(l.id)] = str(getattr(l, "name", "") or "")

            for r in rows:
                record_count += 1
                yield {
                    "id": int(r.id),
                    "lawyer_id": int(r.lawyer_id),
                    "lawyer_name": lawyer_name_by_id.get(int(r.lawyer_id), ""),
                    "lawyer_income": float(r.lawyer_income),
                    "status": str(r.status),
                    "order_no": str(r.order_no) if r.order_no else "",
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            offset += batch_size

        # 记录审计日志
        logger.info(f"Admin export income records: user_id={user_id}, records={record_count}")

    fieldnames = [
        "id",
        "lawyer_id",
        "lawyer_name",
        "lawyer_income",
        "status",
        "order_no",
        "created_at"]

    return StreamingResponse(_generate_csv_stream(
        fieldnames, rows_iter()), media_type="text/csv")


async def _build_withdrawal_item(
        db: AsyncSession, w: WithdrawalRequest) -> WithdrawalItem:
    """构建 WithdrawalItem 响应"""
    lawyer_res = await db.execute(select(Lawyer).where(Lawyer.id == w.lawyer_id))
    lawyer = lawyer_res.scalar_one_or_none()

    lawyer_name = str(getattr(lawyer, "name", "") or "") if lawyer else ""
    lawyer_rating = float(
        getattr(
            lawyer,
            "rating",
            0.0) or 0.0) if lawyer else 0.0

    completed_res = await db.execute(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == w.lawyer_id,
            LawyerConsultation.status == "completed",
        )
    )
    completed_count = int(completed_res.scalar() or 0)

    platform_fee_rate = settlement_service.choose_platform_fee_rate(
        int(w.lawyer_id), lawyer_rating, completed_count)

    return WithdrawalItem(
        id=int(w.id),
        request_no=str(w.request_no),
        lawyer_id=int(w.lawyer_id),
        lawyer_name=str(lawyer_name) or None,
        lawyer_rating=float(lawyer_rating) if lawyer_rating else None,
        lawyer_completed_count=int(
            completed_count) if completed_count else None,
        platform_fee_rate=float(
            platform_fee_rate) if platform_fee_rate else None,
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
