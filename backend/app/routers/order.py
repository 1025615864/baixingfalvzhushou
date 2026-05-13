from __future__ import annotations

from datetime import datetime, timezone, timedelta
import random as _random
import copy as _copy

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/orders", tags=["Orders"])


# ==================== 请求模型 ====================

class CreateOrderRequest(BaseModel):
    service_type: str
    service_id: int
    amount: float
    payment_method: Optional[str] = None
    coupon_code: Optional[str] = None
    note: Optional[str] = None


class CancelOrderRequest(BaseModel):
    reason: Optional[str] = None


class PayOrderRequest(BaseModel):
    payment_method: str


# ==================== Mock 数据 ====================

NOW = datetime.now(timezone.utc)

_MOCK_ORDERS = [
    {
        "id": 1001, "order_no": "BL202605130001", "service_type": "consultation",
        "service_name": "婚姻家庭法律咨询", "lawyer_name": "张明远",
        "amount": 500.00, "payment_status": "paid", "order_status": "completed",
        "created_at": (NOW - timedelta(days=30)).isoformat(),
        "paid_at": (NOW - timedelta(days=30, hours=-1)).isoformat(),
        "payment_method": "wechat",
        "service_details": {"type": "婚姻家庭", "duration": 60, "consultation_id": 301},
        "timeline": [
            {"time": (NOW - timedelta(days=30)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=30, hours=-1)).isoformat(), "event": "支付成功"},
            {"time": (NOW - timedelta(days=29)).isoformat(), "event": "咨询完成"},
        ],
        "related_consultation": {"id": 301, "topic": "离婚财产分割咨询"},
    },
    {
        "id": 1002, "order_no": "BL202605130002", "service_type": "document_review",
        "service_name": "劳动合同审查", "lawyer_name": "李雪萍",
        "amount": 1200.00, "payment_status": "paid", "order_status": "completed",
        "created_at": (NOW - timedelta(days=25)).isoformat(),
        "paid_at": (NOW - timedelta(days=25, hours=-2)).isoformat(),
        "payment_method": "alipay",
        "service_details": {"type": "劳动法", "pages": 8, "review_id": 412},
        "timeline": [
            {"time": (NOW - timedelta(days=25)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=25, hours=-2)).isoformat(), "event": "支付成功"},
            {"time": (NOW - timedelta(days=23)).isoformat(), "event": "审查完成，已发送报告"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1003, "order_no": "BL202605130003", "service_type": "litigation",
        "service_name": "交通事故损害赔偿代理", "lawyer_name": "王大伟",
        "amount": 15000.00, "payment_status": "paid", "order_status": "processing",
        "created_at": (NOW - timedelta(days=20)).isoformat(),
        "paid_at": (NOW - timedelta(days=20, hours=-5)).isoformat(),
        "payment_method": "alipay",
        "service_details": {"type": "交通事故", "case_id": 587, "court": "朝阳区人民法院"},
        "timeline": [
            {"time": (NOW - timedelta(days=20)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=20, hours=-5)).isoformat(), "event": "支付成功"},
            {"time": (NOW - timedelta(days=15)).isoformat(), "event": "已立案"},
            {"time": (NOW - timedelta(days=5)).isoformat(), "event": "已开庭"},
        ],
        "related_consultation": {"id": 305, "topic": "交通事故责任认定咨询"},
    },
    {
        "id": 1004, "order_no": "BL202605130004", "service_type": "membership",
        "service_name": "年度VIP会员", "lawyer_name": None,
        "amount": 599.00, "payment_status": "paid", "order_status": "completed",
        "created_at": (NOW - timedelta(days=60)).isoformat(),
        "paid_at": (NOW - timedelta(days=60, hours=-1)).isoformat(),
        "payment_method": "wechat",
        "service_details": {"type": "年度VIP", "duration_days": 365, "benefits": ["无限次AI咨询", "文档模板免费", "律师优先响应"]},
        "timeline": [
            {"time": (NOW - timedelta(days=60)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=60, hours=-1)).isoformat(), "event": "支付成功"},
            {"time": (NOW - timedelta(days=60, hours=-1)).isoformat(), "event": "会员开通"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1005, "order_no": "BL202605130005", "service_type": "consultation",
        "service_name": "房产纠纷法律咨询", "lawyer_name": "赵雪梅",
        "amount": 800.00, "payment_status": "unpaid", "order_status": "pending",
        "created_at": (NOW - timedelta(hours=3)).isoformat(),
        "paid_at": None,
        "payment_method": None,
        "service_details": {"type": "房产纠纷", "duration": 90, "consultation_id": 310},
        "timeline": [
            {"time": (NOW - timedelta(hours=3)).isoformat(), "event": "订单创建，等待支付"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1006, "order_no": "BL202605130006", "service_type": "document_review",
        "service_name": "借款合同审查", "lawyer_name": "李雪萍",
        "amount": 800.00, "payment_status": "unpaid", "order_status": "pending",
        "created_at": (NOW - timedelta(hours=5)).isoformat(),
        "paid_at": None,
        "payment_method": None,
        "service_details": {"type": "合同法", "pages": 5, "review_id": 415},
        "timeline": [
            {"time": (NOW - timedelta(hours=5)).isoformat(), "event": "订单创建，等待支付"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1007, "order_no": "BL202605130007", "service_type": "litigation",
        "service_name": "知识产权侵权诉讼代理", "lawyer_name": "陈志强",
        "amount": 50000.00, "payment_status": "paid", "order_status": "processing",
        "created_at": (NOW - timedelta(days=14)).isoformat(),
        "paid_at": (NOW - timedelta(days=14, hours=-3)).isoformat(),
        "payment_method": "alipay",
        "service_details": {"type": "知识产权", "case_id": 601, "court": "北京知识产权法院"},
        "timeline": [
            {"time": (NOW - timedelta(days=14)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=14, hours=-3)).isoformat(), "event": "支付成功"},
            {"time": (NOW - timedelta(days=10)).isoformat(), "event": "证据收集中"},
        ],
        "related_consultation": {"id": 312, "topic": "商标侵权初步评估"},
    },
    {
        "id": 1008, "order_no": "BL202605130008", "service_type": "consultation",
        "service_name": "劳动争议法律咨询", "lawyer_name": "刘建国",
        "amount": 300.00, "payment_status": "paid", "order_status": "completed",
        "created_at": (NOW - timedelta(days=12)).isoformat(),
        "paid_at": (NOW - timedelta(days=12, hours=-1)).isoformat(),
        "payment_method": "wechat",
        "service_details": {"type": "劳动法", "duration": 45, "consultation_id": 318},
        "timeline": [
            {"time": (NOW - timedelta(days=12)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=12, hours=-1)).isoformat(), "event": "支付成功"},
            {"time": (NOW - timedelta(days=11)).isoformat(), "event": "咨询完成"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1009, "order_no": "BL202605130009", "service_type": "document_review",
        "service_name": "股权转让协议审查", "lawyer_name": "周明辉",
        "amount": 2000.00, "payment_status": "paid", "order_status": "completed",
        "created_at": (NOW - timedelta(days=8)).isoformat(),
        "paid_at": (NOW - timedelta(days=8, hours=-4)).isoformat(),
        "payment_method": "alipay",
        "service_details": {"type": "公司法", "pages": 15, "review_id": 420},
        "timeline": [
            {"time": (NOW - timedelta(days=8)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=8, hours=-4)).isoformat(), "event": "支付成功"},
            {"time": (NOW - timedelta(days=6)).isoformat(), "event": "审查完成，已发送报告"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1010, "order_no": "BL202605130010", "service_type": "membership",
        "service_name": "季度VIP会员", "lawyer_name": None,
        "amount": 199.00, "payment_status": "paid", "order_status": "completed",
        "created_at": (NOW - timedelta(days=45)).isoformat(),
        "paid_at": (NOW - timedelta(days=45, hours=-1)).isoformat(),
        "payment_method": "wechat",
        "service_details": {"type": "季度VIP", "duration_days": 90, "benefits": ["每日5次AI咨询", "文档模板9折"]},
        "timeline": [
            {"time": (NOW - timedelta(days=45)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=45, hours=-1)).isoformat(), "event": "支付成功"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1011, "order_no": "BL202605130011", "service_type": "litigation",
        "service_name": "遗产继承纠纷代理", "lawyer_name": "张明远",
        "amount": 8000.00, "payment_status": "unpaid", "order_status": "cancelled",
        "created_at": (NOW - timedelta(days=10)).isoformat(),
        "paid_at": None,
        "payment_method": None,
        "cancel_reason": "用户自行协商解决",
        "service_details": {"type": "继承纠纷", "case_id": None, "court": "海淀区人民法院"},
        "timeline": [
            {"time": (NOW - timedelta(days=10)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=8)).isoformat(), "event": "用户申请取消"},
            {"time": (NOW - timedelta(days=8)).isoformat(), "event": "订单已取消"},
        ],
        "related_consultation": {"id": 325, "topic": "遗产继承法律咨询"},
    },
    {
        "id": 1012, "order_no": "BL202605130012", "service_type": "consultation",
        "service_name": "刑事辩护初步咨询", "lawyer_name": "陈志强",
        "amount": 800.00, "payment_status": "paid", "order_status": "refunded",
        "created_at": (NOW - timedelta(days=7)).isoformat(),
        "paid_at": (NOW - timedelta(days=7, hours=-1)).isoformat(),
        "payment_method": "alipay",
        "refund_reason": "当事人自行和解",
        "service_details": {"type": "刑事辩护", "duration": 60, "consultation_id": 330},
        "timeline": [
            {"time": (NOW - timedelta(days=7)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=7, hours=-1)).isoformat(), "event": "支付成功"},
            {"time": (NOW - timedelta(days=5)).isoformat(), "event": "申请退款"},
            {"time": (NOW - timedelta(days=4)).isoformat(), "event": "退款成功"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1013, "order_no": "BL202605130013", "service_type": "litigation",
        "service_name": "合同纠纷诉讼代理", "lawyer_name": "王大伟",
        "amount": 3000.00, "payment_status": "paid", "order_status": "completed",
        "created_at": (NOW - timedelta(days=40)).isoformat(),
        "paid_at": (NOW - timedelta(days=40, hours=-2)).isoformat(),
        "payment_method": "alipay",
        "service_details": {"type": "合同纠纷", "case_id": 555, "court": "上海市浦东新区人民法院"},
        "timeline": [
            {"time": (NOW - timedelta(days=40)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=40, hours=-2)).isoformat(), "event": "支付成功"},
            {"time": (NOW - timedelta(days=35)).isoformat(), "event": "已立案"},
            {"time": (NOW - timedelta(days=20)).isoformat(), "event": "胜诉判决"},
            {"time": (NOW - timedelta(days=15)).isoformat(), "event": "结案"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1014, "order_no": "BL202605130014", "service_type": "document_review",
        "service_name": "房屋买卖合同审查", "lawyer_name": "赵雪梅",
        "amount": 500.00, "payment_status": "unpaid", "order_status": "pending",
        "created_at": (NOW - timedelta(hours=8)).isoformat(),
        "paid_at": None,
        "payment_method": None,
        "service_details": {"type": "房产法", "pages": 3, "review_id": 430},
        "timeline": [
            {"time": (NOW - timedelta(hours=8)).isoformat(), "event": "订单创建，等待支付"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1015, "order_no": "BL202605130015", "service_type": "membership",
        "service_name": "月度VIP会员", "lawyer_name": None,
        "amount": 99.00, "payment_status": "paid", "order_status": "completed",
        "created_at": (NOW - timedelta(days=70)).isoformat(),
        "paid_at": (NOW - timedelta(days=70, hours=-1)).isoformat(),
        "payment_method": "wechat",
        "service_details": {"type": "月度VIP", "duration_days": 30, "benefits": ["每日3次AI咨询"]},
        "timeline": [
            {"time": (NOW - timedelta(days=70)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=70, hours=-1)).isoformat(), "event": "支付成功"},
        ],
        "related_consultation": None,
    },
    {
        "id": 1016, "order_no": "BL202605130016", "service_type": "consultation",
        "service_name": "公司股权结构咨询", "lawyer_name": "周明辉",
        "amount": 600.00, "payment_status": "paid", "order_status": "completed",
        "created_at": (NOW - timedelta(days=18)).isoformat(),
        "paid_at": (NOW - timedelta(days=18, hours=-1)).isoformat(),
        "payment_method": "wechat",
        "service_details": {"type": "公司法", "duration": 60, "consultation_id": 335},
        "timeline": [
            {"time": (NOW - timedelta(days=18)).isoformat(), "event": "订单创建"},
            {"time": (NOW - timedelta(days=18, hours=-1)).isoformat(), "event": "支付成功"},
            {"time": (NOW - timedelta(days=17)).isoformat(), "event": "咨询完成"},
        ],
        "related_consultation": None,
    },
]

_NEXT_ID = 1017


def _generate_order_no() -> str:
    seq = _random.randint(1000, 9999)
    return f"BL{NOW.strftime('%Y%m%d')}{seq:04d}"


def _list_item(order: dict) -> dict:
    return {
        "id": order["id"],
        "order_no": order["order_no"],
        "service_type": order["service_type"],
        "service_name": order["service_name"],
        "lawyer_name": order.get("lawyer_name"),
        "amount": order["amount"],
        "payment_status": order["payment_status"],
        "order_status": order["order_status"],
        "created_at": order["created_at"],
    }


def _detail(order: dict) -> dict:
    result = _copy.deepcopy(order)
    result.pop("cancel_reason", None)
    result.pop("refund_reason", None)
    return result


# ==================== 端点 ====================


@router.get("/orders")
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    filtered = list(_MOCK_ORDERS)

    if status:
        filtered = [o for o in filtered if o["order_status"] == status]

    if keyword:
        kw = keyword.lower()
        filtered = [
            o for o in filtered
            if kw in o["order_no"].lower()
            or kw in o["service_name"].lower()
            or (o.get("lawyer_name") and kw in o["lawyer_name"].lower())
        ]

    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            filtered = [o for o in filtered if datetime.fromisoformat(o["created_at"]) >= dt_from]
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            filtered = [o for o in filtered if datetime.fromisoformat(o["created_at"]) <= dt_to]
        except ValueError:
            pass

    sorted_orders = sorted(filtered, key=lambda o: o["created_at"], reverse=True)

    total = len(sorted_orders)
    start = (page - 1) * page_size
    end = start + page_size
    items = [_list_item(o) for o in sorted_orders[start:end]]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/orders/stats")
async def order_stats():
    by_status: dict = {}
    by_service_type: dict = {}
    total_amount = 0.0
    total_orders = len(_MOCK_ORDERS)

    monthly: dict = {}

    for o in _MOCK_ORDERS:
        total_amount += o["amount"]

        st = o["order_status"]
        by_status[st] = by_status.get(st, 0) + 1

        tp = o["service_type"]
        by_service_type[tp] = by_service_type.get(tp, 0) + 1

        try:
            month_key = datetime.fromisoformat(o["created_at"]).strftime("%Y-%m")
        except (ValueError, TypeError):
            month_key = "unknown"
        if month_key not in monthly:
            monthly[month_key] = {"orders": 0, "amount": 0.0}
        monthly[month_key]["orders"] += 1
        monthly[month_key]["amount"] += o["amount"]

    monthly_trend = [
        {"month": k, "orders": v["orders"], "amount": round(v["amount"], 2)}
        for k, v in sorted(monthly.items())
    ]

    return {
        "total_orders": total_orders,
        "total_amount": round(total_amount, 2),
        "by_status": by_status,
        "by_service_type": by_service_type,
        "monthly_trend": monthly_trend,
    }


@router.get("/orders/{order_id}")
async def get_order_detail(order_id: str):
    order = next((o for o in _MOCK_ORDERS if o["order_no"] == order_id), None)
    if not order:
        try:
            oid = int(order_id)
            order = next((o for o in _MOCK_ORDERS if o["id"] == oid), None)
        except ValueError:
            pass
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "order": _detail(order),
        "service_details": order.get("service_details"),
        "payment_info": {
            "amount": order["amount"],
            "payment_method": order.get("payment_method"),
            "payment_status": order["payment_status"],
            "paid_at": order.get("paid_at"),
        },
        "timeline": order.get("timeline", []),
        "related_consultation": order.get("related_consultation"),
    }


@router.post("/orders")
async def create_order(data: CreateOrderRequest):
    global _NEXT_ID

    valid_types = {"consultation", "document_review", "litigation", "membership"}
    if data.service_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的服务类型: {data.service_type}，可选: {', '.join(sorted(valid_types))}")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="金额必须大于0")

    order_no = _generate_order_no()
    created_at_iso = datetime.now(timezone.utc).isoformat()

    service_names = {
        "consultation": "法律咨询服务",
        "document_review": "文书审查服务",
        "litigation": "诉讼代理服务",
        "membership": "会员服务",
    }

    new_order = {
        "id": _NEXT_ID,
        "order_no": order_no,
        "service_type": data.service_type,
        "service_name": service_names.get(data.service_type, data.service_type),
        "lawyer_name": None,
        "amount": data.amount,
        "payment_status": "unpaid",
        "order_status": "pending",
        "created_at": created_at_iso,
        "paid_at": None,
        "payment_method": data.payment_method,
        "service_details": {
            "type": data.service_type,
            "service_id": data.service_id,
            "note": data.note,
            "coupon_code": data.coupon_code,
        },
        "timeline": [
            {"time": created_at_iso, "event": "订单创建，等待支付"},
        ],
        "related_consultation": None,
    }

    _MOCK_ORDERS.insert(0, new_order)
    _NEXT_ID += 1

    payment_url = f"https://pay.baixingfalv.com/order/{order_no}"

    return {
        "id": new_order["id"],
        "order_no": order_no,
        "amount": data.amount,
        "payment_status": "unpaid",
        "order_status": "pending",
        "payment_url": payment_url,
        "created_at": created_at_iso,
    }


@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str, data: CancelOrderRequest = CancelOrderRequest()):
    order = None
    for o in _MOCK_ORDERS:
        if o["order_no"] == order_id:
            order = o
            break

    if not order:
        try:
            oid = int(order_id)
            order = next((o for o in _MOCK_ORDERS if o["id"] == oid), None)
        except ValueError:
            pass

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order["order_status"] not in ("pending",) or order["payment_status"] not in ("unpaid",):
        raise HTTPException(status_code=400, detail="只有待支付状态的订单才能取消")

    order["order_status"] = "cancelled"
    order["cancel_reason"] = data.reason or "用户取消"
    now_iso = datetime.now(timezone.utc).isoformat()
    order.setdefault("timeline", []).append({"time": now_iso, "event": "订单已取消"})

    return {
        "success": True,
        "message": "订单已取消",
        "order_no": order["order_no"],
        "order_status": "cancelled",
    }


@router.post("/orders/{order_id}/pay")
async def pay_order(order_id: str, data: PayOrderRequest):
    order = None
    for o in _MOCK_ORDERS:
        if o["order_no"] == order_id:
            order = o
            break

    if not order:
        try:
            oid = int(order_id)
            order = next((o for o in _MOCK_ORDERS if o["id"] == oid), None)
        except ValueError:
            pass

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order["order_status"] != "pending" or order["payment_status"] != "unpaid":
        raise HTTPException(status_code=400, detail="订单当前状态不可支付")

    if data.payment_method not in ("wechat", "alipay", "balance"):
        raise HTTPException(status_code=400, detail="不支持的支付方式，可选: wechat, alipay, balance")

    success = _random.random() > 0.05

    if not success:
        now_iso = datetime.now(timezone.utc).isoformat()
        order.setdefault("timeline", []).append({"time": now_iso, "event": f"支付失败 ({data.payment_method})"})
        return {
            "success": False,
            "message": "支付失败，请重试",
            "order_no": order["order_no"],
            "order_status": order["order_status"],
            "payment_status": order["payment_status"],
        }

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    trade_no = f"TRADE{NOW.strftime('%Y%m%d%H%M%S')}{_random.randint(1000, 9999)}"

    order["payment_status"] = "paid"
    order["order_status"] = "paid"
    order["payment_method"] = data.payment_method
    order["paid_at"] = now_iso
    order.setdefault("timeline", []).append({"time": now_iso, "event": f"支付成功 ({data.payment_method})"})

    return {
        "success": True,
        "message": "支付成功",
        "order_no": order["order_no"],
        "trade_no": trade_no,
        "amount": order["amount"],
        "payment_method": data.payment_method,
        "payment_status": "paid",
        "order_status": "paid",
        "paid_at": now_iso,
    }