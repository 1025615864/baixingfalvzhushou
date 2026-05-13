from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/settlement", tags=["Settlement"])

_counter = 1
_wallet = {
    "lawyer_id": 1,
    "total_income": 125800,
    "withdrawn_amount": 85000,
    "pending_amount": 15800,
    "frozen_amount": 0,
    "available_amount": 25000,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": datetime.now().isoformat(),
}

_income_records: list[dict] = [
    {"id": 1, "lawyer_id": 1, "consultation_id": 101, "consultation_subject": "离婚财产分割咨询", "order_no": "INC202505010001", "user_paid_amount": 500, "platform_fee": 100, "lawyer_income": 400, "withdrawn_amount": 400, "status": "settled", "settle_time": "2025-05-01T10:00:00", "created_at": "2025-05-01T09:00:00", "updated_at": "2025-05-01T10:00:00"},
    {"id": 2, "lawyer_id": 1, "consultation_id": 102, "consultation_subject": "劳动合同纠纷咨询", "order_no": "INC202505030001", "user_paid_amount": 800, "platform_fee": 160, "lawyer_income": 640, "withdrawn_amount": 640, "status": "settled", "settle_time": "2025-05-03T14:00:00", "created_at": "2025-05-03T09:00:00", "updated_at": "2025-05-03T14:00:00"},
    {"id": 3, "lawyer_id": 1, "consultation_id": 103, "consultation_subject": "工伤赔偿咨询", "order_no": "INC202505050001", "user_paid_amount": 600, "platform_fee": 120, "lawyer_income": 480, "withdrawn_amount": 0, "status": "pending", "settle_time": None, "created_at": "2025-05-05T11:00:00", "updated_at": "2025-05-05T11:00:00"},
    {"id": 4, "lawyer_id": 1, "consultation_id": 104, "consultation_subject": "房屋买卖纠纷咨询", "order_no": "INC202505080001", "user_paid_amount": 1000, "platform_fee": 200, "lawyer_income": 800, "withdrawn_amount": 0, "status": "pending", "settle_time": None, "created_at": "2025-05-08T15:00:00", "updated_at": "2025-05-08T15:00:00"},
    {"id": 5, "lawyer_id": 1, "consultation_id": 105, "consultation_subject": "知识产权侵权咨询", "order_no": "INC202505100001", "user_paid_amount": 1500, "platform_fee": 300, "lawyer_income": 1200, "withdrawn_amount": 0, "status": "pending", "settle_time": None, "created_at": "2025-05-10T10:00:00", "updated_at": "2025-05-10T10:00:00"},
]

_bank_accounts: list[dict] = [
    {"id": 1, "lawyer_id": 1, "account_type": "bank_card", "bank_name": "中国工商银行", "account_no_masked": "6222****1234", "account_holder": "张律师", "is_default": True, "is_active": True, "created_at": "2024-01-15T09:00:00", "updated_at": "2024-01-15T09:00:00"},
    {"id": 2, "lawyer_id": 1, "account_type": "alipay", "bank_name": None, "account_no_masked": "zha***@example.com", "account_holder": "张律师", "is_default": False, "is_active": True, "created_at": "2024-06-01T10:00:00", "updated_at": "2024-06-01T10:00:00"},
]

_withdrawals: list[dict] = [
    {"id": 1, "request_no": "WD202505020001", "lawyer_id": 1, "lawyer_name": "张律师", "lawyer_rating": 4.8, "lawyer_completed_count": 156, "platform_fee_rate": 0.2, "amount": 5000, "fee": 10, "actual_amount": 4990, "withdraw_method": "bank_card", "account_info_masked": "6222****1234", "status": "completed", "reject_reason": None, "admin_id": None, "reviewed_at": "2025-05-02T14:00:00", "completed_at": "2025-05-03T09:00:00", "remark": None, "created_at": "2025-05-02T10:00:00", "updated_at": "2025-05-03T09:00:00"},
    {"id": 2, "request_no": "WD202505080001", "lawyer_id": 1, "lawyer_name": "张律师", "lawyer_rating": 4.8, "lawyer_completed_count": 162, "platform_fee_rate": 0.2, "amount": 3000, "fee": 6, "actual_amount": 2994, "withdraw_method": "alipay", "account_info_masked": "zha***@example.com", "status": "pending", "reject_reason": None, "admin_id": None, "reviewed_at": None, "completed_at": None, "remark": None, "created_at": "2025-05-08T16:00:00", "updated_at": "2025-05-08T16:00:00"},
]


