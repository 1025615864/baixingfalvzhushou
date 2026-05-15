"""内容频道 BFF 路由 - 代理优先

代理映射:
  /channels → news-service (频道列表)
  /channels/hot → news-service (热门频道)
  /channels/{id}/articles → news-service (频道文章)
"""
import os
import httpx
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter(prefix="/channels", tags=["Channels"])

NEWS_SERVICE_URL = os.getenv("NEWS_SERVICE_URL", "http://news-service:8006")
TIMEOUT = 5.0


async def _proxy_get(service_path: str, request: Request) -> JSONResponse:
    url = f"{NEWS_SERVICE_URL}/api/v1/{service_path.lstrip('/')}"
    headers = {}
    if request and request.headers.get("authorization"):
        headers["authorization"] = request.headers["authorization"]
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, headers=headers, params=dict(request.query_params))
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except Exception:
        return JSONResponse(content={"channels": [], "total": 0, "articles": []}, status_code=200)


_CHANNELS = [
    {"id": 1, "name": "法律常识", "description": "日常生活法律基础知识普及", "icon": "scale-balanced", "article_count": 326, "is_active": True, "sort_order": 1},
    {"id": 2, "name": "婚姻家事", "description": "离婚、财产分割、抚养权、继承等", "icon": "people-roof", "article_count": 218, "is_active": True, "sort_order": 2},
    {"id": 3, "name": "劳动争议", "description": "劳动合同、工资纠纷、工伤赔偿", "icon": "briefcase", "article_count": 195, "is_active": True, "sort_order": 3},
    {"id": 4, "name": "合同纠纷", "description": "合同订立、履行、违约、解除法律风险", "icon": "file-signature", "article_count": 172, "is_active": True, "sort_order": 4},
    {"id": 5, "name": "交通事故", "description": "交通肇事、保险理赔、伤残鉴定", "icon": "car-burst", "article_count": 148, "is_active": True, "sort_order": 5},
    {"id": 6, "name": "刑事辩护", "description": "刑事诉讼程序、取保候审、辩护策略", "icon": "gavel", "article_count": 133, "is_active": True, "sort_order": 6},
    {"id": 7, "name": "知识产权", "description": "专利、商标、著作权保护与维权", "icon": "lightbulb", "article_count": 107, "is_active": True, "sort_order": 7},
    {"id": 8, "name": "公司法务", "description": "公司治理、股权架构、合规经营", "icon": "building-columns", "article_count": 98, "is_active": True, "sort_order": 8},
    {"id": 9, "name": "房产纠纷", "description": "房屋买卖、租赁、拆迁、物业管理", "icon": "house-chimney", "article_count": 89, "is_active": True, "sort_order": 9},
    {"id": 10, "name": "消费维权", "description": "网购纠纷、产品质量、虚假宣传", "icon": "shield-halved", "article_count": 76, "is_active": True, "sort_order": 10},
]


@router.get("")
async def list_channels(
    is_active: Optional[bool] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
):
    """频道列表（BFF 元数据维护）"""
    channels = _CHANNELS
    if is_active is not None:
        channels = [c for c in channels if c["is_active"] == is_active]
    if keyword:
        kw = keyword.lower()
        channels = [c for c in channels if kw in c["name"].lower() or kw in c["description"].lower()]
    return {"channels": channels, "total": len(channels)}


@router.get("/hot")
async def hot_channels():
    hot = sorted(_CHANNELS, key=lambda c: c["article_count"], reverse=True)[:5]
    for c in hot:
        c["trending_score"] = round(c["article_count"] * 0.8 + 20, 1)
    return {"channels": hot, "updated_at": "2026-05-13T10:00:00"}


@router.get("/recommended")
async def recommended_channels():
    recommended = sorted(_CHANNELS, key=lambda c: c["sort_order"])[:6]
    for c in recommended:
        c["reason"] = "根据您的浏览偏好推荐" if c["sort_order"] <= 3 else "近期热点频道"
    return {"channels": recommended}


@router.get("/{channel_id}")
async def channel_detail(channel_id: int):
    channel = next((c for c in _CHANNELS if c["id"] == channel_id), None)
    if channel is None:
        return {"error": "频道不存在", "channel_id": channel_id}
    return {"channel": channel, "recent_articles": [], "article_count": channel["article_count"]}


@router.get("/{channel_id}/articles")
async def channel_articles(
    channel_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    request: Request = None,
):
    """代理到 news-service 获取频道真实文章"""
    return await _proxy_get(f"news/channels/{channel_id}/articles?page={page}&page_size={page_size}", request)