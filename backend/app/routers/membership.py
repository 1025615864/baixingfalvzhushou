"""会员系统 BFF 路由 - 代理优先 + Mock 降级

代理映射:
  /pricing, /benefits, /me, /upgrade → user-service (真实数据)
  /orders, /history, /stats → BFF Mock (待 ORDER_SERVICE 支持后迁移)
"""
from datetime import datetime
import os
import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/membership", tags=["Membership"])

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
TIMEOUT = 5.0


async def _proxy_get(path: str, request: Request) -> JSONResponse:
    """代理 GET 请求到 user-service"""
    url = f"{USER_SERVICE_URL}/api/v1/membership/{path.lstrip('/')}"
    headers = {}
    if request and request.headers.get("authorization"):
        headers["authorization"] = request.headers["authorization"]
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, headers=headers, params=dict(request.query_params))
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception:
        raise HTTPException(status_code=503, detail="会员服务暂时不可用")


async def _proxy_post(path: str, body: dict, request: Request) -> JSONResponse:
    """代理 POST 请求到 user-service"""
    url = f"{USER_SERVICE_URL}/api/v1/membership/{path.lstrip('/')}"
    headers = {"content-type": "application/json"}
    if request and request.headers.get("authorization"):
        headers["authorization"] = request.headers["authorization"]
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, json=body, headers=headers)
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception:
        raise HTTPException(status_code=503, detail="会员服务暂时不可用")


# ==================== 代理到 user-service ====================

@router.get("/pricing")
async def get_pricing(request: Request):
    return await _proxy_get("pricing", request)


@router.get("/benefits")
async def get_all_benefits(request: Request):
    return await _proxy_get("benefits", request)


@router.get("/benefits/{tier}")
async def get_tier_benefits(tier: str, request: Request):
    return await _proxy_get(f"benefits/{tier}", request)


@router.get("/me")
async def get_my_membership(request: Request):
    return await _proxy_get("me", request)


@router.post("/upgrade")
async def upgrade_membership(body: dict, request: Request):
    return await _proxy_post("upgrade", body, request)


# ==================== Mock 降级（待微服务支持后迁移）====================

_orders: list[dict] = [
    {"id": "MEM202501010001", "order_no": "MEM202501010001", "order_type": "annual_renewal", "tier": "annual", "duration": "annual", "amount": 299, "payment_method": "wechat_pay", "status": "paid", "paid_at": "2025-01-01T00:05:00", "created_at": "2025-01-01T00:00:00"},
    {"id": "MEM202406010001", "order_no": "MEM202406010001", "order_type": "new_purchase", "tier": "annual", "duration": "annual", "amount": 299, "payment_method": "alipay", "status": "paid", "paid_at": "2024-06-01T00:05:00", "created_at": "2024-06-01T00:00:00"},
]
_order_counter = 3


@router.get("/orders")
async def get_orders():
    return {"items": _orders, "total": len(_orders), "page": 1, "page_size": 20}


@router.post("/orders")
async def create_order(body: dict):
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
        "tier": tier, "duration": duration, "amount": amount,
        "status": "pending", "created_at": datetime.now().isoformat(),
    }
    _orders.append(order)
    _order_counter += 1
    return {"order_no": order["order_no"], "amount": amount, "payment_url": f"/payment/membership/{order['order_no']}"}


@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str):
    for o in _orders:
        if o["id"] == order_id or o["order_no"] == order_id:
            o["status"] = "cancelled"
            return {"success": True, "message": "订单已取消"}
    raise HTTPException(status_code=404, detail="订单不存在")


@router.get("/history")
async def get_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    _history = [{"order_no": o["order_no"], "order_type": o["order_type"], "amount": o["amount"], "paid_at": o.get("paid_at")} for o in _orders]
    return {"items": _history, "total": len(_history), "page": page, "page_size": page_size}


@router.get("/stats/conversions")
async def get_conversion_stats(days: int = Query(30)):
    return {"total_conversions": len(_orders), "conversion_rate": 100.0, "revenue": sum(o["amount"] for o in _orders if o["status"] == "paid"), "period": str(days)}


@router.get("/stats/revenue")
async def get_revenue_stats():
    paid = sum(o["amount"] for o in _orders if o["status"] == "paid")
    return {"total_revenue": paid, "monthly_revenue": paid, "average_order_value": 299, "period": datetime.now().strftime("%Y-%m")}