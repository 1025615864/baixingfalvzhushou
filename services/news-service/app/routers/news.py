"""新闻路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import News
from sqlalchemy import select

router = APIRouter()


class NewsResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    status: str
    view_count: int

    class Config:
        from_attributes = True


@router.get("/", response_model=list[NewsResponse])
async def list_news(page: int = 1, page_size: int = 20, category: Optional[str] = None):
    return []


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news(news_id: int):
    return NewsResponse(id=news_id, title="News", content="", category="news", status="published", view_count=0)
