"""知识库向量化服务

提供知识向量化到 ChromaDB 的功能
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.knowledge import LegalKnowledge

logger = logging.getLogger(__name__)


class KnowledgeVectorizeService:
    """知识向量化服务"""

    def _try_get_ai_assistant(self):
        """尝试获取 AI 助手"""
        try:
            from ..ai_assistant import get_ai_assistant
            return get_ai_assistant()
        except Exception:
            logger.exception("AI助手不可用，无法进行向量化")
            return None

    async def vectorize_knowledge(
        self,
        db: AsyncSession,
        knowledge_id: int
    ) -> bool:
        """将单条知识向量化到ChromaDB"""
        from .core import knowledge_service

        knowledge = await knowledge_service.get_knowledge(db, knowledge_id)
        if not knowledge or knowledge.is_vectorized:
            return False

        try:
            assistant = self._try_get_ai_assistant()
            if assistant is None:
                return False

            kb = assistant.knowledge_base
            kb.initialize()

            if kb.vector_store is None:
                logger.warning("向量数据库未初始化")
                return False

            # 构建文档
            doc: dict[str, object] = {
                "law_name": knowledge.title,
                "article": knowledge.article_number or "",
                "content": knowledge.content,
                "source": knowledge.source or knowledge.category,
                "knowledge_id": int(knowledge.id),
                "source_url": getattr(knowledge, "source_url", None),
                "source_version": getattr(knowledge, "source_version", None),
                "source_hash": getattr(knowledge, "source_hash", None),
                "ingest_batch_id": getattr(knowledge, "ingest_batch_id", None),
            }

            kb.add_law_documents([doc])

            knowledge.is_vectorized = True
            await db.commit()
            return True

        except Exception:
            logger.exception("向量化失败")
            return False

    async def batch_vectorize(
        self,
        db: AsyncSession,
        ids: list[int]
    ) -> tuple[int, int]:
        """批量向量化"""
        success = 0
        failed = 0

        for kid in ids:
            if await self.vectorize_knowledge(db, kid):
                success += 1
            else:
                failed += 1

        return success, failed

    async def sync_all_to_vector_store(
            self, db: AsyncSession) -> tuple[int, int]:
        """同步所有未向量化的知识到向量库"""
        from sqlalchemy import select
        from ...models.knowledge import LegalKnowledge

        result = await db.execute(
            select(LegalKnowledge).where(
                LegalKnowledge.is_active,
                LegalKnowledge.is_vectorized == False
            )
        )
        items = result.scalars().all()

        success = 0
        failed = 0

        for item in items:
            if await self.vectorize_knowledge(db, item.id):
                success += 1
            else:
                failed += 1

        return success, failed


# 单例
knowledge_vectorize_service = KnowledgeVectorizeService()
