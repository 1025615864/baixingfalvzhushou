"""News service."""
from __future__ import annotations
import time
from typing import Optional


class NewsService:
    def __init__(self):
        self._articles: dict[int, dict] = {}
        self._next_id = 1

    async def create_article(self, title: str, content: str, category: str = "general", author: Optional[str] = None, source: Optional[str] = None) -> dict:
        article_id = self._next_id
        self._next_id += 1
        self._articles[article_id] = {
            "id": article_id, "title": title, "content": content,
            "category": category, "author": author, "source": source,
            "status": "draft", "created_at": time.time(),
            "view_count": 0, "like_count": 0,
        }
        return {"id": article_id, "title": title, "status": "draft"}

    async def get_article(self, article_id: int) -> Optional[dict]:
        return self._articles.get(article_id)

    async def list_articles(self, category: Optional[str] = None, limit: int = 20, offset: int = 0) -> list[dict]:
        articles = list(self._articles.values())
        if category:
            articles = [a for a in articles if a["category"] == category]
        return articles[offset:offset + limit]

    async def publish_article(self, article_id: int) -> dict:
        article = self._articles.get(article_id)
        if not article:
            return {"success": False, "error": "文章不存在"}
        article["status"] = "published"
        return {"success": True, "id": article_id, "status": "published"}

    async def delete_article(self, article_id: int) -> dict:
        if article_id not in self._articles:
            return {"success": False, "error": "文章不存在"}
        del self._articles[article_id]
        return {"success": True}

    def _escape_like(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def _news_snapshot(self, news) -> dict:
        raise NotImplementedError


news_service = NewsService()
