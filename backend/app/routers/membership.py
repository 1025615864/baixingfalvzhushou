from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/membership", tags=["Membership"])

_pricing = [
    {"tier": "monthly", "name": "月度会员", "monthly_price": 29, "annual_price": 299, "annual_discount": 0.14, "lifetime_price": 999, "savings_annual": 49},
    {"tier": "annual", "name": "年度会员", "monthly_price": 25, "annual_price": 299, "annual_discount": 0.14, "lifetime_price": 999, "savings_annual": 49},
    {"tier": "lifetime", "name": "终身会员", "monthly_price": 999, "annual_price": 999, "annual_discount": 0.0, "lifetime_price": 999, "savings_annual": 0},
]

_benefits = {
    "monthly": {
        "tier": "monthly",
        "tier_name": "月度会员",
        "benefits": [
            {"name": "无限次AI咨询", "description": "每月不限次数使用AI智能法律咨询", "icon": "robot"},
            {"name": "律师咨询8折", "description": "平台律师咨询服务享8折优惠", "icon": "discount"},
            {"name": "文书模板", "description": "免费下载20套精选法律文书模板", "icon": "document"},
            {"name": "法律资讯", "description": "专属法律资讯推送与解读", "icon": "news"},
        ],
    },
}

_all_benefits: list[dict] = [
    {"tier": "free", "tier_name": "免费用户", "benefits": [], "features": {"ai_consultation_limit": 3, "document_templates": 5, "lawyer_discount": 0, "priority_support": False, "custom_reports": False}},
    {"tier": "monthly", "tier_name": "月度会员", "benefits": [{"name": "AI咨询每日10次", "description": "每日10次AI法律咨询", "icon": "robot"}, {"name": "律师服务9折", "description": "所有律师服务享9折", "icon": "discount"}, {"name": "文书模板15套", "description": "免费下载15套法律文书", "icon": "document"}, {"name": "专属客服", "description": "工作日专属客服优先响应", "icon": "support"}], "features": {"ai_consultation_limit": 10, "document_templates": 15, "lawyer_discount": 10, "priority_support": True, "custom_reports": False}},
    {"tier": "annual", "tier_name": "年度会员", "benefits": [{"name": "AI咨询无限次", "description": "无限次AI法律咨询", "icon": "robot"}, {"name": "律师服务8折", "description": "所有律师服务享8折", "icon": "discount"}, {"name": "文书模板50套", "description": "免费下载50套法律文书", "icon": "document"}, {"name": "VIP专属客服", "description": "7x24小时VIP专属客服", "icon": "support"}, {"name": "月度法律报告", "description": "每月推送个人法律风险评估报告", "icon": "report"}], "features": {"ai_consultation_limit": -1, "document_templates": 50, "lawyer_discount": 20, "priority_support": True, "custom_reports": True}},
    {"tier": "lifetime", "tier_name": "终身会员", "benefits": [{"name": "AI咨询无限次", "description": "永久无限次AI法律咨询", "icon": "robot"}, {"name": "律师服务7折", "description": "所有律师服务享7折优惠", "icon": "discount"}, {"name": "文书模板全量", "description": "免费下载全部法律文书模板", "icon": "document"}, {"name": "终身专属管家", "description": "终身专属法律管家服务", "icon": "support"}, {"name": "年度法律报告", "description": "年度综合法律风险评估", "icon": "report"}, {"name": "合同审查无限次", "description": "无限次AI合同审查服务", "icon": "contract"}], "features": {"ai_consultation_limit": -1, "document_templates": -1, "lawyer_discount": 30, "priority_support": True, "custom_reports": True}},
]

_current_membership = {
    "user_id": 1,
    "level": "annual",
    "level_name": "年度会员",
    "start_date": "2025-01-01T00:00:00",
    "end_date": "2026-01-01T00:00:00",
    "auto_renew": True,
    "is_active": True,
    "created_at": "2024-06-01T00:00:00",
    "updated_at": "2025-05-01T00:00:00",
    "benefits": _all_benefits[2]["benefits"],
    "is_vip": True,
}

_orders: list[dict] = [
    {"id": "MEM202501010001", "order_no": "MEM202501010001", "order_type": "annual_renewal", "tier": "annual", "duration": "annual", "amount": 299, "payment_method": "wechat_pay", "status": "paid", "paid_at": "2025-01-01T00:05:00", "created_at": "2025-01-01T00:00:00"},
    {"id": "MEM202406010001", "order_no": "MEM202406010001", "order_type": "new_purchase", "tier": "annual", "duration": "annual", "amount": 299, "payment_method": "alipay", "status": "paid", "paid_at": "2024-06-01T00:05:00", "created_at": "2024-06-01T00:00:00"},
]

_history: list[dict] = [
    {"order_no": "MEM202501010001", "order_type": "annual_renewal", "amount": 299, "paid_at": "2025-01-01T00:05:00"},
    {"order_no": "MEM202406010001", "order_type": "new_purchase", "amount": 299, "paid_at": "2024-06-01T00:05:00"},
]

_order_counter = 3


@router.get("/pricing")
def get_pricing():
    return _pricing


@router.get("/me")
def get_my_membership():
    return _current_membership


@router.get("/benefits")
def get_all_benefits():
    return _all_benefits


@router.get("/benefits/{tier}")
def get_tier_benefits(tier: str):
    for b in _all_benefits:
        if b["tier"] == tier:
            return b
    raise HTTPException(status_code=404, detail="会员等级不存在")


@router.get("/orders")
def get_orders():
    total = len(_orders)
    return {"items": _orders, "total": total, "page": 1, "page_size": 20}


@router.post("/orders")
def create_order(body: dict):
    global _order_counter
    tier = body.get("tier", "monthly")
    duration = body.get("duration", "monthly")
    price_map = {"monthly": 29, "annual": 299, "lifetime": 999}
    amount = price_map.get(tier, 29)
    if duration == "annual" and tier == "monthly":
        amount = 299

    order = {
        "id": f"MEM{datetime.now().strftime('%Y%m%d')}{_order_counter:04d}",
        "order_no": f"MEM{datetime.now().strftime('%Y%m%d')}{_order_counter:04d}",
        "tier": tier,
        "duration": duration,
        "amount": amount,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    _orders.append(order)
    _order_counter += 1
    return {"order_no": order["order_no"], "amount": amount, "payment_url": f"/payment/membership/{order['order_no']}"}


@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str):
    for o in _orders:
        if o["id"] == order_id or o["order_no"] == order_id:
            o["status"] = "cancelled"
            return {"success": True, "message": "订单已取消"}
    raise HTTPException(status_code=404, detail="订单不存在")


@router.get("/history")
def get_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    total = len(_history)
    return {"items": _history, "total": total, "page": page, "page_size": page_size}


@router.get("/stats/conversions")
def get_conversion_stats(days: int = Query(30)):
    return {"total_conversions": 256, "conversion_rate": 12.5, "revenue": 76544, "period": str(days)}


@router.get("/stats/revenue")
def get_revenue_stats():
    return {"total_revenue": 435500, "monthly_revenue": 38500, "average_order_value": 299, "period": datetime.now().strftime("%Y-%m")}


@router.post("/upgrade")
def upgrade_membership(body: dict):
    tier = body.get("tier", "annual")
    order_no = f"UPG{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return {"success": True, "order_no": order_no, "payment_url": f"/payment/upgrade/{order_no}"}