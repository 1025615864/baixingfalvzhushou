"""搜索路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def search(query: str, type: str = "all", page: int = 1, page_size: int = 20):
    return {"items": [], "total": 0, "query": query}


@router.get("/suggestions")
async def get_suggestions(query: str, limit: int = 10):
    return {"items": []}


@router.get("/hot")
async def get_hot_searches(limit: int = 10):
    return {"items": []}
