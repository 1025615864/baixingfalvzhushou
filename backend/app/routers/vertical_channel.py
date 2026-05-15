"""垂直频道 BFF 路由 - 代理优先

代理映射:
  /channels → BFF 聚合 (频道元数据由 BFF 维护)
  /channels/{key}/news → news-service (真实新闻数据)
  /channels/{key}/consultation/types → BFF (咨询类型元数据)
  /channels/{key}/document/types → BFF (文书类型元数据)
  /channels/{key}/stats → news-service (文章统计)
"""
import os
import httpx
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter(prefix="/vertical", tags=["VerticalChannel"])

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
        return JSONResponse(content={"items": [], "total": 0}, status_code=200)


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
async def get_channel_news(
    channel_key: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    request: Request = None,
):
    """代理到 news-service 获取频道新闻"""
    return await _proxy_get(f"news/vertical/{channel_key}?page={page}&page_size={page_size}", request)


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
async def get_channel_stats(channel_key: str, request: Request = None):
    return await _proxy_get(f"news/vertical/{channel_key}/stats", request)