from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, func, delete as sa_delete, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.knowledge import LegalKnowledge


class KnowledgeService:

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_dict(article: LegalKnowledge) -> dict:
        return {
            "id": article.id,
            "knowledge_type": article.knowledge_type,
            "title": article.title,
            "article_number": article.article_number,
            "content": article.content,
            "summary": article.summary,
            "category": article.category,
            "keywords": article.keywords,
            "source": article.source,
            "source_url": article.source_url,
            "source_version": article.source_version,
            "effective_date": article.effective_date,
            "weight": article.weight,
            "is_active": article.is_active,
            "is_vectorized": article.is_vectorized,
            "vector_id": article.vector_id,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "updated_at": article.updated_at.isoformat() if article.updated_at else None,
        }

    async def get_articles(
        self,
        page: int = 1,
        page_size: int = 20,
        knowledge_type: Optional[str] = None,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        query = select(LegalKnowledge)
        count_query = select(func.count()).select_from(LegalKnowledge)

        if knowledge_type:
            query = query.where(LegalKnowledge.knowledge_type == knowledge_type)
            count_query = count_query.where(LegalKnowledge.knowledge_type == knowledge_type)
        if category:
            query = query.where(LegalKnowledge.category == category)
            count_query = count_query.where(LegalKnowledge.category == category)
        if keyword:
            kw = f"%{keyword}%"
            query = query.where(
                (LegalKnowledge.title.ilike(kw)) | (LegalKnowledge.keywords.ilike(kw))
            )
            count_query = count_query.where(
                (LegalKnowledge.title.ilike(kw)) | (LegalKnowledge.keywords.ilike(kw))
            )
        if is_active is not None:
            query = query.where(LegalKnowledge.is_active == is_active)
            count_query = count_query.where(LegalKnowledge.is_active == is_active)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(LegalKnowledge.weight.desc(), LegalKnowledge.id.desc())
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        articles = list(result.scalars().all())

        return {
            "items": [self._to_dict(a) for a in articles],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_article(self, article_id: int) -> dict:
        result = await self.db.execute(
            select(LegalKnowledge).where(LegalKnowledge.id == article_id)
        )
        article = result.scalar_one_or_none()
        if not article:
            raise HTTPException(status_code=404, detail="知识条目不存在")
        return self._to_dict(article)

    async def create_article(self, data: dict) -> dict:
        article = LegalKnowledge(**data)
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        return self._to_dict(article)

    async def update_article(self, article_id: int, data: dict) -> dict:
        result = await self.db.execute(
            select(LegalKnowledge).where(LegalKnowledge.id == article_id)
        )
        article = result.scalar_one_or_none()
        if not article:
            raise HTTPException(status_code=404, detail="知识条目不存在")

        for field, value in data.items():
            if value is not None:
                setattr(article, field, value)

        await self.db.commit()
        await self.db.refresh(article)
        return self._to_dict(article)

    async def delete_article(self, article_id: int) -> dict:
        result = await self.db.execute(
            select(LegalKnowledge).where(LegalKnowledge.id == article_id)
        )
        article = result.scalar_one_or_none()
        if not article:
            raise HTTPException(status_code=404, detail="知识条目不存在")

        await self.db.delete(article)
        await self.db.commit()
        return {"message": "删除成功"}

    async def get_distinct_categories(self) -> list[str]:
        result = await self.db.execute(
            select(LegalKnowledge.category).distinct()
        )
        return [row[0] for row in result.all()]

    async def batch_delete(self, ids: list[int]) -> dict:
        result = await self.db.execute(
            sa_delete(LegalKnowledge).where(LegalKnowledge.id.in_(ids))
        )
        await self.db.commit()
        removed = result.rowcount
        return {
            "success_count": removed,
            "failed_count": len(ids) - removed,
            "message": f"成功删除{removed}条",
        }

    async def batch_import(self, items: list[dict], dry_run: bool = False) -> dict:
        count = 0
        for item in items:
            row = LegalKnowledge(
                knowledge_type=item.get("knowledge_type", "law"),
                title=item.get("title", ""),
                article_number=item.get("article_number"),
                content=item.get("content"),
                summary=item.get("summary"),
                category=item.get("category", "法律"),
                keywords=item.get("keywords"),
                source=item.get("source"),
                source_url=item.get("source_url"),
                source_version=item.get("source_version"),
                effective_date=item.get("effective_date"),
                weight=item.get("weight", 1.0),
                is_active=item.get("is_active", True),
            )
            if not dry_run:
                self.db.add(row)
            count += 1

        if not dry_run:
            await self.db.commit()

        prefix = "预览" if dry_run else ""
        return {
            "success_count": count,
            "failed_count": 0,
            "message": f"{prefix}成功导入{count}条",
        }

    async def vectorize_article(self, article_id: int) -> dict:
        result = await self.db.execute(
            select(LegalKnowledge).where(LegalKnowledge.id == article_id)
        )
        article = result.scalar_one_or_none()
        if not article:
            raise HTTPException(status_code=404, detail="知识条目不存在")

        article.is_vectorized = True
        await self.db.commit()
        return {"message": "向量化成功"}

    async def batch_vectorize(self, ids: list[int]) -> dict:
        result = await self.db.execute(
            sa_update(LegalKnowledge)
            .where(LegalKnowledge.id.in_(ids))
            .where(LegalKnowledge.is_vectorized == False)
            .values(is_vectorized=True)
        )
        await self.db.commit()
        count = result.rowcount
        return {
            "success_count": count,
            "failed_count": len(ids) - count,
            "message": f"成功向量化{count}条",
        }

    async def get_stats(self) -> dict:
        total_result = await self.db.execute(
            select(func.count()).select_from(LegalKnowledge)
        )
        total = total_result.scalar() or 0

        type_result = await self.db.execute(
            select(LegalKnowledge.knowledge_type, func.count())
            .group_by(LegalKnowledge.knowledge_type)
        )
        type_counts = {row[0]: row[1] for row in type_result.all()}

        category_result = await self.db.execute(
            select(LegalKnowledge.category, func.count())
            .group_by(LegalKnowledge.category)
        )
        categories = [
            {"category": row[0], "count": row[1]}
            for row in category_result.all()
        ]

        vectorized_result = await self.db.execute(
            select(func.count()).select_from(LegalKnowledge).where(
                LegalKnowledge.is_vectorized == True
            )
        )
        vectorized_count = vectorized_result.scalar() or 0

        return {
            "total_laws": type_counts.get("law", 0),
            "total_cases": type_counts.get("case", 0),
            "total_regulations": type_counts.get("regulation", 0),
            "total_interpretations": type_counts.get("interpretation", 0),
            "vectorized_count": vectorized_count,
            "categories": categories,
        }
