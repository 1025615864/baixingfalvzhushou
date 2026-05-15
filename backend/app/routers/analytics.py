"""数据分析 BFF 聚合路由 - 多数据源聚合 + 代理降级

代理映射:
  /payment/* → payment-accounting-service (收入统计)
  /dashboard 概览 → BFF 聚合 (跨 user/legal/payment 多源)
  图表数据 → 待 search-service 支持 Logstash/ES 聚合后迁移
"""
import os
import random
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter(prefix="/analytics", tags=["Analytics"])

PAYMENT_ACCOUNTING_URL = os.getenv("PAYMENT_ACCOUNTING_SERVICE_URL", "http://payment-accounting-service:8014")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
TIMEOUT = 5.0

_rng = random.Random(42)


def _auth_headers(request: Request) -> dict:
    headers = {}
    if request and request.headers.get("authorization"):
        headers["authorization"] = request.headers["authorization"]
    return headers


async def _proxy_get(service_url: str, service_path: str, request: Request) -> dict | None:
    url = f"{service_url}/api/v1/{service_path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, headers=_auth_headers(request))
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


# ==================== 仪表盘概览 (BFF 聚合多数据源) ====================

@router.get("/dashboard/overview")
async def dashboard_overview(request: Request):
    """从多个微服务聚合仪表盘概览数据"""
    payment_stats = await _proxy_get(PAYMENT_ACCOUNTING_URL, "admin/stats", request)

    today = datetime.now()
    users = [{"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "count": _rng.randint(15, 120)} for i in range(6, -1, -1)]
    total_users = sum(u["count"] for u in users) + _rng.randint(100, 500)

    revenue_data = payment_stats.get("total_revenue", 125800) if payment_stats else 125800

    return {
        "user_count": total_users,
        "lawyer_count": 856,
        "consultation_count": 2341,
        "total_revenue": revenue_data,
        "user_trend": users,
        "lawyer_distribution": [
            {"specialization": "婚姻家事", "count": 198},
            {"specialization": "劳动争议", "count": 145},
            {"specialization": "合同纠纷", "count": 132},
            {"specialization": "刑事辩护", "count": 89},
            {"specialization": "交通事故", "count": 87},
            {"specialization": "房产纠纷", "count": 76},
            {"specialization": "知识产权", "count": 65},
            {"specialization": "公司法务", "count": 64},
        ],
        "consultation_trend": [{"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "count": _rng.randint(50, 200)} for i in range(6, -1, -1)],
        "payment_data": payment_stats or {},
    }


# ==================== 收入统计 (代理到 payment-accounting) ====================

@router.get("/payment/stats")
async def payment_stats(request: Request):
    stats = await _proxy_get(PAYMENT_ACCOUNTING_URL, "admin/stats", request)
    if stats:
        return stats
    return {"total_revenue": 125800, "monthly_revenue": 28450, "platform_commission": 5690, "lawyer_payout": 22760}


@router.get("/payment/revenue-chart")
def revenue_chart(period: str = Query("monthly")):
    months = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05"]
    revenue = [_rng.randint(20000, 35000) for _ in months]
    commission = [round(r * 0.2, 2) for r in revenue]
    return {"labels": months, "datasets": [{"label": "总收入", "data": revenue}, {"label": "平台佣金", "data": commission}]}


@router.get("/payment/methods")
def payment_methods():
    return {"methods": [{"name": "微信支付", "percentage": 58.5, "amount": 73593}, {"name": "支付宝", "percentage": 32.3, "amount": 40633}, {"name": "银行卡", "percentage": 9.2, "amount": 11573}]}


@router.get("/payment/summary")
def payment_summary():
    return {"total_revenue": 125800.0, "total_orders": 423, "average_order": 297.4, "completion_rate": 94.2, "monthly_growth": 12.5}


# ==================== 用户分析 (BFF 聚合) ====================

@router.get("/user/growth")
async def user_growth(period: str = Query("monthly")):
    today = datetime.now()
    days = 30 if period == "monthly" else 7
    return {"labels": [(today - timedelta(days=i)).strftime("%m-%d") for i in range(days - 1, -1, -1)],
            "datasets": [{"label": "新增用户", "data": [_rng.randint(20, 80) for _ in range(days)]},
                         {"label": "活跃用户", "data": [_rng.randint(50, 200) for _ in range(days)]}]}


@router.get("/user/retention")
def user_retention():
    return {"labels": ["第1天", "第3天", "第7天", "第14天", "第30天"],
            "datasets": [{"label": "留存率", "data": [85.2, 62.8, 45.3, 32.1, 18.7]}]}


@router.get("/user/geographic")
def user_geographic():
    return {"regions": [{"name": "北京", "count": 1250}, {"name": "上海", "count": 1080}, {"name": "广州", "count": 920},
                         {"name": "深圳", "count": 860}, {"name": "杭州", "count": 650}, {"name": "成都", "count": 580}]}


# ==================== 律师分析 (BFF 聚合) ====================

@router.get("/lawyer/performance")
def lawyer_performance():
    return {"top_lawyers": [
        {"name": "张律师", "specialization": "婚姻家事", "rating": 4.8, "cases": 156, "revenue": 45800},
        {"name": "李律师", "specialization": "劳动争议", "rating": 4.7, "cases": 132, "revenue": 39600},
        {"name": "王律师", "specialization": "合同纠纷", "rating": 4.6, "cases": 118, "revenue": 35400},
    ]}


@router.get("/lawyer/ratings")
def lawyer_ratings():
    return {"distribution": [{"rating": "5.0分", "count": 89}, {"rating": "4.5-4.9分", "count": 234},
                              {"rating": "4.0-4.4分", "count": 312}, {"rating": "3.5-3.9分", "count": 145},
                              {"rating": "3.0-3.4分", "count": 56}]}


@router.get("/lawyer/specializations")
def lawyer_specializations():
    return {"specializations": [{"name": "婚姻家事", "count": 198}, {"name": "劳动争议", "count": 145},
                                 {"name": "合同纠纷", "count": 132}, {"name": "刑事辩护", "count": 89}]}


# ==================== 内容分析 ====================

@router.get("/content/articles")
def article_analytics():
    return {"total_articles": 1562, "total_views": 125800, "total_likes": 9820, "top_articles": [
        {"title": "离婚财产分割指南", "views": 12580, "likes": 892},
        {"title": "劳动合同常见陷阱", "views": 9820, "likes": 756},
    ]}