@router.get("/lawyer/wallet")
def get_wallet():
    _wallet["updated_at"] = datetime.now().isoformat()
    return _wallet


@router.get("/lawyer/income-records")
def get_income_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
):
    items = list(_income_records)
    if status:
        items = [r for r in items if r["status"] == status]
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "total": total, "page": page, "page_size": page_size}


@router.get("/lawyer/income-records/export")
def export_income_records(status: Optional[str] = Query(None)):
    return {"message": "导出功能开发中"}


@router.get("/lawyer/bank-accounts")
def get_bank_accounts():
    return {"items": _bank_accounts, "total": len(_bank_accounts)}


@router.post("/lawyer/bank-accounts")
def add_bank_account(body: dict):
    account = {
        "id": len(_bank_accounts) + 1,
        "lawyer_id": 1,
        "account_type": body.get("account_type", "bank_card"),
        "bank_name": body.get("bank_name"),
        "account_no_masked": "****" + (body.get("account_no", ""))[-4:] if body.get("account_no") else "",
        "account_holder": body.get("account_holder", ""),
        "is_default": body.get("is_default", False),
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    if body.get("is_default"):
        for a in _bank_accounts:
            a["is_default"] = False
    _bank_accounts.append(account)
    return account


@router.put("/lawyer/bank-accounts/{account_id}")
def update_bank_account(account_id: int, body: dict):
    for a in _bank_accounts:
        if a["id"] == account_id:
            for k, v in body.items():
                if k in a:
                    a[k] = v
            a["updated_at"] = datetime.now().isoformat()
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
def get_withdrawals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
):
    items = list(_withdrawals)
    if status:
        items = [w for w in items if w["status"] == status]
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "total": total, "page": page, "page_size": page_size}


@router.get("/lawyer/withdrawals/{withdrawal_id}")
def get_withdrawal_detail(withdrawal_id: int):
    for w in _withdrawals:
        if w["id"] == withdrawal_id:
            return w
    raise HTTPException(status_code=404, detail="提现记录不存在")


@router.post("/lawyer/withdrawals")
def request_withdrawal(body: dict):
    global _counter
    amount = body.get("amount", 0)
    withdrawal = {
        "id": len(_withdrawals) + 1,
        "request_no": f"WD{datetime.now().strftime('%Y%m%d')}{_counter:04d}",
        "lawyer_id": 1,
        "lawyer_name": "张律师",
        "lawyer_rating": 4.8,
        "lawyer_completed_count": 165,
        "platform_fee_rate": 0.2,
        "amount": amount,
        "fee": int(amount * 0.002),
        "actual_amount": int(amount * 0.998),
        "withdraw_method": body.get("withdraw_method", "bank_card"),
        "account_info_masked": "6222****1234",
        "status": "pending",
        "reject_reason": None,
        "admin_id": None,
        "reviewed_at": None,
        "completed_at": None,
        "remark": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    _withdrawals.append(withdrawal)
    _counter += 1
    _wallet["pending_amount"] += amount
    _wallet["available_amount"] = max(0, _wallet["available_amount"] - amount)
    return withdrawal


@router.get("/admin/stats")
def get_admin_stats():
    return {
        "month_start": (datetime.now().replace(day=1)).strftime("%Y-%m-%d"),
        "month_end": datetime.now().strftime("%Y-%m-%d"),
        "wallet_summary": {
            "total_income": 125800,
            "withdrawn_amount": 85000,
            "pending_amount": 15800,
            "frozen_amount": 0,
            "available_amount": 25000,
        },
        "withdrawal_summary": {
            "pending_count": 1,
            "pending_amount": 3000,
            "approved_count": 0,
            "approved_amount": 0,
            "completed_month_count": 1,
            "completed_month_amount": 5000,
        },
        "platform_fee_month_total": 880,
        "lawyer_income_month_total": 3520,
        "top_lawyers": [
            {"lawyer_id": 1, "lawyer_name": "张律师", "income_records": 5, "lawyer_income": 3520, "platform_fee": 880},
            {"lawyer_id": 2, "lawyer_name": "李律师", "income_records": 3, "lawyer_income": 2400, "platform_fee": 600},
            {"lawyer_id": 3, "lawyer_name": "王律师", "income_records": 2, "lawyer_income": 1600, "platform_fee": 400},
        ],
    }