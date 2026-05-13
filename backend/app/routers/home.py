from datetime import datetime, timedelta
from fastapi import APIRouter, Request
from typing import Optional

router = APIRouter(prefix="/home", tags=["Home"])

_BANNERS = [
    {"id": "1", "title": "AI 智能法律咨询", "subtitle": "专业律师 24 小时在线为您服务", "image_url": "/assets/banners/ai-banner.png", "link": "/ai-consultation", "sort_order": 1, "is_active": True},
    {"id": "2", "title": "民法典专题解读", "subtitle": "了解与您生活息息相关的法律知识", "image_url": "/assets/banners/civil-code.png", "link": "/knowledge/civil-code", "sort_order": 2, "is_active": True},
    {"id": "3", "title": "律师匹配服务", "subtitle": "智能匹配最适合您的专业律师", "image_url": "/assets/banners/lawyer-match.png", "link": "/lawyer-matching", "sort_order": 3, "is_active": True},
    {"id": "4", "title": "积分商城上新", "subtitle": "法律文书模板、咨询服务积分兑换", "image_url": "/assets/banners/points-mall.png", "link": "/points/mall", "sort_order": 4, "is_active": True},
]

_QUICK_ACTIONS = [
    {"id": "ai", "label": "AI 咨询", "icon": "robot", "type": "feature", "link": "/ai-consultation", "badge": None, "content": "智能法律问答"},
    {"id": "lawyer", "label": "找律师", "icon": "user-tie", "type": "feature", "link": "/lawyer-matching", "badge": None, "content": "专业律师匹配"},
    {"id": "consult", "label": "法律咨询", "icon": "comment-dots", "type": "feature", "link": "/consultations", "badge": 3, "content": "在线法律咨询"},
    {"id": "document", "label": "文书模板", "icon": "file-contract", "type": "feature", "link": "/legal-document-mall", "badge": None, "content": "法律文书生成"},
    {"id": "contract", "label": "合同审查", "icon": "file-signature", "type": "feature", "link": "/contracts", "badge": None, "content": "合同审查工具"},
    {"id": "points", "label": "积分商城", "icon": "gift", "type": "feature", "link": "/points", "badge": None, "content": "积分兑换好礼"},
    {"id": "forum", "label": "法律社区", "icon": "users", "type": "community", "link": "/forum", "badge": 12, "content": "法律交流社区"},
    {"id": "news", "label": "法律资讯", "icon": "newspaper", "type": "content", "link": "/news", "badge": None, "content": "法律热点解读"},
]

_RECOMMENDATIONS = [
    {"id": "1", "type": "lawyer", "title": "张律师 - 婚姻家庭法专家", "content": "15年执业经验，擅长离婚财产分割、子女抚养权等领域", "tags": ["婚姻家庭", "财产分割", "抚养权"], "image_url": "/assets/lawyers/zhang.png", "score": 95, "link": "/lawyers/1"},
    {"id": "2", "type": "lawyer", "title": "李律师 - 劳动纠纷专家", "content": "10年劳动仲裁经验，代理劳动争议案件300+", "tags": ["劳动法", "劳动合同", "工伤赔偿"], "image_url": "/assets/lawyers/li.png", "score": 92, "link": "/lawyers/2"},
    {"id": "3", "type": "service", "title": "合同审查服务", "content": "专业律师审阅合同条款，帮您规避法律风险", "tags": ["合同", "审查", "风险控制"], "image_url": "/assets/services/contract-review.png", "score": 88, "link": "/services/contract-review"},
    {"id": "4", "type": "article", "title": "民法典：你应该知道的十大变化", "content": "深度解读民法典对日常生活的影响", "tags": ["民法典", "法律解读", "普法"], "image_url": "/assets/articles/civil-code.png", "score": 90, "link": "/knowledge/1"},
    {"id": "5", "type": "document", "title": "房屋租赁合同模板", "content": "标准房屋租赁合同模板，免费下载使用", "tags": ["租赁合同", "模板", "房产"], "image_url": "/assets/documents/rental.png", "score": 85, "link": "/documents/rental"},
    {"id": "6", "type": "service", "title": "法律咨询服务", "content": "30分钟在线法律咨询，专业律师为您解答", "tags": ["咨询", "在线服务", "法律建议"], "image_url": "/assets/services/consultation.png", "score": 94, "link": "/consultations/new"},
]

_ACTIVITIES = [
    {"id": "1", "type": "consultation", "title": "您收到了张律师的咨询回复", "description": "关于\"劳动合同解除\"的咨询已获专业解答", "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(), "link": "/consultations/1"},
    {"id": "2", "type": "post", "title": "您的帖子获得10个点赞", "description": "「租房押金不退怎么办」获得社区关注", "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(), "link": "/forum/post/123"},
    {"id": "3", "type": "points", "title": "每日签到获得10积分", "description": "连续签到第7天，获得额外奖励", "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(), "link": "/points"},
    {"id": "4", "type": "news", "title": "新法规解读已更新", "description": "《消费者权益保护法》最新修订解读", "timestamp": (datetime.now() - timedelta(days=1)).isoformat(), "link": "/news/1"},
]

_STATS = {
    "total_users": 125680,
    "total_lawyers": 3820,
    "total_consultations": 526941,
    "total_documents": 89120,
    "today_active_users": 3580,
    "monthly_resolved_cases": 12560,
}

_PERSONALIZED_CONTENT = {
    "title": "为您推荐",
    "description": "基于您的浏览历史和兴趣偏好",
    "items": [
        {"id": "1", "type": "article", "title": "劳动争议处理流程全解", "summary": "从仲裁到诉讼，一文读懂劳动争议解决路径", "tags": ["劳动法", "仲裁", "诉讼"], "image_url": "/assets/articles/labor.png", "score": 88},
        {"id": "2", "type": "article", "title": "民间借贷利息的法律保护上限", "summary": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定解读", "tags": ["借贷", "利息", "民间借贷"], "image_url": "/assets/articles/loan.png", "score": 85},
        {"id": "3", "type": "service", "title": "AI 智能文书生成", "summary": "输入基本信息，AI 自动生成法律文书初稿", "tags": ["AI", "文书", "智能"], "image_url": "/assets/services/ai-document.png", "score": 92},
    ],
    "category": "法律知识",
}


@router.get("/data")
def get_home_data():
    return {
        "user": {
            "id": 1,
            "username": "demo_user",
            "nickname": "法律小助手",
            "avatar_url": "/assets/avatars/default.png",
            "member_level": "VIP1",
            "points_balance": 1250,
        },
        "banners": _BANNERS,
        "quick_actions": _QUICK_ACTIONS,
        "recommendations": _RECOMMENDATIONS,
        "stats": _STATS,
        "recent_activity": _ACTIVITIES,
        "personalized_content": _PERSONALIZED_CONTENT,
    }


@router.get("/recommendations")
def get_recommendations(page: int = 1, page_size: int = 10, recommendation_type: Optional[str] = None):
    items = _RECOMMENDATIONS
    if recommendation_type:
        items = [r for r in items if r["type"] == recommendation_type]
    total = len(items)
    start = (page - 1) * page_size
    return {"recommendations": items[start:start + page_size], "total": total, "page": page, "page_size": page_size}


@router.get("/quick-actions")
def get_quick_actions():
    return _QUICK_ACTIONS


@router.get("/stats")
def get_stats():
    return _STATS


@router.get("/banners")
def get_banners():
    return _BANNERS


@router.post("/track-click")
async def track_click(body: dict, request: Request):
    return {"success": True}


@router.post("/interests")
async def set_interests(body: dict):
    return {"success": True, "interests": body.get("interests", [])}