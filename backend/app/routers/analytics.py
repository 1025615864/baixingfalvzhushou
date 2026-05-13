from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from typing import Optional
import random

router = APIRouter(prefix="/analytics", tags=["Analytics"])

_random = random.Random(42)


def _generate_daily_trend(days: int = 30, base: int = 100) -> list[dict]:
    result = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        result.append({"date": date, "value": _random.randint(base - 20, base + 40)})
    return result


def _activity_trend(days: int = 30) -> list[dict]:
    result = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        result.append({
            "date": date,
            "active_users": _random.randint(2800, 4200),
            "new_users": _random.randint(80, 200),
            "returning_users": _random.randint(2500, 3800),
        })
    return result


def _revenue_trend(days: int = 30) -> list[dict]:
    result = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        result.append({
            "date": date,
            "revenue": _random.randint(8000, 18000),
            "membership": _random.randint(3000, 7000),
            "consultation": _random.randint(2000, 6000),
            "other": _random.randint(1000, 4000),
        })
    return result


_FEATURE_USAGE = [
    {"feature": "AI 智能咨询", "usage_count": 12560, "percentage": 32.5, "color": "#3B82F6"},
    {"feature": "律师匹配", "usage_count": 8920, "percentage": 23.1, "color": "#10B981"},
    {"feature": "合同审查", "usage_count": 6540, "percentage": 16.9, "color": "#F59E0B"},
    {"feature": "法律文书", "usage_count": 5230, "percentage": 13.5, "color": "#EF4444"},
    {"feature": "积分商城", "usage_count": 3120, "percentage": 8.1, "color": "#8B5CF6"},
    {"feature": "法律社区", "usage_count": 2280, "percentage": 5.9, "color": "#EC4899"},
]

_REVENUE_SOURCES = [
    {"name": "会员订阅", "value": 185000, "percentage": 42.5, "color": "#3B82F6"},
    {"name": "法律咨询", "value": 128000, "percentage": 29.4, "color": "#10B981"},
    {"name": "合同审查", "value": 65000, "percentage": 14.9, "color": "#F59E0B"},
    {"name": "文书服务", "value": 38000, "percentage": 8.7, "color": "#EF4444"},
    {"name": "其他", "value": 19500, "percentage": 4.5, "color": "#8B5CF6"},
]

_CONVERSION_STEPS = [
    {"name": "访问首页", "count": 125600, "conversion_rate": 100.0, "drop_rate": 0.0, "color": "#3B82F6"},
    {"name": "浏览服务", "count": 56200, "conversion_rate": 44.7, "drop_rate": 55.3, "color": "#10B981"},
    {"name": "开始咨询", "count": 18200, "conversion_rate": 14.5, "drop_rate": 30.2, "color": "#F59E0B"},
    {"name": "完成支付", "count": 5200, "conversion_rate": 4.1, "drop_rate": 10.4, "color": "#EF4444"},
    {"name": "复购使用", "count": 2100, "conversion_rate": 1.7, "drop_rate": 2.4, "color": "#8B5CF6"},
]

_BEHAVIOR_LOGS: list[dict] = []
_log_counter = 1


@router.get("/dashboard/metrics")
def get_dashboard_metrics():
    return {
        "dau": _random.randint(3200, 4500),
        "mau": 125680,
        "total_revenue": 435500,
        "paying_users": 15200,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/dashboard/revenue")
def get_revenue(start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None)):
    return {
        "trend": _revenue_trend(30),
        "sources": _REVENUE_SOURCES,
        "total": sum(s["value"] for s in _REVENUE_SOURCES),
    }


@router.get("/dashboard/user-behavior")
def get_user_behavior():
    return {
        "activity_trend": _activity_trend(30),
        "feature_usage": _FEATURE_USAGE,
        "total_sessions": 256800,
        "average_session_duration": 385,
    }


@router.get("/dashboard/conversion")
def get_conversion(start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None)):
    return {
        "steps": _CONVERSION_STEPS,
        "total_users": 125600,
        "overall_conversion": 1.7,
        "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d"),
    }


@router.post("/funnel/conversion")
def funnel_conversion(body: dict):
    start_date = body.get("start_date", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
    end_date = body.get("end_date", datetime.now().strftime("%Y-%m-%d"))
    return {"start_date": start_date, "end_date": end_date, "steps": _CONVERSION_STEPS[:4]}


@router.post("/retention")
def get_retention(body: dict):
    cohort_date = body.get("cohort_date", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
    return {
        "cohort_date": cohort_date,
        "cohort_count": 1250,
        "retention": [
            {"day": 1, "count": 850, "rate": 68.0},
            {"day": 3, "count": 620, "rate": 49.6},
            {"day": 7, "count": 450, "rate": 36.0},
            {"day": 14, "count": 320, "rate": 25.6},
            {"day": 30, "count": 210, "rate": 16.8},
        ],
    }


@router.post("/log")
def log_behavior(body: dict):
    global _log_counter
    entry = {
        "id": _log_counter,
        "user_id": body.get("user_id", 1),
        "action": body.get("action", ""),
        "resource_type": body.get("resource_type"),
        "resource_id": body.get("resource_id"),
        "metadata": str(body.get("metadata", "")),
        "created_at": datetime.now().isoformat(),
    }
    _BEHAVIOR_LOGS.append(entry)
    _log_counter += 1
    return entry


@router.get("/history")
def get_behavior_history(
    user_id: int = Query(default=1),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None, alias="resource_type"),
    limit: int = Query(20),
    offset: int = Query(0),
):
    items = list(_BEHAVIOR_LOGS)
    if user_id:
        items = [i for i in items if i["user_id"] == user_id]
    if action:
        items = [i for i in items if i["action"] == action]
    if resource_type:
        items = [i for i in items if i["resource_type"] == resource_type]
    total = len(items)
    return {"user_id": user_id, "total": total, "items": items[offset:offset + limit]}


@router.get("/resource/{resource_type}/{resource_id}/view-count")
def get_resource_view_count(resource_type: str, resource_id: int):
    return {"resource_type": resource_type, "resource_id": resource_id, "view_count": _random.randint(100, 5000)}


@router.get("/statistics/actions")
def get_action_statistics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
):
    actions = [
        {"action": "page_view", "count": 125600},
        {"action": "click", "count": 89200},
        {"action": "search", "count": 45200},
        {"action": "submit", "count": 18600},
        {"action": "purchase", "count": 5200},
        {"action": "comment", "count": 12500},
        {"action": "like", "count": 38000},
        {"action": "share", "count": 8900},
        {"action": "download", "count": 7200},
        {"action": "register", "count": 3200},
        {"action": "login", "count": 56800},
    ]
    return {
        "start_date": start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "end_date": end_date or datetime.now().strftime("%Y-%m-%d"),
        "items": [a for a in actions if not action or a["action"] == action],
    }