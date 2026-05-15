"""结算系统 BFF 路由 - 代理优先 + Mock 降级

代理映射:
  /lawyer/wallet → payment-accounting-service (真实 DB 钱包)
  /lawyer/withdrawals/POST → payment-accounting-service (真实提现)
  /admin/stats → payment-accounting-service admin_router (真实统计)

Mock 降级 (待迁移到 payment-accounting-service):
  /lawyer/income-records, /lawyer/bank-accounts, /lawyer/withdrawals GET
"""
from datetime import datetime
import os
import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter(prefix="/settlement", tags=["Settlement"])

PAYMENT_ACCOUNTING_URL = os.getenv("PAYMENT_ACCOUNTING_SERVICE_URL", "http://payment-accounting-service:8014")
TIMEOUT = 5.0


def _auth_headers(request: Request) -> dict:
    headers = {"content-type": "application/json"}
    if request and request.headers.get("authorization"):
        headers["authorization"] = request.headers["authorization"]
    return headers


async def _proxy_get(service_path: str, request: Request) -> JSONResponse:
    url = f"{PAYMENT_ACCOUNTING_URL}/api/v1/{service_path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, headers=_auth_headers(request), params=dict(request.query_params))
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception:
        raise HTTPException(status_code=503, detail="结算服务暂时不可用")


async def _proxy_post(service_path: str, body: dict, request: Request) -> JSONResponse:
    url = f"{PAYMENT_ACCOUNTING_URL}/api/v1/{service_path.lstrip('/')}"
    headers = _auth_headers(request)
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, json=body, headers=headers)
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception:
        raise HTTPException(status_code=503, detail="结算服务暂时不可用")


# ==================== 代理到 payment-accounting-service ====================

@router.get("/lawyer/wallet")
async def get_wallet(request: Request):
    """从支付会计服务获取律师钱包（真实 DB）"""
    return await _proxy_get("settlement/wallet/1", request)


@router.post("/lawyer/withdrawals")
async def request_withdrawal(body: dict, request: Request):
    """提交提现申请到支付会计服务"""
    return await _proxy_post(
        f"settlement/withdraw?lawyer_id=1&amount={body.get('amount', 0)}&bank_account={body.get('account_info_masked', '')}&real_name={body.get('account_holder', '')}",
        body, request
    )


@router.get("/admin/stats")
async def get_admin_stats(request: Request):
    """从支付会计服务获取管理统计"""
    return await _proxy_get("admin/stats", request)


# ==================== Mock 降级（待迁移到 payment-accounting-service）====================

_counter = 1
_income_records: list[dict] = [
    {"id": 1, "lawyer_id": 1, "consultation_id": 101, "consultation_subject": "离婚财产分割咨询", "order_no": "INC202505010001", "user_paid_amount": 500, "platform_fee": 100, "lawyer_income": 400, "withdrawn_amount": 400, "status": "settled", "settle_time": "2025-05-01T10:00:00", "created_at": "2025-05-01T09:00:00", "updated_at": "2025-05-01T10:00:00"},
    {"id": 2, "lawyer_id": 1, "consultation_id": 102, "consultation_subject": "劳动合同纠纷咨询", "order_no": "INC202505030001", "user_paid_amount": 800, "platform_fee": 160, "lawyer_income": 640, "withdrawn_amount": 640, "status": "settled", "settle_time": "2025-05-03T14:00:00", "created_at": "2025-05-03T09:00:00", "updated_at": "2025-05-03T14:00:00"},
    {"id": 3, "lawyer_id": 1, "consultation_id": 103, "consultation_subject": "工伤赔偿咨询", "order_no": "INC202505050001", "user_paid_amount": 600, "platform_fee": 120, "lawyer_income": 480, "withdrawn_amount": 0, "status": "pending", "settle_time": None, "created_at": "2025-05-05T11:00:00", "updated_at": "2025-05-05T11:00:00"},
]

_bank_accounts: list[dict] = [
    {"id": 1, "lawyer_id": 1, "account_type": "bank_card", "bank_name": "中国工商银行", "account_no_masked": "6222****1234", "account_holder": "张律师", "is_default": True, "is_active": True, "created_at": "2024-01-15T09:00:00", "updated_at": "2024-01-15T09:00:00"},
    {"id": 2, "lawyer_id": 1, "account_type": "alipay", "bank_name": None, "account_no_masked": "zha***@example.com", "account_holder": "张律师", "is_default": False, "is_active": True, "created_at": "2024-06-01T10:00:00", "updated_at": "2024-06-01T10:00:00"},
]

_withdrawals: list[dict] = [
    {"id": 1, "request_no": "WD202505020001", "lawyer_id": 1, "lawyer_name": "张律师", "lawyer_rating": 4.8, "lawyer_completed_count": 156, "platform_fee_rate": 0.2, "amount": 5000, "fee": 10, "actual_amount": 4990, "withdraw_method": "bank_card", "account_info_masked": "6222****1234", "status": "completed", "reject_reason": None, "created_at": "2025-05-02T10:00:00"},
]


@router.get("/lawyer/income-records")
def get_income_records(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status: Optional[str] = Query(None)):
    items = list(_income_records)
    if status:
        items = [r for r in items if r["status"] == status]
    return {"items": items, "total": len(items), "page": page, "page_size": page_size}


@router.get("/lawyer/income-records/export")
def export_income_records():
    return {"message": "导出功能开发中（需 payment-accounting-service 支持）"}


@router.get("/lawyer/bank-accounts")
def get_bank_accounts():
    return {"items": _bank_accounts, "total": len(_bank_accounts)}


@router.post("/lawyer/bank-accounts")
def add_bank_account(body: dict):
    account = {"id": len(_bank_accounts) + 1, "lawyer_id": 1, **body, "created_at": datetime.now().isoformat()}
    _bank_accounts.append(account)
    return account


@router.put("/lawyer/bank-accounts/{account_id}")
def update_bank_account(account_id: int, body: dict):
    for a in _bank_accounts:
        if a["id"] == account_id:
            a.update({k: v for k, v in body.items() if k in a})
            return a
    raise HTTPException(status_code=404, detail="账户不存在")


@router.delete("/lawyer/bank-accounts/{account_id}")
def delete_bank_account(account_id: int):
    global _bank_accounts
    _bank_accounts = [a for a in _bank_accounts if a["id"] != account_id]
    return {"message": "删除成功"}


@router.put("/lawyer/bank-accounts/{account_id}/default")
def set_default_bank_account(account_id: int):
    for a in _bank_accounts:
        a["is_default"] = a["id"] == account_id
    return {"message": "设置成功"}


@router.get("/lawyer/withdrawals")
def get_withdrawals(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status: Optional[str] = Query(None)):
    items = list(_withdrawals)
    if status:
        items = [w for w in items if w["status"] == status]
    return {"items": items, "total": len(items), "page": page, "page_size": page_size}


@router.get("/lawyer/withdrawals/{withdrawal_id}")
def get_withdrawal_detail(withdrawal_id: int):
    for w in _withdrawals:
        if w["id"] == withdrawal_id:
            return w
    raise HTTPException(status_code=404, detail="提现记录不存在")