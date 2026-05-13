"""积分系统 API 路由"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database.session import get_db
from ..models import PointsUser, PointsHistory

router = APIRouter(prefix="/points", tags=["Points"])


class EarnPointsBody(BaseModel):
    points: int
    type: str
    description: Optional[str] = None
    source: Optional[str] = None
    reference_id: Optional[str] = None


_points_balance: dict = {"total": 1580, "available": 1520, "frozen": 60, "expiring_soon": 200}

_mock_transactions: list[dict] = [
    {"id": 1, "user_id": 1001, "type": "sign_in", "amount": 10, "balance_after": 1580, "description": "每日签到", "source": "daily_signin", "reference_id": None, "created_at": (datetime.now() - timedelta(hours=2)).isoformat()},
    {"id": 2, "user_id": 1001, "type": "earn", "amount": 50, "balance_after": 1570, "description": "邀请好友注册奖励", "source": "invitation", "reference_id": "INV2024A8F3", "created_at": (datetime.now() - timedelta(days=1)).isoformat()},
    {"id": 3, "user_id": 1001, "type": "earn", "amount": 20, "balance_after": 1520, "description": "完成法律咨询", "source": "consultation", "reference_id": "1", "created_at": (datetime.now() - timedelta(days=2)).isoformat()},
    {"id": 4, "user_id": 1001, "type": "spend", "amount": -100, "balance_after": 1500, "description": "兑换法律咨询服务", "source": "exchange", "reference_id": "EXC001", "created_at": (datetime.now() - timedelta(days=3)).isoformat()},
    {"id": 5, "user_id": 1001, "type": "earn", "amount": 30, "balance_after": 1600, "description": "发表法律问答", "source": "contribution", "reference_id": None, "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
    {"id": 6, "user_id": 1001, "type": "earn", "amount": 50, "balance_after": 1570, "description": "完成合同审查", "source": "contract_review", "reference_id": None, "created_at": (datetime.now() - timedelta(days=7)).isoformat()},
    {"id": 7, "user_id": 1001, "type": "spend", "amount": -200, "balance_after": 1520, "description": "兑换律师优先服务", "source": "exchange", "reference_id": "EXC002", "created_at": (datetime.now() - timedelta(days=10)).isoformat()},
    {"id": 8, "user_id": 1001, "type": "earn", "amount": 100, "balance_after": 1720, "description": "法律知识贡献奖励", "source": "knowledge", "reference_id": None, "created_at": (datetime.now() - timedelta(days=14)).isoformat()},
    {"id": 9, "user_id": 1001, "type": "earn", "amount": 5, "balance_after": 1520, "description": "浏览法律文章", "source": "reading", "reference_id": None, "created_at": (datetime.now() - timedelta(days=20)).isoformat()},
    {"id": 10, "user_id": 1001, "type": "earn", "amount": 15, "balance_after": 1515, "description": "分享法律知识文章", "source": "sharing", "reference_id": None, "created_at": (datetime.now() - timedelta(days=25)).isoformat()},
]

_exchange_items: list[dict] = [
    {"id": 1, "name": "免费法律咨询", "description": "兑换一次30分钟在线法律咨询", "price": 500, "original_price": 0, "category": "consultation", "stock": 100, "image_url": None, "is_active": True, "created_at": "2025-01-01T00:00:00"},
    {"id": 2, "name": "合同审查", "description": "专业律师审查一份合同", "price": 800, "original_price": 0, "category": "document", "stock": 50, "image_url": None, "is_active": True, "created_at": "2025-01-01T00:00:00"},
    {"id": 3, "name": "律师优先预约", "description": "享受律师优先预约服务一次", "price": 300, "original_price": 0, "category": "appointment", "stock": 200, "image_url": None, "is_active": True, "created_at": "2025-01-01T00:00:00"},
    {"id": 4, "name": "诉讼指导手册", "description": "获取专业诉讼指导手册电子版", "price": 200, "original_price": 0, "category": "resource", "stock": 500, "image_url": None, "is_active": True, "created_at": "2025-02-01T00:00:00"},
    {"id": 5, "name": "法律知识课程", "description": "免费获得法律知识在线课程", "price": 600, "original_price": 0, "category": "education", "stock": 30, "image_url": None, "is_active": True, "created_at": "2025-03-01T00:00:00"},
]

_exchange_history: list[dict] = [
    {"id": 1, "user_id": 1001, "exchange_item_id": 4, "exchange_item_name": "诉讼指导手册", "points_spent": 200, "status": "completed", "shipment_info": "发至用户邮箱", "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
    {"id": 2, "user_id": 1001, "exchange_item_id": 3, "exchange_item_name": "律师优先预约", "points_spent": 300, "status": "completed", "shipment_info": "服务已开通", "created_at": (datetime.now() - timedelta(days=15)).isoformat()},
    {"id": 3, "user_id": 1001, "exchange_item_id": 1, "exchange_item_name": "免费法律咨询", "points_spent": 500, "status": "pending", "shipment_info": None, "created_at": (datetime.now() - timedelta(days=30)).isoformat()},
]

_next_tx_id = 11
_next_exchange_id = 4


def _paginate(data: list[dict], page: int, page_size: int) -> dict:
    total = len(data)
    start = (page - 1) * page_size
    items = data[start:start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/balance")
async def get_points_balance():
    return _points_balance


@router.get("/transactions")
async def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trans_type: Optional[str] = Query(None, alias="type"),
):
    data = list(_mock_transactions)
    if trans_type:
        data = [t for t in data if t["type"] == trans_type]
    return _paginate(data, page, page_size)


@router.post("/transactions/earn")
async def earn_points(body: EarnPointsBody, db: AsyncSession = Depends(get_db)):
    global _next_tx_id
    _points_balance["total"] += body.points
    _points_balance["available"] += body.points
    tx = {
        "id": _next_tx_id, "user_id": 1001, "type": "earn",
        "amount": body.points, "balance_after": _points_balance["total"],
        "description": body.description or f"获得{body.points}积分",
        "source": body.source, "reference_id": body.reference_id,
        "created_at": datetime.now().isoformat(),
    }
    _next_tx_id += 1
    _mock_transactions.insert(0, tx)
    try:
        db_history = PointsHistory(
            user_id=1001, action=body.type, points=body.points,
            balance_after=_points_balance["total"],
            description=body.description or f"获得{body.points}积分",
        )
        db.add(db_history)
        await db.commit()
    except Exception:
        pass
    return {"balance": _points_balance, "transaction": tx}


@router.get("/transactions/stats")
async def get_transaction_stats():
    total_earned = sum(t["amount"] for t in _mock_transactions if t["amount"] > 0)
    total_spent = abs(sum(t["amount"] for t in _mock_transactions if t["amount"] < 0))
    return {
        "total_points_earned": total_earned,
        "total_points_spent": total_spent,
        "total_transactions": len(_mock_transactions),
        "current_balance": _points_balance["total"],
    }


@router.get("/exchange/items")
async def get_exchange_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
):
    data = list(_exchange_items)
    if category:
        data = [e for e in data if e["category"] == category]
    return _paginate(data, page, page_size)


@router.get("/exchange/items/{item_id}")
async def get_exchange_item(item_id: int):
    for e in _exchange_items:
        if e["id"] == item_id:
            return e
    return {"detail": "兑换项目不存在"}


@router.post("/exchange/items/{item_id}/redeem")
async def redeem_exchange_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = next((e for e in _exchange_items if e["id"] == item_id), None)
    if not item:
        return {"detail": "兑换项目不存在"}
    if _points_balance["available"] < item["price"]:
        return {"detail": "积分不足以兑换", "required": item["price"], "available": _points_balance["available"]}
    global _next_exchange_id
    _points_balance["available"] -= item["price"]
    _points_balance["total"] -= item["price"]
    record = {
        "id": _next_exchange_id, "user_id": 1001, "exchange_item_id": item_id,
        "exchange_item_name": item["name"], "points_spent": item["price"],
        "status": "completed", "shipment_info": "已兑换", "created_at": datetime.now().isoformat(),
    }
    _next_exchange_id += 1
    _exchange_history.insert(0, record)
    tx = {
        "id": 999, "type": "spend", "amount": -item["price"],
        "description": f"兑换{item['name']}", "source": "exchange", "created_at": datetime.now().isoformat(),
    }
    _mock_transactions.insert(0, tx)
    try:
        db_history = PointsHistory(
            user_id=1001, action="exchange", points=-item["price"],
            balance_after=_points_balance["total"],
            description=f"兑换{item['name']}",
        )
        db.add(db_history)
        await db.commit()
    except Exception:
        pass
    return {"message": "兑换成功", "exchange_record": record, "balance": _points_balance}


@router.get("/exchange/history")
async def get_exchange_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return _paginate(_exchange_history, page, page_size)


@router.get("/rules")
async def get_points_rules():
    return {
        "earn_rules": [
            {"action": "每日签到", "points": 10, "limit": "每天1次"},
            {"action": "邀请好友注册", "points": 50, "limit": "每月10次"},
            {"action": "完成法律咨询", "points": 20, "limit": "每次"},
            {"action": "发表法律问答", "points": 30, "limit": "每天3次"},
            {"action": "合同审查", "points": 50, "limit": "每次"},
            {"action": "浏览法律文章", "points": 5, "limit": "每天5次"},
            {"action": "分享文章", "points": 15, "limit": "每天3次"},
        ],
        "exchange_rules": [
            {"item": "免费法律咨询", "points": 500, "description": "兑换一次30分钟在线法律咨询"},
            {"item": "合同审查", "points": 800, "description": "专业律师审查一份合同"},
            {"item": "律师优先预约", "points": 300, "description": "享受律师优先预约服务一次"},
        ],
        "expiration": "积分有效期为365天，过期自动清零",
    }