"""知识库服务核心

提供法律知识 CRUD、统计、分类管理
"""
import hashlib
import json
import logging
import uuid
from typing import cast

from sqlalchemy import select, func, delete, CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.knowledge import LegalKnowledge, KnowledgeType
from ...schemas.knowledge import (
    LegalKnowledgeCreate,
    LegalKnowledgeUpdate,
    KnowledgeCategoryCount,
    KnowledgeStats,
)

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库服务"""

    def _compute_source_hash(
        self,
        *,
        knowledge_type: str,
        title: str,
        article_number: str | None,
        content: str,
        source_url: str | None,
        source_version: str | None,
    ) -> str:
        raw = "|".join(
            [
                str(knowledge_type or "").strip(),
                str(title or "").strip(),
                str(article_number or "").strip(),
                str(content or "").strip(),
                str(source_url or "").strip(),
                str(source_version or "").strip(),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # === 法律知识 CRUD ===

    async def create_knowledge(
        self,
        db: AsyncSession,
        data: LegalKnowledgeCreate
    ) -> LegalKnowledge:
        """创建法律知识"""
        source_hash = (
            str(getattr(data, "source_hash", "") or "").strip()
            or self._compute_source_hash(
                knowledge_type=data.knowledge_type.value,
                title=str(data.title),
                article_number=data.article_number,
                content=str(data.content),
                source_url=getattr(data, "source_url", None),
                source_version=getattr(data, "source_version", None),
            )
        )
        knowledge = LegalKnowledge(
            knowledge_type=data.knowledge_type.value,
            title=data.title,
            article_number=data.article_number,
            content=data.content,
            summary=data.summary,
            category=data.category,
            keywords=data.keywords,
            source=data.source,
            source_url=getattr(data, "source_url", None),
            source_version=getattr(data, "source_version", None),
            source_hash=source_hash,
            ingest_batch_id=getattr(data, "ingest_batch_id", None),
            effective_date=data.effective_date,
            weight=data.weight,
            is_active=data.is_active,
        )
        db.add(knowledge)
        await db.commit()
        await db.refresh(knowledge)
        return knowledge

    async def get_knowledge(
        self,
        db: AsyncSession,
        knowledge_id: int
    ) -> LegalKnowledge | None:
        """获取单条法律知识"""
        result = await db.execute(
            select(LegalKnowledge).where(LegalKnowledge.id == knowledge_id)
        )
        return result.scalar_one_or_none()

    async def list_knowledge(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        knowledge_type: str | None = None,
        category: str | None = None,
        keyword: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[LegalKnowledge], int]:
        """获取法律知识列表"""
        query = select(LegalKnowledge)
        count_query = select(func.count(LegalKnowledge.id))

        # 过滤条件
        if knowledge_type:
            query = query.where(
                LegalKnowledge.knowledge_type == knowledge_type)
            count_query = count_query.where(
                LegalKnowledge.knowledge_type == knowledge_type)

        if category:
            query = query.where(LegalKnowledge.category == category)
            count_query = count_query.where(
                LegalKnowledge.category == category)

        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.where(
                (LegalKnowledge.title.ilike(search_pattern)) |
                (LegalKnowledge.content.ilike(search_pattern)) |
                (LegalKnowledge.keywords.ilike(search_pattern))
            )
            count_query = count_query.where(
                (LegalKnowledge.title.ilike(search_pattern)) |
                (LegalKnowledge.content.ilike(search_pattern)) |
                (LegalKnowledge.keywords.ilike(search_pattern))
            )

        if is_active is not None:
            query = query.where(LegalKnowledge.is_active == is_active)
            count_query = count_query.where(
                LegalKnowledge.is_active == is_active)

        # 排序和分页
        query = query.order_by(
            LegalKnowledge.weight.desc(),
            LegalKnowledge.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        items = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return items, total

    async def update_knowledge(
        self,
        db: AsyncSession,
        knowledge_id: int,
        data: LegalKnowledgeUpdate
    ) -> LegalKnowledge | None:
        """更新法律知识"""
        knowledge = await self.get_knowledge(db, knowledge_id)
        if not knowledge:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "knowledge_type" in update_data and update_data["knowledge_type"]:
            update_data["knowledge_type"] = update_data["knowledge_type"].value

        for key, value in update_data.items():
            setattr(knowledge, key, value)

        # 内容变更时需要重新向量化
        if "content" in update_data or "title" in update_data:
            knowledge.is_vectorized = False

        await db.commit()
        await db.refresh(knowledge)
        return knowledge

    async def delete_knowledge(
        self,
        db: AsyncSession,
        knowledge_id: int
    ) -> bool:
        """删除法律知识"""
        knowledge = await self.get_knowledge(db, knowledge_id)
        if not knowledge:
            return False

        await db.delete(knowledge)
        await db.commit()
        return True

    async def batch_delete_knowledge(
        self,
        db: AsyncSession,
        ids: list[int]
    ) -> tuple[int, int]:
        """批量删除法律知识"""
        cursor_result = await db.execute(
            delete(LegalKnowledge).where(LegalKnowledge.id.in_(ids))
        )
        await db.commit()
        deleted = cast(CursorResult[tuple[()]], cursor_result).rowcount or 0
        return deleted, len(ids) - deleted

    async def batch_import_knowledge(
        self,
        db: AsyncSession,
        items: list[LegalKnowledgeCreate],
    ) -> tuple[int, int]:
        """批量导入法律知识"""
        from .vectorize import knowledge_vectorize_service

        batch_id = str(uuid.uuid4())
        success = 0
        failed = 0

        for item in items:
            try:
                kt = item.knowledge_type.value
                title = str(item.title).strip()
                article_number = str(
                    item.article_number).strip() if item.article_number else None

                existing_res = await db.execute(
                    select(LegalKnowledge).where(
                        LegalKnowledge.knowledge_type == kt,
                        LegalKnowledge.title == title,
                        LegalKnowledge.article_number == article_number,
                    )
                )
                existing = existing_res.scalar_one_or_none()

                if existing is None:
                    item_source_hash = (
                        str(getattr(item, "source_hash", "") or "").strip()
                        or self._compute_source_hash(
                            knowledge_type=kt,
                            title=title,
                            article_number=article_number,
                            content=str(item.content),
                            source_url=getattr(item, "source_url", None),
                            source_version=getattr(
                                item, "source_version", None),
                        )
                    )
                    knowledge = LegalKnowledge(
                        knowledge_type=kt,
                        title=title,
                        article_number=article_number,
                        content=item.content,
                        summary=item.summary,
                        category=item.category,
                        keywords=item.keywords,
                        source=item.source,
                        source_url=getattr(item, "source_url", None),
                        source_version=getattr(item, "source_version", None),
                        source_hash=item_source_hash,
                        ingest_batch_id=(
                            getattr(
                                item,
                                "ingest_batch_id",
                                None) or batch_id),
                        effective_date=item.effective_date,
                        weight=item.weight,
                        is_active=item.is_active,
                    )
                    db.add(knowledge)
                else:
                    existing.content = item.content
                    existing.summary = item.summary
                    existing.category = item.category
                    existing.keywords = item.keywords
                    existing.source = item.source
                    existing.source_url = getattr(item, "source_url", None)
                    existing.source_version = getattr(
                        item, "source_version", None)
                    existing.source_hash = (
                        str(getattr(item, "source_hash", "") or "").strip()
                        or self._compute_source_hash(
                            knowledge_type=kt,
                            title=title,
                            article_number=article_number,
                            content=str(item.content),
                            source_url=getattr(item, "source_url", None),
                            source_version=getattr(
                                item, "source_version", None),
                        )
                    )
                    existing.ingest_batch_id = getattr(
                        item, "ingest_batch_id", None) or batch_id
                    existing.effective_date = item.effective_date
                    existing.weight = item.weight
                    existing.is_active = item.is_active
                    existing.is_vectorized = False
                    db.add(existing)

                await db.commit()
                success += 1
            except Exception:
                logger.exception("批量导入失败：%s", getattr(item, "title", ""))
                await db.rollback()
                failed += 1

        return success, failed

    # === 统计 ===

    async def get_stats(self, db: AsyncSession) -> KnowledgeStats:
        """获取知识库统计"""
        # 各类型统计
        type_counts: dict[str, int] = {}
        for kt in KnowledgeType:
            result = await db.execute(
                select(func.count(LegalKnowledge.id)).where(
                    LegalKnowledge.knowledge_type == kt.value
                )
            )
            type_counts[kt.value] = result.scalar() or 0

        # 已向量化数量
        vectorized_result = await db.execute(
            select(func.count(LegalKnowledge.id)).where(
                LegalKnowledge.is_vectorized
            )
        )
        vectorized_count = vectorized_result.scalar() or 0

        # 分类统计
        category_result = await db.execute(
            select(
                LegalKnowledge.category,
                func.count(LegalKnowledge.id).label("count")
            ).group_by(LegalKnowledge.category)
        )

        categories = [
            KnowledgeCategoryCount(
                category=str(
                    row[0] or ""), count=int(
                    row[1] or 0))
            for row in category_result.all()
        ]

        return KnowledgeStats(
            total_laws=type_counts.get("law", 0),
            total_cases=type_counts.get("case", 0),
            total_regulations=type_counts.get("regulation", 0),
            total_interpretations=type_counts.get("interpretation", 0),
            vectorized_count=vectorized_count,
            categories=categories,
        )

    # === 分类管理 ===

    async def get_categories(self, db: AsyncSession) -> list[str]:
        """获取所有分类"""
        result = await db.execute(
            select(LegalKnowledge.category).distinct()
        )
        return [row[0] for row in result.all()]

    async def get_categories_with_count(
            self, db: AsyncSession) -> dict[str, int]:
        """获取知识分类统计"""
        result = await db.execute(
            select(
                LegalKnowledge.category,
                func.count(LegalKnowledge.id).label("count")
            ).group_by(LegalKnowledge.category)
        )
        return {str(row[0] or "未分类"): int(row[1] or 0) for row in result.all()}

    async def sync_all_to_vector_store(
            self, db: AsyncSession) -> tuple[int, int]:
        """同步所有未向量化的知识到向量库"""
        from .vectorize import knowledge_vectorize_service
        return await knowledge_vectorize_service.sync_all_to_vector_store(db)

    async def batch_vectorize(self, db: AsyncSession,
                              ids: list[int]) -> tuple[int, int]:
        """批量向量化"""
        from .vectorize import knowledge_vectorize_service
        return await knowledge_vectorize_service.batch_vectorize(db, ids)

    async def vectorize_knowledge(
            self, db: AsyncSession, knowledge_id: int) -> bool:
        """向量化单条知识"""
        from .vectorize import knowledge_vectorize_service
        return await knowledge_vectorize_service.vectorize_knowledge(db, knowledge_id)

    # === 模板管理 ===

    async def list_templates(
        self,
        db: AsyncSession,
        category: str | None = None,
        is_active: bool | None = True
    ) -> list:
        """获取咨询模板列表（兼容接口）"""
        from .templates import knowledge_template_service
        return await knowledge_template_service.list_templates(db, category, is_active)

    async def get_template(self, db: AsyncSession, template_id: int):
        """获取单个咨询模板"""
        from .templates import knowledge_template_service
        return await knowledge_template_service.get_template(db, template_id)

    async def create_template(self, db: AsyncSession, data):
        """创建咨询模板"""
        from .templates import knowledge_template_service
        return await knowledge_template_service.create_template(db, data)

    async def update_template(self, db: AsyncSession, template_id: int, data):
        """更新咨询模板"""
        from .templates import knowledge_template_service
        return await knowledge_template_service.update_template(db, template_id, data)

    async def delete_template(self, db: AsyncSession,
                              template_id: int) -> bool:
        """删除咨询模板"""
        from .templates import knowledge_template_service
        return await knowledge_template_service.delete_template(db, template_id)

    def parse_template_questions(self, template):
        """解析模板问题列表"""
        from .templates import knowledge_template_service
        return knowledge_template_service.parse_template_questions(template)


# 单例
_knowledge_service: KnowledgeService | None = None


def get_knowledge_service() -> KnowledgeService:
    """获取知识库服务实例"""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service


knowledge_service = get_knowledge_service()
