"""垂直频道路由 - 婚姻/劳动法律服务专属入口

提供婚姻、劳动两个垂直领域的专属法律服务入口，
包括专属咨询、文书生成、案例推荐等功能。
"""
from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..schemas.news import NewsListResponse
from ..services.news_service import news_service
from ..utils.deps import get_current_user_optional

router = APIRouter(prefix="/vertical", tags=["垂直频道"])

# 垂直频道定义
VERTICAL_CHANNELS = {
    "marriage": {
        "name": "婚姻家庭",
        "description": "离婚纠纷、子女抚养、财产分割等婚姻家庭法律服务",
        "keywords": ["离婚", "抚养权", "财产分割", "婚姻", "家庭暴力"],
        "icon": "marriage",
    },
    "labor": {
        "name": "劳动争议",
        "description": "劳动合同、工资福利、工伤赔偿等劳动法律服务",
        "keywords": ["劳动合同", "工资", "工伤", "社保", "劳动仲裁"],
        "icon": "labor",
    },
}


@router.get("/channels")
async def list_channels() -> dict:
    """获取垂直频道列表"""
    return {
        "channels": [
            {
                "key": key,
                "name": info["name"],
                "description": info["description"],
                "icon": info["icon"],
            }
            for key, info in VERTICAL_CHANNELS.items()
        ]
    }


@router.get("/channels/{channel_key}/news", response_model=NewsListResponse)
async def get_channel_news(
    channel_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    page: int = Query(ge=1, default=1),
    page_size: int = Query(ge=1, le=100, default=20),
):
    """获取垂直频道专属新闻推荐

    根据频道关键词过滤相关新闻，支持婚姻/劳动两个垂直领域
    """
    if channel_key not in VERTICAL_CHANNELS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="频道不存在")

    channel_info = VERTICAL_CHANNELS[channel_key]
    keywords = channel_info["keywords"]

    # 使用关键词搜索获取相关新闻
    news_list, total = await news_service.get_news_list(
        db,
        page=page,
        page_size=page_size,
        keyword=" ".join(keywords[:3]),  # 使用前3个关键词
        category=None,
        from_dt=None,
        to_dt=None,
    )

    from ..routers.news.core import _build_news_list_items, _get_ai_risk_levels, _get_ai_keywords
    from ..services.news_service import news_service as ns

    ids = [int(n.id) for n in news_list]
    fav_stats = await ns.get_favorite_stats(db, ids, int(current_user.id) if current_user else None)
    risk_levels = await _get_ai_risk_levels(db, ids)
    keywords_map = await _get_ai_keywords(db, ids)

    user_id = int(current_user.id) if current_user else None
    items = _build_news_list_items(
        news_list,
        fav_stats,
        risk_levels,
        keywords_map,
        user_id)

    return NewsListResponse(items=items, total=total,
                            page=page, page_size=page_size)


@router.get("/channels/{channel_key}/consultation/types")
async def get_consultation_types(channel_key: str) -> dict:
    """获取垂直频道专属咨询类型

    返回该频道支持的法律咨询类型
    """
    if channel_key not in VERTICAL_CHANNELS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="频道不存在")

    consultation_types = {
        "marriage": [
            {"key": "divorce", "name": "离婚咨询", "description": "离婚条件、程序、财产分割咨询"},
            {"key": "custody", "name": "子女抚养", "description": "抚养权争夺、抚养费计算咨询"},
            {"key": "property", "name": "财产分割", "description": "夫妻共同财产认定与分割咨询"},
            {"key": "domestic", "name": "家庭暴力", "description": "人身保护、损害赔偿咨询"},
        ],
        "labor": [
            {"key": "contract", "name": "劳动合同", "description": "合同签订、解除、违约金咨询"},
            {"key": "salary", "name": "工资福利", "description": "拖欠工资、加班费、社保咨询"},
            {"key": "injury", "name": "工伤赔偿", "description": "工伤认定、劳动能力鉴定咨询"},
            {"key": "arbitration", "name": "劳动仲裁", "description": "仲裁申请、流程、证据咨询"},
        ],
    }

    return {
        "channel_key": channel_key,
        "channel_name": VERTICAL_CHANNELS[channel_key]["name"],
        "types": consultation_types.get(channel_key, []),
    }


@router.get("/channels/{channel_key}/document/types")
async def get_document_types(channel_key: str) -> dict:
    """获取垂直频道专属文书类型

    返回该频道支持的法律文书模板
    """
    if channel_key not in VERTICAL_CHANNELS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="频道不存在")

    document_types = {
        "marriage": [
            {"key": "divorce_agreement", "name": "离婚协议书",
                "description": "自愿离婚财产分割子女抚养协议"},
            {"key": "divorce_litigation", "name": "离婚起诉状",
                "description": "向法院提起离婚诉讼"},
            {"key": "custody_agreement", "name": "子女抚养协议",
                "description": "离婚后子女抚养安排协议"},
            {"key": "property_split", "name": "财产分割协议", "description": "夫妻财产分割书面协议"},
        ],
        "labor": [
            {"key": "labor_contract", "name": "劳动合同", "description": "标准劳动合同模板"},
            {"key": "labor_award", "name": "劳动仲裁申请书", "description": "向劳动仲裁委申请仲裁"},
            {"key": "resignation", "name": "辞职报告", "description": "员工主动辞职报告模板"},
            {"key": "severance", "name": "经济补偿协议", "description": "解除劳动关系补偿协议"},
        ],
    }

    return {
        "channel_key": channel_key,
        "channel_name": VERTICAL_CHANNELS[channel_key]["name"],
        "types": document_types.get(channel_key, []),
    }


@router.get("/channels/{channel_key}/stats")
async def get_channel_stats(channel_key: str,
                            db: Annotated[AsyncSession,
                                          Depends(get_db)]) -> dict:
    """获取垂直频道统计数据"""
    if channel_key not in VERTICAL_CHANNELS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="频道不存在")

    channel_info = VERTICAL_CHANNELS[channel_key]
    keywords = channel_info["keywords"]

    # 统计相关新闻数量
    from sqlalchemy import select, func
    from ..models.news import News

    keyword_pattern = f"%{keywords[0]}%"
    count_res = await db.execute(
        select(func.count(News.id)).where(News.content.ilike(keyword_pattern))
    )
    news_count = count_res.scalar() or 0

    return {
        "channel_key": channel_key,
        "channel_name": channel_info["name"],
        "news_count": news_count,
        "keywords": keywords,
    }
