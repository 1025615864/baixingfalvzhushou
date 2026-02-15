"""FAQ服务核心

提供 FAQ 知识库的 CRUD 和搜索功能
"""
import json
from typing import Any

from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.faq import FAQ


class FAQService:
    """FAQ知识库服务"""

    @staticmethod
    async def search_faqs(
        db: AsyncSession,
        keyword: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        is_active: bool | None = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[FAQ], int]:
        """
        搜索FAQ

        Args:
            db: 数据库会话
            keyword: 搜索关键词
            category: 分类筛选
            tags: 标签筛选
            is_active: 是否只返回激活的FAQ
            page: 页码
            page_size: 每页数量

        Returns:
            (FAQ列表, 总数)
        """
        query = select(FAQ)
        count_query = select(func.count(FAQ.id))

        # 只返回激活的FAQ
        if is_active is not None:
            query = query.where(FAQ.is_active == is_active)
            count_query = count_query.where(FAQ.is_active == is_active)

        # 分类筛选
        if category:
            query = query.where(FAQ.category == category)
            count_query = count_query.where(FAQ.category == category)

        # 标签筛选
        if tags:
            for tag in tags:
                query = query.where(FAQ.tags.contains(tag))
                count_query = count_query.where(FAQ.tags.contains(tag))

        # 关键词搜索
        if keyword:
            search_filter = or_(
                FAQ.question.contains(keyword),
                FAQ.answer.contains(keyword),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # 排序：优先级高的在前，然后是创建时间
        query = query.order_by(desc(FAQ.priority), desc(FAQ.created_at))

        # 分页
        total_result = await db.execute(count_query)
        total = int(total_result.scalar() or 0)

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        faqs = list(result.scalars().all())

        return faqs, total

    @staticmethod
    async def get_faq_by_id(db: AsyncSession, faq_id: int) -> FAQ | None:
        """
        根据ID获取FAQ

        Args:
            db: 数据库会话
            faq_id: FAQ ID

        Returns:
            FAQ对象或None
        """
        result = await db.execute(
            select(FAQ).where(FAQ.id == faq_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_faq_categories(db: AsyncSession) -> list[str]:
        """
        获取所有FAQ分类

        Args:
            db: 数据库会话

        Returns:
            分类列表
        """
        result = await db.execute(
            select(FAQ.category)
            .where(FAQ.category.isnot(None))
            .where(FAQ.category != "")
            .distinct()
        )
        categories = [str(c[0]) for c in result.all() if c[0]]
        return categories

    @staticmethod
    async def get_popular_faqs(
        db: AsyncSession,
        limit: int = 10,
        category: str | None = None,
    ) -> list[FAQ]:
        """
        获取热门FAQ（按浏览量排序）

        Args:
            db: 数据库会话
            limit: 返回数量
            category: 分类筛选

        Returns:
            FAQ列表
        """
        query = select(FAQ).where(FAQ.is_active)

        if category:
            query = query.where(FAQ.category == category)

        query = query.order_by(
            desc(
                FAQ.view_count), desc(
                FAQ.priority)).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def increment_view_count(db: AsyncSession, faq_id: int) -> bool:
        """
        增加FAQ浏览量

        Args:
            db: 数据库会话
            faq_id: FAQ ID

        Returns:
            是否成功
        """
        faq = await FAQService.get_faq_by_id(db, faq_id)
        if not faq:
            return False

        faq.view_count += 1
        db.add(faq)
        await db.commit()
        return True

    @staticmethod
    async def create_faq(
        db: AsyncSession,
        question: str,
        answer: str,
        category: str | None = None,
        tags: list[str] | None = None,
        priority: int = 0,
        is_active: bool = True,
    ) -> FAQ:
        """
        创建FAQ

        Args:
            db: 数据库会话
            question: 问题
            answer: 答案
            category: 分类
            tags: 标签列表
            priority: 优先级
            is_active: 是否激活

        Returns:
            创建的FAQ对象
        """
        tags_json = json.dumps(tags) if tags else None

        faq = FAQ(
            question=question,
            answer=answer,
            category=category,
            tags=tags_json,
            priority=priority,
            is_active=is_active,
        )
        db.add(faq)
        await db.commit()
        await db.refresh(faq)
        return faq

    @staticmethod
    async def update_faq(
        db: AsyncSession,
        faq_id: int,
        question: str | None = None,
        answer: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        priority: int | None = None,
        is_active: bool | None = None,
    ) -> FAQ | None:
        """
        更新FAQ

        Args:
            db: 数据库会话
            faq_id: FAQ ID
            question: 问题
            answer: 答案
            category: 分类
            tags: 标签列表
            priority: 优先级
            is_active: 是否激活

        Returns:
            更新后的FAQ对象或None
        """
        faq = await FAQService.get_faq_by_id(db, faq_id)
        if not faq:
            return None

        if question is not None:
            faq.question = question
        if answer is not None:
            faq.answer = answer
        if category is not None:
            faq.category = category
        if tags is not None:
            faq.tags = json.dumps(tags) if tags else None
        if priority is not None:
            faq.priority = priority
        if is_active is not None:
            faq.is_active = is_active

        db.add(faq)
        await db.commit()
        await db.refresh(faq)
        return faq

    @staticmethod
    async def delete_faq(db: AsyncSession, faq_id: int) -> bool:
        """
        删除FAQ

        Args:
            db: 数据库会话
            faq_id: FAQ ID

        Returns:
            是否成功
        """
        faq = await FAQService.get_faq_by_id(db, faq_id)
        if not faq:
            return False

        await db.delete(faq)
        await db.commit()
        return True


# 单例实例
faq_service = FAQService()
