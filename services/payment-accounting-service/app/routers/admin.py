from datetime import datetime, date, timedelta, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db, AsyncSessionLocal
from ..models.core import UserBalance, BalanceTransaction, LawyerWallet, Settlement
from ..models.admin import SettlementAudit, FinancialReport, AccountingAuditLog

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import status

    class AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions: Optional[List[str]] = None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in {"super_admin", "admin"}

    _security = HTTPBearer(auto_error=False)

    async def get_admin_user(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> AdminUser:
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证凭据")
        return AdminUser(user_id=1, role="admin")

    def require_domain_role(domain: str, roles: Optional[List[str]] = None):
        async def domain_checker(admin: AdminUser = Depends(get_admin_user)):
            return admin
        return domain_checker


router = APIRouter()


class AuditRequest(BaseModel):
    action: str
    comment: Optional[str] = None


class BatchSettlementRequest(BaseModel):
    settlement_ids: List[int]


class GenerateReportRequest(BaseModel):
    report_date: str
    report_type: str = "daily"


@router.get("/dashboard", dependencies=[Depends(require_domain_role("payment", roles=["payment_admin"]))])
async def dashboard(
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    month_start = datetime(today.year, today.month, 1, tzinfo=timezone.utc)

    income_today = await db.scalar(
        select(func.coalesce(func.sum(BalanceTransaction.amount), 0)).where(
            and_(
                BalanceTransaction.type == "recharge",
                BalanceTransaction.created_at >= today_start,
            )
        )
    )
    expense_today = await db.scalar(
        select(func.coalesce(func.sum(BalanceTransaction.amount), 0)).where(
            and_(
                BalanceTransaction.type == "consume",
                BalanceTransaction.created_at >= today_start,
            )
        )
    )
    pending_count = await db.scalar(
        select(func.count()).where(Settlement.status == "pending")
    )
    pending_amount = await db.scalar(
        select(func.coalesce(func.sum(Settlement.settle_amount), 0)).where(
            Settlement.status == "pending"
        )
    )
    income_month = await db.scalar(
        select(func.coalesce(func.sum(BalanceTransaction.amount), 0)).where(
            and_(
                BalanceTransaction.type == "recharge",
                BalanceTransaction.created_at >= month_start,
            )
        )
    )
    expense_month = await db.scalar(
        select(func.coalesce(func.sum(BalanceTransaction.amount), 0)).where(
            and_(
                BalanceTransaction.type == "consume",
                BalanceTransaction.created_at >= month_start,
            )
        )
    )

    return {
        "today_income": float(income_today or 0),
        "today_expense": float(expense_today or 0),
        "today_profit": float((income_today or 0) - (expense_today or 0)),
        "pending_settlements": pending_count or 0,
        "pending_amount": float(pending_amount or 0),
        "month_income": float(income_month or 0),
        "month_expense": float(expense_month or 0),
        "month_profit": float((income_month or 0) - (expense_month or 0)),
    }


@router.get("/settlements/pending", dependencies=[Depends(require_domain_role("payment", roles=["payment_ops"]))])
async def pending_settlements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    query = select(Settlement).where(Settlement.status == "pending").order_by(Settlement.created_at.desc())
    total = await db.scalar(
        select(func.count()).select_from(Settlement).where(Settlement.status == "pending")
    )
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": s.id,
                "lawyer_id": s.lawyer_id,
                "total_amount": float(s.total_amount or 0),
                "platform_fee": float(s.platform_fee or 0),
                "settle_amount": float(s.settle_amount or 0),
                "status": s.status,
                "period_start": s.period_start.isoformat() if s.period_start else None,
                "period_end": s.period_end.isoformat() if s.period_end else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in items
        ],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }


