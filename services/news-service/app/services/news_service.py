"""新闻服务 - 服务层"""
from typing import List, Optional, Tuple
from datetime import datetime, timezone

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import News, NewsCategory, NewsTag, UserNewsInteraction, NewsTagAssociation


class NewsService:
    """新闻服务"""

    async def get_news_list(
        self,
        session: AsyncSession,
        category_id: int = None,
        tag_id: int = None,
        query: str = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "latest",
    ) -> Tuple[List[News], int]:
        """获取新闻列表"""
        conditions = []
        if category_id:
            conditions.append(News.category_id == category_id)
        if tag_id:
            # Use subquery to find news with the tag
            from sqlalchemy import select as sa_select
            tag_news_query = sa_select(NewsTagAssociation.news_id).where(
                NewsTagAssociation.tag_id == tag_id
            )
            conditions.append(News.id.in_(tag_news_query))
        if query:
            conditions.append(or_(
                News.title.ilike(f"%{query}%"),
                News.summary.ilike(f"%{query}%"),
                News.content.ilike(f"%{query}%"),
            ))

        base_query = select(News).where(*conditions) if conditions else select(News)

        if sort_by == "hot":
            base_query = base_query.order_by(News.view_count.desc())
        else:
            base_query = base_query.order_by(News.published_at.desc())

        # 总数
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        query_obj = base_query.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(query_obj)
        news_list = result.scalars().all()

        return list(news_list), total

    async def get_news_detail(
        self,
        session: AsyncSession,
        news_id: int,
        increment_view: bool = True,
    ) -> Optional[News]:
        """获取新闻详情"""
        query = select(News).where(News.id == news_id)
        result = await session.execute(query)
        news = result.scalar_one_or_none()

        if news and increment_view:
            news.view_count += 1
            news.updated_at = datetime.now(timezone.utc)
            await session.flush()

        return news

    async def get_news_by_category(
        self,
        session: AsyncSession,
        category_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[News], int]:
        """获取分类下的新闻"""
        return await self.get_news_list(
            session,
            category_id=category_id,
            page=page,
            page_size=page_size,
        )

    async def get_news_by_tag(
        self,
        session: AsyncSession,
        tag_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[News], int]:
        """获取标签下的新闻"""
        return await self.get_news_list(
            session,
            tag_id=tag_id,
            page=page,
            page_size=page_size,
        )

    async def search_news(
        self,
        session: AsyncSession,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[News], int]:
        """搜索新闻"""
        return await self.get_news_list(
            session,
            query=query,
            page=page,
            page_size=page_size,
            sort_by="hot",
        )

    async def bookmark_news(
        self,
        session: AsyncSession,
        user_id: int,
        news_id: int,
    ) -> UserNewsInteraction:
        """收藏新闻"""
        interaction = await self._get_or_create_interaction(session, user_id, news_id)
        interaction.is_bookmarked = True
        await session.flush()
        return interaction

    async def unbookmark_news(
        self,
        session: AsyncSession,
        user_id: int,
        news_id: int,
    ) -> bool:
        """取消收藏"""
        interaction = await self._get_or_create_interaction(session, user_id, news_id)
        interaction.is_bookmarked = False
        await session.flush()
        return True

    async def get_user_bookmarks(
        self,
        session: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[News], int]:
        """获取用户收藏的新闻"""
        query = (
            select(News)
            .join(UserNewsInteraction)
            .where(
                UserNewsInteraction.user_id == user_id,
                UserNewsInteraction.is_bookmarked == True,
            )
            .order_by(UserNewsInteraction.interacted_at.desc())
        )

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(query)
        news_list = result.scalars().all()

        return list(news_list), total

    async def _get_or_create_interaction(
        self,
        session: AsyncSession,
        user_id: int,
        news_id: int,
    ) -> UserNewsInteraction:
        """获取或创建用户新闻互动记录"""
        query = select(UserNewsInteraction).where(
            UserNewsInteraction.user_id == user_id,
            UserNewsInteraction.news_id == news_id,
        )
        result = await session.execute(query)
        interaction = result.scalar_one_or_none()

        if not interaction:
            interaction = UserNewsInteraction(
                user_id=user_id,
                news_id=news_id,
            )
            session.add(interaction)
            await session.flush()

        return interaction


news_service = NewsService()
