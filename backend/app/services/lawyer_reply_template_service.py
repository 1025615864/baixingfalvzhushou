"""律师快捷回复模板服务"""
from typing import Any
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lawfirm import LawyerReplyTemplate


class LawyerReplyTemplateService:
    """律师快捷回复模板服务"""

    @staticmethod
    async def create(
        db: AsyncSession,
        lawyer_id: int,
        title: str,
        content: str,
        category: str | None = None,
        is_active: bool = True,
    ) -> LawyerReplyTemplate:
        """
        创建律师快捷回复模板

        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            title: 模板标题
            content: 模板内容
            category: 分类
            is_active: 是否启用

        Returns:
            创建的模板对象
        """
        template = LawyerReplyTemplate(
            lawyer_id=lawyer_id,
            title=title,
            content=content,
            category=category,
            is_active=is_active,
            use_count=0,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        template_id: int,
        lawyer_id: int | None = None,
    ) -> LawyerReplyTemplate | None:
        """
        根据ID获取模板

        Args:
            db: 数据库会话
            template_id: 模板ID
            lawyer_id: 律师ID（可选，用于权限验证）

        Returns:
            模板对象或None
        """
        query = select(LawyerReplyTemplate).where(
            LawyerReplyTemplate.id == template_id)
        if lawyer_id is not None:
            query = query.where(LawyerReplyTemplate.lawyer_id == lawyer_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession,
        lawyer_id: int,
        category: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LawyerReplyTemplate], int]:
        """
        获取律师的模板列表

        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            category: 分类筛选
            is_active: 是否启用筛选
            page: 页码
            page_size: 每页数量

        Returns:
            (模板列表, 总数)
        """
        query = select(LawyerReplyTemplate).where(
            LawyerReplyTemplate.lawyer_id == lawyer_id)
        count_query = select(func.count(LawyerReplyTemplate.id)).where(
            LawyerReplyTemplate.lawyer_id == lawyer_id
        )

        if category is not None:
            query = query.where(LawyerReplyTemplate.category == category)
            count_query = count_query.where(
                LawyerReplyTemplate.category == category)

        if is_active is not None:
            query = query.where(LawyerReplyTemplate.is_active == is_active)
            count_query = count_query.where(
                LawyerReplyTemplate.is_active == is_active)

        query = query.order_by(
            desc(
                LawyerReplyTemplate.use_count),
            LawyerReplyTemplate.created_at)
        query = query.offset((page - 1) * page_size).limit(page_size)

        templates = (await db.execute(query)).scalars().all()
        total = int((await db.execute(count_query)).scalar() or 0)

        return list(templates), total

    @staticmethod
    async def update(
        db: AsyncSession,
        template_id: int,
        lawyer_id: int,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> LawyerReplyTemplate | None:
        """
        更新模板

        Args:
            db: 数据库会话
            template_id: 模板ID
            lawyer_id: 律师ID
            title: 模板标题
            content: 模板内容
            category: 分类
            is_active: 是否启用

        Returns:
            更新后的模板对象或None
        """
        template = await LawyerReplyTemplateService.get_by_id(db, template_id, lawyer_id)
        if not template:
            return None

        if title is not None:
            template.title = title
        if content is not None:
            template.content = content
        if category is not None:
            template.category = category
        if is_active is not None:
            template.is_active = is_active

        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def delete(
        db: AsyncSession,
        template_id: int,
        lawyer_id: int,
    ) -> bool:
        """
        删除模板

        Args:
            db: 数据库会话
            template_id: 模板ID
            lawyer_id: 律师ID

        Returns:
            是否删除成功
        """
        template = await LawyerReplyTemplateService.get_by_id(db, template_id, lawyer_id)
        if not template:
            return False

        await db.delete(template)
        await db.commit()
        return True

    @staticmethod
    async def increment_use_count(
        db: AsyncSession,
        template_id: int,
        lawyer_id: int | None = None,
    ) -> bool:
        """
        增加模板使用次数

        Args:
            db: 数据库会话
            template_id: 模板ID
            lawyer_id: 律师ID（可选，用于权限验证）

        Returns:
            是否更新成功
        """
        query = select(LawyerReplyTemplate).where(
            LawyerReplyTemplate.id == template_id)
        if lawyer_id is not None:
            query = query.where(LawyerReplyTemplate.lawyer_id == lawyer_id)

        result = await db.execute(query)
        template = result.scalar_one_or_none()
        if not template:
            return False

        template.use_count += 1
        db.add(template)
        await db.commit()
        return True

    @staticmethod
    async def get_categories(
        db: AsyncSession,
        lawyer_id: int,
    ) -> list[str]:
        """
        获取律师的所有分类

        Args:
            db: 数据库会话
            lawyer_id: 律师ID

        Returns:
            分类列表
        """
        result = await db.execute(
            select(LawyerReplyTemplate.category)
            .where(
                and_(
                    LawyerReplyTemplate.lawyer_id == lawyer_id,
                    LawyerReplyTemplate.category.isnot(None),
                )
            )
            .distinct()
        )
        categories = [row[0] for row in result.all() if row[0]]
        return categories