@router.get("/settlements", dependencies=[Depends(require_domain_role("payment", roles=["payment_admin"]))])
async def list_settlements_admin(
    status: Optional[str] = Query(None),
    lawyer_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    from ..services.settlement_service import SettlementService
    svc = SettlementService(db)
    return await svc.list_settlements(status=status, lawyer_id=lawyer_id, page=page, page_size=page_size)


@router.post("/settlements/{settlement_id}/approve", dependencies=[Depends(require_domain_role("payment", roles=["payment_admin"]))])
async def approve_settlement_admin(
    settlement_id: int,
    admin: AdminUser = Depends(require_domain_role("payment", roles=["payment_admin"])),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    from ..services.settlement_service import SettlementService
    svc = SettlementService(db)
    settlement = await svc.approve_settlement(settlement_id, admin.user_id, getattr(admin, 'username', str(admin.user_id)))
    await db.commit()
    return {"id": settlement.id, "status": settlement.status}


@router.post("/settlements/{settlement_id}/reject", dependencies=[Depends(require_domain_role("payment", roles=["payment_admin"]))])
async def reject_settlement_admin(
    settlement_id: int,
    reason: str = Query("", description="拒绝原因"),
    admin: AdminUser = Depends(require_domain_role("payment", roles=["payment_admin"])),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    from ..services.settlement_service import SettlementService
    svc = SettlementService(db)
    settlement = await svc.reject_settlement(settlement_id, admin.user_id, getattr(admin, 'username', str(admin.user_id)), reason)
    await db.commit()
    return {"id": settlement.id, "status": settlement.status}


@router.post("/settlements/{settlement_id}/audit", dependencies=[Depends(require_domain_role("payment", roles=["payment_admin"]))])
async def audit_settlement(
    settlement_id: int,
    req: AuditRequest,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    settlement = await db.get(Settlement, settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="结算记录不存在")
    if settlement.status != "pending":
        raise HTTPException(status_code=400, detail="只能审核待结算记录")
    if req.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action 必须为 approve 或 reject")

    audit = SettlementAudit(
        settlement_id=settlement_id,
        auditor_id=admin.user_id,
        auditor_name=f"admin_{admin.user_id}",
        action=req.action,
        comment=req.comment,
    )
    db.add(audit)

    settlement.status = "completed" if req.action == "approve" else "rejected"

    log = AccountingAuditLog(
        target_id=settlement_id,
        operator_id=admin.user_id,
        operator_name=f"admin_{admin.user_id}",
        action=f"settlement_{req.action}",
        comment=req.comment,
        extra_data={"settlement_id": settlement_id, "lawyer_id": settlement.lawyer_id},
    )
    db.add(log)

    await db.commit()
    await db.refresh(audit)

    return {
        "id": audit.id,
        "settlement_id": settlement_id,
        "action": req.action,
        "status": settlement.status,
    }


@router.post("/settlements/batch", dependencies=[Depends(require_domain_role("payment", roles=["payment_admin"]))])
async def batch_settlement(
    req: BatchSettlementRequest,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    if not req.settlement_ids:
        raise HTTPException(status_code=400, detail="结算ID列表不能为空")

    result = await db.execute(
        select(Settlement).where(
            and_(
                Settlement.id.in_(req.settlement_ids),
                Settlement.status == "pending",
            )
        )
    )
    settlements = result.scalars().all()

    if not settlements:
        raise HTTPException(status_code=404, detail="未找到待结算记录")

    approved_ids = []
    for s in settlements:
        s.status = "completed"
        audit = SettlementAudit(
            settlement_id=s.id,
            auditor_id=admin.user_id,
            auditor_name=f"admin_{admin.user_id}",
            action="approve",
            comment="批量审核通过",
        )
        db.add(audit)
        approved_ids.append(s.id)

    log = AccountingAuditLog(
        operator_id=admin.user_id,
        operator_name=f"admin_{admin.user_id}",
        action="batch_settlement_approve",
        comment=f"批量审核 {len(approved_ids)} 条结算",
        extra_data={"settlement_ids": approved_ids},
    )
    db.add(log)

    await db.commit()

    return {
        "approved_count": len(approved_ids),
        "approved_ids": approved_ids,
    }


@router.get("/reports", dependencies=[Depends(require_domain_role("payment", roles=["payment_ops"]))])
async def list_reports(
    report_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    query = select(FinancialReport).order_by(FinancialReport.report_date.desc())
    if report_type:
        query = query.where(FinancialReport.report_type == report_type)

    total = await db.scalar(
        select(func.count()).select_from(FinancialReport)
    )
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": r.id,
                "report_date": r.report_date,
                "report_type": r.report_type,
                "total_income": float(r.total_income or 0),
                "total_expense": float(r.total_expense or 0),
                "total_profit": float(r.total_profit or 0),
                "platform_fee": float(r.platform_fee or 0),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in items
        ],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }


@router.post("/reports/generate", dependencies=[Depends(require_domain_role("payment", roles=["payment_admin"]))])
async def generate_report(
    req: GenerateReportRequest,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    if req.report_type not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="report_type 必须为 daily/weekly/monthly")

    existing = await db.scalar(
        select(FinancialReport).where(FinancialReport.report_date == req.report_date)
    )
    if existing:
        raise HTTPException(status_code=409, detail="该日期报表已存在")

    try:
        report_dt = datetime.strptime(req.report_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="report_date 格式错误，应为 YYYY-MM-DD")

    if req.report_type == "daily":
        start = report_dt
        end = report_dt + timedelta(days=1)
    elif req.report_type == "weekly":
        start = report_dt - timedelta(days=report_dt.weekday())
        end = start + timedelta(days=7)
    else:
        start = report_dt.replace(day=1)
        if report_dt.month == 12:
            end = report_dt.replace(year=report_dt.year + 1, month=1, day=1)
        else:
            end = report_dt.replace(month=report_dt.month + 1, day=1)

    total_income = await db.scalar(
        select(func.coalesce(func.sum(BalanceTransaction.amount), 0)).where(
            and_(
                BalanceTransaction.type == "recharge",
                BalanceTransaction.created_at >= start,
                BalanceTransaction.created_at < end,
            )
        )
    )
    total_expense = await db.scalar(
        select(func.coalesce(func.sum(BalanceTransaction.amount), 0)).where(
            and_(
                BalanceTransaction.type == "consume",
                BalanceTransaction.created_at >= start,
                BalanceTransaction.created_at < end,
            )
        )
    )
    platform_fee = await db.scalar(
        select(func.coalesce(func.sum(Settlement.platform_fee), 0)).where(
            and_(
                Settlement.created_at >= start,
                Settlement.created_at < end,
            )
        )
    )

    total_income = float(total_income or 0)
    total_expense = float(total_expense or 0)
    platform_fee = float(platform_fee or 0)
    total_profit = total_income - total_expense

    report = FinancialReport(
        report_date=req.report_date,
        report_type=req.report_type,
        total_income=total_income,
        total_expense=total_expense,
        total_profit=total_profit,
        platform_fee=platform_fee,
        details_json={
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "generated_by": admin.user_id,
        },
    )
    db.add(report)

    log = AccountingAuditLog(
        operator_id=admin.user_id,
        operator_name=f"admin_{admin.user_id}",
        action="generate_report",
        comment=f"生成{req.report_type}报表: {req.report_date}",
        extra_data={"report_date": req.report_date, "report_type": req.report_type},
    )
    db.add(log)

    await db.commit()
    await db.refresh(report)

    return {
        "id": report.id,
        "report_date": report.report_date,
        "report_type": report.report_type,
        "total_income": total_income,
        "total_expense": total_expense,
        "total_profit": total_profit,
        "platform_fee": platform_fee,
    }


@router.get("/reports/{report_id}", dependencies=[Depends(require_domain_role("payment", roles=["payment_ops"]))])
async def get_report(
    report_id: int,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    report = await db.get(FinancialReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")

    return {
        "id": report.id,
        "report_date": report.report_date,
        "report_type": report.report_type,
        "total_income": float(report.total_income or 0),
        "total_expense": float(report.total_expense or 0),
        "total_profit": float(report.total_profit or 0),
        "platform_fee": float(report.platform_fee or 0),
        "details_json": report.details_json,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.get("/reconciliation", dependencies=[Depends(require_domain_role("payment", roles=["payment_admin"]))])
async def reconciliation(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    recharge_subq = (
        select(
            BalanceTransaction.user_id,
            func.coalesce(func.sum(BalanceTransaction.amount), 0).label("recharge_total"),
        )
        .where(BalanceTransaction.type == "recharge")
        .group_by(BalanceTransaction.user_id)
        .subquery()
    )
    consume_subq = (
        select(
            BalanceTransaction.user_id,
            func.coalesce(func.sum(BalanceTransaction.amount), 0).label("consume_total"),
        )
        .where(BalanceTransaction.type == "consume")
        .group_by(BalanceTransaction.user_id)
        .subquery()
    )

    query = (
        select(
            UserBalance.user_id,
            UserBalance.total_recharged,
            UserBalance.total_consumed,
            func.coalesce(recharge_subq.c.recharge_total, 0).label("tx_recharge_total"),
            func.coalesce(consume_subq.c.consume_total, 0).label("tx_consume_total"),
        )
        .outerjoin(recharge_subq, UserBalance.user_id == recharge_subq.c.user_id)
        .outerjoin(consume_subq, UserBalance.user_id == consume_subq.c.user_id)
    )

    total = await db.scalar(select(func.count()).select_from(UserBalance))
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    rows = result.all()

    discrepancies = []
    for row in rows:
        recharge_diff = abs(float(row.total_recharged or 0) - float(row.tx_recharge_total or 0))
        consume_diff = abs(float(row.total_consumed or 0) - float(row.tx_consume_total or 0))
        if recharge_diff > 0.01 or consume_diff > 0.01:
            discrepancies.append({
                "user_id": row.user_id,
                "total_recharged": float(row.total_recharged or 0),
                "tx_recharge_total": float(row.tx_recharge_total or 0),
                "recharge_diff": recharge_diff,
                "total_consumed": float(row.total_consumed or 0),
                "tx_consume_total": float(row.tx_consume_total or 0),
                "consume_diff": consume_diff,
            })

    return {
        "discrepancies": discrepancies,
        "total_checked": total or 0,
        "discrepancy_count": len(discrepancies),
        "page": page,
        "page_size": page_size,
    }


@router.get("/audit-logs", dependencies=[Depends(require_domain_role("payment", roles=["payment_admin"]))])
async def audit_logs(
    action: Optional[str] = None,
    operator_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    query = select(AccountingAuditLog).order_by(AccountingAuditLog.created_at.desc())
    if action:
        query = query.where(AccountingAuditLog.action == action)
    if operator_id:
        query = query.where(AccountingAuditLog.operator_id == operator_id)

    count_query = select(func.count()).select_from(AccountingAuditLog)
    if action:
        count_query = count_query.where(AccountingAuditLog.action == action)
    if operator_id:
        count_query = count_query.where(AccountingAuditLog.operator_id == operator_id)

    total = await db.scalar(count_query)
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": log.id,
                "target_id": log.target_id,
                "operator_id": log.operator_id,
                "operator_name": log.operator_name,
                "action": log.action,
                "comment": log.comment,
                "extra_data": log.extra_data,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in items
        ],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }
