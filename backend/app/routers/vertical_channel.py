from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/vertical", tags=["VerticalChannel"])

_MARRIAGE_NEWS = [
    {"id": 1, "title": "民法典婚姻家庭编最新司法解释解读", "content": "最高人民法院发布关于适用民法典婚姻家庭编的解释，对离婚冷静期、夫妻共同债务、子女抚养权等内容进行了细化规定。", "source": "最高人民法院", "publish_time": "2025-05-10T09:00:00", "view_count": 12580, "is_favorite": False, "favorite_count": 256, "risk_level": None, "keywords": ["民法典", "婚姻家庭", "司法解释"]},
    {"id": 2, "title": "离婚时房产分割的5种常见情形", "content": "婚前购房、婚后购房、父母出资购房等不同情形下，离婚时房产如何分割？本文为您详细梳理。", "source": "法律日报", "publish_time": "2025-05-08T14:30:00", "view_count": 8920, "is_favorite": True, "favorite_count": 180, "risk_level": None, "keywords": ["离婚", "房产分割", "财产分割"]},
    {"id": 3, "title": "家暴受害人如何申请人身安全保护令", "content": "遭受家庭暴力时，受害人可以申请人身安全保护令。本文介绍申请条件、流程和所需材料。", "source": "全国妇联", "publish_time": "2025-05-06T11:00:00", "view_count": 6540, "is_favorite": False, "favorite_count": 312, "risk_level": "high", "keywords": ["家暴", "人身保护令", "维权"]},
    {"id": 4, "title": "夫妻共同债务认定新规：这些债务你不用还", "content": "民法典明确规定，超出家庭日常需要的债务不属于夫妻共同债务，债权人需举证。", "source": "法治日报", "publish_time": "2025-05-04T08:00:00", "view_count": 7230, "is_favorite": False, "favorite_count": 145, "risk_level": None, "keywords": ["夫妻共同债务", "债务认定", "民法典"]},
    {"id": 5, "title": "子女抚养权纠纷：法院判决的关键因素", "content": "离婚时子女抚养权如何判定？法院会考虑孩子的年龄、父母的抚养能力、孩子的意愿等多种因素。", "source": "中国法院网", "publish_time": "2025-05-01T16:00:00", "view_count": 10200, "is_favorite": False, "favorite_count": 220, "risk_level": "medium", "keywords": ["抚养权", "离婚", "未成年人"]},
]

_LABOR_NEWS = [
    {"id": 101, "title": "2025年劳动合同签订注意事项", "content": "新修订的劳动合同法对试用期、违约金、竞业限制等条款进行了调整，企业和劳动者都需了解。", "source": "人社部", "publish_time": "2025-05-10T10:00:00", "view_count": 15680, "is_favorite": True, "favorite_count": 380, "risk_level": None, "keywords": ["劳动合同", "劳动法", "2025新规"]},
    {"id": 102, "title": "被违法辞退怎么办？赔偿标准详解", "content": "用人单位违法解除劳动合同，劳动者可获得经济赔偿金。本文详解2N赔偿的计算方法和维权途径。", "source": "中国劳动保障报", "publish_time": "2025-05-08T09:30:00", "view_count": 11200, "is_favorite": False, "favorite_count": 450, "risk_level": "high", "keywords": ["违法辞退", "赔偿金", "劳动仲裁"]},
    {"id": 103, "title": "工伤认定流程及赔偿项目一览", "content": "从工伤申报到赔偿到位，详细梳理工伤认定的完整流程和各项赔偿标准。", "source": "安全生产报", "publish_time": "2025-05-06T14:00:00", "view_count": 9800, "is_favorite": False, "favorite_count": 210, "risk_level": "medium", "keywords": ["工伤", "工伤认定", "工伤赔偿"]},
    {"id": 104, "title": "加班工资怎么算？法定节假日三倍工资全解读", "content": "工作日加班、休息日加班、法定节假日加班，计算标准各不相同。一文理清加班费计算规则。", "source": "工人日报", "publish_time": "2025-05-03T11:00:00", "view_count": 13500, "is_favorite": False, "favorite_count": 520, "risk_level": None, "keywords": ["加班", "加班费", "劳动权益"]},
    {"id": 105, "title": "竞业限制协议：你需要知道的权益保护", "content": "签了竞业限制协议就必须遵守吗？竞业限制的范围、期限和补偿金标准是什么？", "source": "法治日报", "publish_time": "2025-05-01T08:00:00", "view_count": 7800, "is_favorite": False, "favorite_count": 165, "risk_level": None, "keywords": ["竞业限制", "劳动合同", "补偿金"]},
]

