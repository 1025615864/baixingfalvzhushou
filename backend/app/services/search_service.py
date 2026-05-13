from __future__ import annotations

from sqlalchemy import select, func, delete as sa_delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.forum import Post
from app.models.knowledge import LegalKnowledge
from app.models.lawfirm import LawFirm, Lawyer
from app.models.news import News
from app.models.system import SearchHistory


class SearchService:
    @staticmethod
    def _escape_like(value: str) -> str:
        result = value.replace("\\", "\\\\")
        result = result.replace("%", "\\%")
        result = result.replace("_", "\\_")
        return result

    @staticmethod
    def _make_snippet(text: str | None, keyword: str, max_len: int = 100) -> str | None:
        if not text:
            return None
        idx = text.find(keyword)
        if idx == -1:
            return text[:max_len] + ("..." if len(text) > max_len else "")
        start = max(0, idx - max_len // 3)
        end = min(len(text), start + max_len)
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        return snippet

    async def global_search(self, db: AsyncSession, query: str, limit: int = 10) -> dict:
        if not query or len(query) < 2:
            return {"news": [], "posts": [], "lawfirms": [], "lawyers": [], "knowledge": []}

        escaped = self._escape_like(query)
        pattern = f"%{escaped}%"

        news_stmt = select(News).where(News.is_published.is_(True), News.title.ilike(pattern)).limit(limit)
        news_result = await db.execute(news_stmt)
        news_items = [{"id": n.id, "title": n.title, "snippet": self._make_snippet(n.summary or n.content, query), "type": "news"} for n in news_result.scalars().all()]

        post_stmt = select(Post).where(Post.is_deleted.is_(False), Post.title.ilike(pattern)).limit(limit)
        post_result = await db.execute(post_stmt)
        post_items = [{"id": p.id, "title": p.title, "snippet": self._make_snippet(p.content, query), "type": "post"} for p in post_result.scalars().all()]

        firm_stmt = select(LawFirm).where(LawFirm.is_active.is_(True), LawFirm.name.ilike(pattern)).limit(limit)
        firm_result = await db.execute(firm_stmt)
        firm_items = [{"id": f.id, "title": f.name, "snippet": self._make_snippet(f.description, query), "type": "lawfirm"} for f in firm_result.scalars().all()]

        lawyer_stmt = select(Lawyer).where(
            Lawyer.is_active.is_(True),
            or_(Lawyer.name.ilike(pattern), Lawyer.specialties.ilike(pattern)),
        ).limit(limit)
        lawyer_result = await db.execute(lawyer_stmt)
        lawyer_items = [{"id": l.id, "title": l.name, "snippet": self._make_snippet(getattr(l, "specialties", None), query), "type": "lawyer"} for l in lawyer_result.scalars().all()]

        knowledge_stmt = select(LegalKnowledge).where(LegalKnowledge.is_active.is_(True), LegalKnowledge.title.ilike(pattern)).limit(limit)
        knowledge_result = await db.execute(knowledge_stmt)
        knowledge_items = [{"id": k.id, "title": k.title, "snippet": self._make_snippet(k.content, query), "type": "knowledge"} for k in knowledge_result.scalars().all()]

        return {
            "news": news_items,
            "posts": post_items,
            "lawfirms": firm_items,
            "lawyers": lawyer_items,
            "knowledge": knowledge_items,
        }

    async def search_suggestions(self, db: AsyncSession, query: str, limit: int = 5) -> list[str]:
        if not query:
            return []
        escaped = self._escape_like(query)
        pattern = f"{escaped}%"

        suggestions = []

        news_stmt = select(News.title).where(News.is_published.is_(True), News.title.ilike(pattern)).limit(limit * 2)
        news_result = await db.execute(news_stmt)
        for row in news_result.all():
            title = row[0]
            if title and title not in suggestions:
                suggestions.append(title)

        post_stmt = select(Post.title).where(Post.is_deleted.is_(False), Post.title.ilike(pattern)).limit(limit * 2)
        post_result = await db.execute(post_stmt)
        for row in post_result.all():
            title = row[0]
            if title and title not in suggestions:
                suggestions.append(title)

        return suggestions[:limit]

    async def record_search(self, db: AsyncSession, keyword: str, user_id: int | None = None, ip_address: str | None = None) -> None:
        record = SearchHistory(keyword=keyword, user_id=user_id, ip_address=ip_address)
        db.add(record)
        await db.commit()

    async def get_hot_keywords(self, db: AsyncSession, limit: int = 10) -> list[dict]:
        stmt = select(SearchHistory.keyword, func.count().label("count")).group_by(SearchHistory.keyword).order_by(func.count().desc()).limit(limit)
        result = await db.execute(stmt)
        return [{"keyword": row.keyword, "count": row.count} for row in result.all()]

    async def get_user_search_history(self, db: AsyncSession, user_id: int, limit: int = 10) -> list[str]:
        stmt = select(SearchHistory.keyword).where(SearchHistory.user_id == user_id).order_by(SearchHistory.id.desc()).limit(limit)
        result = await db.execute(stmt)
        seen = set()
        history = []
        for row in result.all():
            kw = row[0]
            if kw not in seen:
                seen.add(kw)
                history.append(kw)
        return history

    async def clear_user_search_history(self, db: AsyncSession, user_id: int) -> bool:
        stmt = sa_delete(SearchHistory).where(SearchHistory.user_id == user_id)
        await db.execute(stmt)
        await db.commit()
        return True


search_service = SearchService()
