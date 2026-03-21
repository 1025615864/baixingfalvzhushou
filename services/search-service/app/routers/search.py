"""搜索路由"""
from typing import List, Optional
import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..config.settings import get_settings

settings = get_settings()
router = APIRouter()


class SearchItem(BaseModel):
    id: int
    type: str
    title: str
    description: str
    url: str
    score: float = 1.0


class SearchResponse(BaseModel):
    items: List[SearchItem]
    total: int
    query: str
    type: str


class SuggestionItem(BaseModel):
    text: str
    count: int


class SuggestionResponse(BaseModel):
    items: List[SuggestionItem]


class HotSearchItem(BaseModel):
    keyword: str
    count: int


class HotSearchResponse(BaseModel):
    items: List[HotSearchItem]


async def _search_service(service_url: str, endpoint: str, query: str, limit: int) -> List[SearchItem]:
    """从指定服务搜索"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{service_url}{endpoint}"
            response = await client.get(url, params={"q": query, "page_size": limit})
            if response.status_code == 200:
                data = response.json()
                return [
                    SearchItem(
                        id=item.get("id", 0),
                        type=item.get("type", "unknown"),
                        title=item.get("title", ""),
                        description=item.get("description", item.get("summary", "")),
                        url=item.get("url", f"/{item.get('type', 'unknown')}/{item.get('id')}"),
                        score=0.8
                    )
                    for item in data.get("items", [])
                ]
    except Exception:
        pass
    return []


@router.get("/", response_model=SearchResponse)
async def search(
    query: str = Query(..., description="搜索关键词"),
    type: str = Query("all", description="搜索类型: all, news, post, lawyer, knowledge"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """全局搜索"""
    items: List[SearchItem] = []
    
    if type in ("all", "news"):
        news_items = await _search_service(
            settings.news_service_url,
            "/api/v1/news",
            query,
            page_size
        )
        items.extend(news_items)
    
    if type in ("all", "post"):
        post_items = await _search_service(
            settings.community_service_url,
            "/api/v1/community/posts",
            query,
            page_size
        )
        items.extend(post_items)
    
    if type in ("all", "lawyer"):
        lawyer_items = await _search_service(
            settings.legal_service_url,
            "/api/v1/legal/lawyers",
            query,
            page_size
        )
        items.extend(lawyer_items)
    
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = items[start:end]
    
    return SearchResponse(
        items=paginated_items,
        total=total,
        query=query,
        type=type
    )


@router.get("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50)
):
    """搜索建议（自动补全）"""
    base_keywords = [
        "离婚", "劳动", "合同", "工伤", "债务", "房产",
        "继承", "交通事故", "医疗纠纷", "刑事"
    ]
    
    items = [
        SuggestionItem(text=kw, count=1000 - i * 50)
        for i, kw in enumerate(base_keywords)
        if query.lower() in kw.lower()
    ][:limit]
    
    if not items and len(query) >= 2:
        items = [
            SuggestionItem(text=query + kw, count=100)
            for kw in ["相关", "律师", "咨询", "服务"]
        ][:limit]
    
    return SuggestionResponse(items=items)


@router.get("/hot", response_model=HotSearchResponse)
async def get_hot_searches(limit: int = Query(10, ge=1, le=50)):
    """热门搜索"""
    hot_keywords = [
        ("离婚程序", 15230),
        ("劳动合同法", 12450),
        ("工伤认定", 11200),
        ("房屋买卖合同", 9850),
        ("债务纠纷", 8900),
        ("交通事故处理", 7650),
        ("遗产继承", 6540),
        ("医疗事故鉴定", 5430),
        ("刑事拘留", 4320),
        ("劳动仲裁", 3210),
    ]
    
    items = [
        HotSearchItem(keyword=kw, count=cnt)
        for kw, cnt in hot_keywords[:limit]
    ]
    
    return HotSearchResponse(items=items)