_CHANNELS = [
    {"key": "marriage", "name": "婚姻家事法律服务", "description": "离婚纠纷、财产分割、子女抚养、家庭暴力等婚姻家事法律服务", "icon": "heart"},
    {"key": "labor", "name": "劳动维权法律服务", "description": "劳动合同、加班工资、工伤赔偿、违法辞退等劳动法律服务", "icon": "briefcase"},
]

_CONSULTATION_TYPES = {
    "marriage": [
        {"key": "divorce", "name": "离婚纠纷", "description": "协议离婚、诉讼离婚、财产分割、债务处理"},
        {"key": "child_custody", "name": "子女抚养", "description": "抚养权归属、抚养费计算、探视权"},
        {"key": "domestic_violence", "name": "家庭暴力", "description": "人身安全保护令、证据收集、法律救济"},
        {"key": "property", "name": "财产分割", "description": "婚前财产认定、共同财产分割、房产纠纷"},
        {"key": "inheritance", "name": "遗产继承", "description": "法定继承、遗嘱继承、遗产分割"},
    ],
    "labor": [
        {"key": "contract", "name": "劳动合同纠纷", "description": "合同签订、变更、解除、终止争议"},
        {"key": "dismissal", "name": "辞退维权", "description": "违法辞退、经济性裁员、赔偿金计算"},
        {"key": "overtime", "name": "加班工资", "description": "加班费计算、工时制度、休息休假"},
        {"key": "work_injury", "name": "工伤认定", "description": "工伤申报、伤残鉴定、工伤待遇"},
        {"key": "social_security", "name": "社保权益", "description": "社保缴纳、公积金、社保纠纷"},
    ],
}

_DOCUMENT_TYPES = {
    "marriage": [
        {"key": "divorce_agreement", "name": "离婚协议书", "description": "夫妻双方自愿离婚的协议模板"},
        {"key": "divorce_petition", "name": "离婚起诉状", "description": "向法院起诉离婚的法律文书"},
        {"key": "property_division", "name": "财产分割协议", "description": "夫妻财产分割的书面协议"},
        {"key": "protection_order", "name": "人身保护令申请", "description": "申请法院签发人身安全保护令"},
        {"key": "custody_agreement", "name": "抚养权协议", "description": "子女抚养权归属及抚养费协议"},
    ],
    "labor": [
        {"key": "labor_contract", "name": "劳动合同模板", "description": "标准劳动合同文本"},
        {"key": "arbitration_application", "name": "劳动仲裁申请书", "description": "向劳动仲裁委提出仲裁申请"},
        {"key": "dismissal_notice", "name": "解除劳动合同通知", "description": "用人单位解除合同的通知书"},
        {"key": "compensation_claim", "name": "赔偿金申请书", "description": "要求支付经济补偿或赔偿"},
        {"key": "work_injury_report", "name": "工伤认定申请表", "description": "工伤认定申请的标准表格"},
    ],
}


@router.get("/channels")
def get_channels():
    return {"channels": _CHANNELS}


@router.get("/channels/{channel_key}/news")
def get_channel_news(
    channel_key: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    news_map = {"marriage": _MARRIAGE_NEWS, "labor": _LABOR_NEWS}
    items = news_map.get(channel_key, [])
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "total": total, "page": page, "page_size": page_size}


@router.get("/channels/{channel_key}/consultation/types")
def get_channel_consultation_types(channel_key: str):
    types = _CONSULTATION_TYPES.get(channel_key, [])
    channel = next((c for c in _CHANNELS if c["key"] == channel_key), {"key": channel_key, "name": channel_key})
    return {"channel_key": channel_key, "channel_name": channel["name"], "types": types}


@router.get("/channels/{channel_key}/document/types")
def get_channel_document_types(channel_key: str):
    types = _DOCUMENT_TYPES.get(channel_key, [])
    channel = next((c for c in _CHANNELS if c["key"] == channel_key), {"key": channel_key, "name": channel_key})
    return {"channel_key": channel_key, "channel_name": channel["name"], "types": types}


@router.get("/channels/{channel_key}/stats")
def get_channel_stats(channel_key: str):
    news_map = {"marriage": _MARRIAGE_NEWS, "labor": _LABOR_NEWS}
    items = news_map.get(channel_key, [])
    keywords = list(set(kw for n in items for kw in n.get("keywords", [])))
    channel = next((c for c in _CHANNELS if c["key"] == channel_key), {"key": channel_key, "name": channel_key})
    return {"channel_key": channel_key, "channel_name": channel["name"], "news_count": len(items), "keywords": keywords}