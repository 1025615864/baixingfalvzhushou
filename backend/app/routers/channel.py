"""内容频道 API 路由 - 法律知识频道"""

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/channels", tags=["Channels"])

_SAMPLE_ARTICLES = [
    {"id": "a001", "title": "民间借贷利息如何计算？一文讲清", "summary": "详解民间借贷利率的LPR四倍上限规定及借条书写要点", "author": "王律师", "publish_time": "2026-05-10T09:00:00", "read_count": 12853},
    {"id": "a002", "title": "新《公司法》修订亮点解读", "summary": "2025年新修订公司法对企业治理和股东权益的重大影响", "author": "公司法务部", "publish_time": "2026-05-09T14:30:00", "read_count": 9620},
    {"id": "a003", "title": "离婚冷静期适用指南", "summary": "协议离婚30天冷静期流程详解及注意事项", "author": "张律师", "publish_time": "2026-05-08T11:15:00", "read_count": 15672},
    {"id": "a004", "title": "交通事故责任认定规则", "summary": "道路交通事故责任划分依据及常见争议焦点", "author": "理赔顾问", "publish_time": "2026-05-07T16:45:00", "read_count": 7341},
    {"id": "a005", "title": "劳动合同到期续签的法律规定", "summary": "劳动合同期满续签、终止的法律后果与补偿标准", "author": "李律师", "publish_time": "2026-05-06T08:30:00", "read_count": 8920},
    {"id": "a006", "title": "购房定金与订金的区别", "summary": "房产交易中定金罚则与订金返还的法律分析", "author": "房产法务", "publish_time": "2026-05-05T13:00:00", "read_count": 11240},
    {"id": "a007", "title": "网络侵权维权路径", "summary": "名誉权、肖像权网络侵权取证与诉讼操作指引", "author": "刘律师", "publish_time": "2026-05-04T10:20:00", "read_count": 4567},
    {"id": "a008", "title": "遗嘱继承常见误区", "summary": "法定继承与遗嘱继承的区别及遗嘱形式要求", "author": "张律师", "publish_time": "2026-05-03T15:10:00", "read_count": 6780},
    {"id": "a009", "title": "消费者七天无理由退货实务", "summary": "《消费者权益保护法》中七日无理由退货的适用范围与例外", "author": "维权顾问", "publish_time": "2026-05-02T09:45:00", "read_count": 10345},
    {"id": "a010", "title": "工伤认定标准与流程", "summary": "工伤认定申请条件、时效及劳动能力鉴定全流程", "author": "李律师", "publish_time": "2026-05-01T14:00:00", "read_count": 8756},
]

_CHANNELS = [
    {"id": 1, "name": "法律常识", "description": "日常生活法律基础知识普及，人人都能看懂的法律入门频道", "icon": "scale-balanced", "article_count": 326, "is_active": True, "sort_order": 1},
    {"id": 2, "name": "婚姻家事", "description": "婚姻家庭法律问题：离婚、财产分割、抚养权、继承等", "icon": "people-roof", "article_count": 218, "is_active": True, "sort_order": 2},
    {"id": 3, "name": "劳动争议", "description": "劳动合同、工资纠纷、工伤赔偿、社保争议一站式解读", "icon": "briefcase", "article_count": 195, "is_active": True, "sort_order": 3},
    {"id": 4, "name": "合同纠纷", "description": "合同订立、履行、违约、解除等各阶段法律风险防范", "icon": "file-signature", "article_count": 172, "is_active": True, "sort_order": 4},
    {"id": 5, "name": "交通事故", "description": "交通肇事、保险理赔、伤残鉴定、赔偿标准全知道", "icon": "car-burst", "article_count": 148, "is_active": True, "sort_order": 5},
    {"id": 6, "name": "刑事辩护", "description": "刑事诉讼程序、取保候审、辩护策略与量刑分析", "icon": "gavel", "article_count": 133, "is_active": True, "sort_order": 6},
    {"id": 7, "name": "知识产权", "description": "专利、商标、著作权保护与侵权维权实务指南", "icon": "lightbulb", "article_count": 107, "is_active": True, "sort_order": 7},
    {"id": 8, "name": "公司法务", "description": "公司治理、股权架构、合规经营与商事争议解决", "icon": "building-columns", "article_count": 98, "is_active": True, "sort_order": 8},
    {"id": 9, "name": "房产纠纷", "description": "房屋买卖、租赁、拆迁、物业管理相关法律实务", "icon": "house-chimney", "article_count": 89, "is_active": True, "sort_order": 9},
    {"id": 10, "name": "消费维权", "description": "网购纠纷、产品质量、虚假宣传、退一赔三维权攻略", "icon": "shield-halved", "article_count": 76, "is_active": True, "sort_order": 10},
]


@router.get("")
async def list_channels(
    is_active: Optional[bool] = Query(default=None, description="按状态过滤"),
    keyword: Optional[str] = Query(default=None, description="搜索关键词"),
):
    channels = _CHANNELS
    if is_active is not None:
        channels = [c for c in channels if c["is_active"] == is_active]
    if keyword:
        keyword_lower = keyword.lower()
        channels = [
            c for c in channels
            if keyword_lower in c["name"].lower() or keyword_lower in c["description"].lower()
        ]
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
    recent_articles = _SAMPLE_ARTICLES[:5]
    return {"channel": channel, "recent_articles": recent_articles, "article_count": len(recent_articles)}


@router.get("/{channel_id}/articles")
async def channel_articles(
    channel_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
):
    start = (page - 1) * page_size
    end = start + page_size
    paged = _SAMPLE_ARTICLES[start:end]
    return {
        "channel_id": channel_id,
        "articles": paged,
        "page": page,
        "page_size": page_size,
        "total": len(_SAMPLE_ARTICLES),
    }