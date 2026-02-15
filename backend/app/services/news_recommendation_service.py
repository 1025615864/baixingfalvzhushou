"""新闻推荐服务

提供用户行为追踪、兴趣标签计算、个性化推荐等功能
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, cast

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..config import get_settings
from ..models.news import News, NewsViewHistory, NewsFavorite
from ..models.news_ai import NewsAIAnnotation
from ..models.user import User
from ..models.user_profile import UserProfile, UserInterestHistory, UserTagInteraction
from ..services.news_quality_service import news_quality_service, LEGAL_CATEGORIES

logger = logging.getLogger(__name__)


# 默认兴趣标签（基于法律分类）
DEFAULT_INTEREST_TAGS = list(LEGAL_CATEGORIES.keys())


@dataclass
class UserInterestProfile:
    """用户兴趣画像"""
    user_id: int
    interest_tags: dict[str, float]           # 标签 -> 权重
    preferred_content_types: list[str]        # 偏好的内容类型
    recent_behaviors: list[dict]              # 最近行为
    interaction_count: int                    # 总交互次数


@dataclass
class NewsRecommendation:
    """新闻推荐结果"""
    news_id: int
    title: str
    category: str
    score: float                              # 推荐分数
    reason: str                               # 推荐理由
    is_new: bool                              # 是否为新内容
    is_high_quality: bool                     # 是否高质量


class NewsRecommendationService:
    """新闻推荐服务"""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def track_user_behavior(
        self,
        db: AsyncSession,
        user_id: int,
        behavior_type: str,
        content_id: int | None = None,
        content_type: str | None = None,
        content_tags: list[str] | None = None,
        interaction_type: str = "viewed",
        weight: float = 1.0,
    ) -> None:
        """追踪用户行为"""
        try:
            # 1. 记录行为历史
            history = UserInterestHistory(
                user_id=user_id,
                behavior_type=behavior_type,
                content_tags=content_tags or [],
                interaction_type=interaction_type,
                weight=weight,
                content_id=str(content_id) if content_id else None,
                content_type=content_type,
            )
            db.add(history)

            # 2. 更新标签交互统计
            if content_tags:
                for tag in content_tags:
                    tag = tag.strip()
                    if not tag:
                        continue

                    # 查询现有记录
                    res = await db.execute(
                        select(UserTagInteraction).where(
                            and_(
                                UserTagInteraction.user_id == user_id,
                                UserTagInteraction.tag == tag,
                            )
                        )
                    )
                    existing = res.scalar_one_or_none()

                    if existing:
                        existing.interaction_count = cast(
                            # type: ignore[assignment]
                            int, existing.interaction_count) + 1
                        existing.total_weight = float(
                            # type: ignore[assignment]
                            existing.total_weight) + weight
                        # type: ignore[assignment]
                        existing.last_interaction_at = datetime.now()
                    else:
                        new_interaction = UserTagInteraction(
                            user_id=user_id,
                            tag=tag,
                            interaction_count=1,
                            total_weight=weight,
                            last_interaction_at=datetime.now(),
                        )
                        db.add(new_interaction)

            # 3. 更新用户画像
            res = await db.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = res.scalar_one_or_none()

            if profile:
                # 更新兴趣标签权重
                if content_tags:
                    current_weights = cast(
                        dict, profile.interest_weights) or {}
                    for tag in content_tags:
                        tag = tag.strip()
                        if not tag:
                            continue
                        current_weights[tag] = current_weights.get(
                            tag, 0.0) + weight * 0.5
                    # type: ignore[assignment]
                    profile.interest_weights = current_weights

            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("track_user_behavior failed user_id=%s", user_id)

    async def track_news_view(
        self,
        db: AsyncSession,
        user_id: int,
        news_id: int,
    ) -> None:
        """追踪用户浏览新闻"""
        # 1. 记录浏览历史
        res = await db.execute(
            select(NewsViewHistory).where(
                and_(
                    NewsViewHistory.user_id == user_id,
                    NewsViewHistory.news_id == news_id,
                )
            )
        )
        existing = res.scalar_one_or_none()

        if existing:
            existing.viewed_at = datetime.now()
        else:
            view_history = NewsViewHistory(
                user_id=user_id,
                news_id=news_id,
            )
            db.add(view_history)

            # 增加新闻浏览量
            news_res = await db.execute(select(News).where(News.id == news_id))
            news = news_res.scalar_one_or_none()
            if news:
                news.view_count = cast(int, news.view_count) + 1

        # 2. 获取新闻标签
        ann_res = await db.execute(
            select(NewsAIAnnotation).where(NewsAIAnnotation.news_id == news_id)
        )
        annotation = ann_res.scalar_one_or_none()

        tags: list[str] = []
        if annotation:
            keywords_raw = annotation.keywords
            if keywords_raw and isinstance(keywords_raw, str):
                import json
                try:
                    tags = json.loads(keywords_raw)
                except Exception:
                    tags = []

        # 3. 获取法律分类
        news_res = await db.execute(select(News).where(News.id == news_id))
        news = news_res.scalar_one_or_none()
        if news:
            category = str(news.category or "").lower()
            if category and category not in ["general", "unknown"]:
                tags.append(category)

        # 4. 追踪行为
        await self.track_user_behavior(
            db=db,
            user_id=user_id,
            behavior_type="news",
            content_id=news_id,
            content_type="news",
            content_tags=tags,
            interaction_type="viewed",
            weight=1.0,
        )

        await db.commit()

    async def track_news_favorite(
        self,
        db: AsyncSession,
        user_id: int,
        news_id: int,
        is_favorite: bool = True,
    ) -> None:
        """追踪用户收藏新闻"""
        # 1. 获取新闻标签
        ann_res = await db.execute(
            select(NewsAIAnnotation).where(NewsAIAnnotation.news_id == news_id)
        )
        annotation = ann_res.scalar_one_or_none()

        tags: list[str] = []
        if annotation:
            keywords_raw = annotation.keywords
            if keywords_raw and isinstance(keywords_raw, str):
                import json
                try:
                    tags = json.loads(keywords_raw)
                except Exception:
                    tags = []

        # 2. 追踪行为
        await self.track_user_behavior(
            db=db,
            user_id=user_id,
            behavior_type="news",
            content_id=news_id,
            content_type="news",
            content_tags=tags,
            interaction_type="favorited" if is_favorite else "unfavorited",
            weight=3.0 if is_favorite else -1.0,
        )

        await db.commit()

    async def get_user_interest_profile(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> UserInterestProfile:
        """获取用户兴趣画像"""
        # 1. 获取用户标签交互
        res = await db.execute(
            select(UserTagInteraction)
            .where(UserTagInteraction.user_id == user_id)
            .order_by(desc(UserTagInteraction.total_weight))
            .limit(20)
        )
        tag_interactions = list(res.scalars().all())

        interest_tags: dict[str, float] = {}
        for ti in tag_interactions:
            interest_tags[cast(str, ti.tag)] = float(
                cast(float, ti.total_weight))

        # 2. 获取用户画像
        res = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = res.scalar_one_or_none()

        preferred_content_types = []
        if profile:
            pref = profile.preferred_content_types
            if pref is not None and isinstance(pref, list):
                preferred_content_types = cast(list[str], pref)

        # 3. 获取最近行为
        res = await db.execute(
            select(UserInterestHistory)
            .where(UserInterestHistory.user_id == user_id)
            .order_by(desc(UserInterestHistory.created_at))
            .limit(50)
        )
        behaviors = list(res.scalars().all())

        recent_behaviors = []
        for b in behaviors:
            recent_behaviors.append({
                "behavior_type": b.behavior_type,
                "content_tags": b.content_tags or [],
                "interaction_type": b.interaction_type,
                # type: ignore[union-attr]
                "created_at": b.created_at.isoformat() if b.created_at is not None else None,
            })

        # 4. 计算总交互次数
        interaction_count = sum(
            cast(int, ti.interaction_count) for ti in tag_interactions
        )

        return UserInterestProfile(
            user_id=user_id,
            interest_tags=interest_tags,
            preferred_content_types=preferred_content_types,
            recent_behaviors=recent_behaviors,
            interaction_count=interaction_count,
        )

    async def get_recommendations(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
        exclude_viewed: bool = True,
    ) -> list[NewsRecommendation]:
        """获取个性化新闻推荐"""
        # 1. 获取用户兴趣画像
        profile = await self.get_user_interest_profile(db, user_id)

        # 2. 获取用户已浏览的新闻ID
        viewed_ids: set[int] = set()
        if exclude_viewed:
            res = await db.execute(
                select(NewsViewHistory.news_id).where(
                    NewsViewHistory.user_id == user_id
                )
            )
            viewed_ids = {cast(int, row[0]) for row in res.all()}

        # 3. 获取用户收藏的新闻ID（增加权重）
        fav_res = await db.execute(
            select(NewsFavorite.news_id).where(
                NewsFavorite.user_id == user_id
            )
        )
        favorite_ids = {cast(int, row[0]) for row in fav_res.all()}

        # 4. 构建查询（已发布、已审核的新闻）
        where_conditions = [
            News.is_published,
            News.review_status == "approved",
        ]
        if exclude_viewed and viewed_ids:
            where_conditions.append(News.id.not_in(list(viewed_ids)))

        from sqlalchemy import or_
        query = (
            select(News)
            .options(joinedload(News.ai_annotation))
            .where(or_(*where_conditions))
            .order_by(desc(News.published_at), desc(News.view_count))
            .offset(offset)
            .limit(limit * 2)  # 多取一些用于排序
        )

        res = await db.execute(query)
        news_list = list(res.unique().scalars().all())

        # 5. 计算推荐分数
        recommendations: list[NewsRecommendation] = []

        for news in news_list:
            if len(recommendations) >= limit:
                break

            # 基础分数：基于时间和热度
            base_score = 0.0

            # 时间衰减（越新分数越高）
            if news.published_at:
                hours_ago = (
                    datetime.now() - news.published_at).total_seconds() / 3600
                time_score = max(0, 100 - hours_ago * 2)
                base_score += time_score * 0.3
            else:
                base_score += 50

            # 热度分数
            view_count = cast(int, news.view_count or 0)
            base_score += min(view_count * 0.5, 50)

            # 兴趣匹配分数
            interest_score = 0.0
            news_tags: list[str] = []

            # 从AI标注获取关键词
            if news.ai_annotation and news.ai_annotation.keywords:
                keywords_raw = news.ai_annotation.keywords
                if isinstance(keywords_raw, str):
                    import json
                    try:
                        news_tags = json.loads(keywords_raw)
                    except Exception:
                        news_tags = []

            # 匹配用户兴趣标签
            for tag, weight in profile.interest_tags.items():
                if tag in news_tags or tag.lower() in str(news.category or "").lower():
                    interest_score += weight * 2

            # 如果新闻在收藏列表中，增加相关内容的权重
            for fav_id in favorite_ids:
                if fav_id == news.id:
                    interest_score += 10
                    break

            # 质量分数
            quality_score = 0.0
            if news.ai_annotation:
                risk = str(news.ai_annotation.risk_level or "").lower()
                if risk == "safe":
                    quality_score += 20
                elif risk == "warning":
                    quality_score += 10

            # 计算最终分数
            final_score = base_score + interest_score + quality_score

            # 生成推荐理由
            reason = ""
            if interest_score > 5:
                reason = "根据您的兴趣推荐"
            elif base_score > 80:
                reason = "热门新闻"
            elif news.published_at and (datetime.now() - news.published_at).total_seconds() < 86400:
                reason = "最新发布"
            else:
                reason = "您可能感兴趣"

            # 判断是否高质量
            is_high_quality = bool(
                quality_score >= 20 or
                (view_count > 100) or
                (news.ai_annotation and str(
                    news.ai_annotation.risk_level or "").lower() == "safe")
            )

            # 判断是否新内容
            is_new = (
                news.published_at is not None and
                (datetime.now() - news.published_at).total_seconds() < 172800  # 48小时内
            )

            recommendations.append(NewsRecommendation(
                news_id=cast(int, news.id),
                title=str(news.title or ""),
                category=str(news.category or ""),
                score=round(final_score, 2),
                reason=reason,
                is_new=is_new,
                is_high_quality=is_high_quality,
            ))

        # 按分数排序
        recommendations.sort(key=lambda x: x.score, reverse=True)

        return recommendations[:limit]

    async def get_similar_news(
        self,
        db: AsyncSession,
        news_id: int,
        limit: int = 5,
    ) -> list[NewsRecommendation]:
        """获取相似新闻推荐"""
        # 1. 获取当前新闻信息
        res = await db.execute(
            select(News)
            .options(joinedload(News.ai_annotation))
            .where(News.id == news_id)
        )
        news = res.scalar_one_or_none()

        if not news:
            return []

        # 2. 提取关键词
        keywords: list[str] = []
        if news.ai_annotation and news.ai_annotation.keywords:
            keywords_raw = news.ai_annotation.keywords
            if isinstance(keywords_raw, str):
                import json
                try:
                    keywords = json.loads(keywords_raw)
                except Exception:
                    pass

        category = str(news.category or "").lower()

        # 3. 查询相似新闻
        where_conditions = [
            News.is_published,
            News.review_status == "approved",
            News.id != news_id,
        ]

        # 分类匹配
        if category not in ["general", "unknown"]:
            where_conditions.append(News.category == news.category)

        from sqlalchemy import or_
        query = (
            select(News)
            .options(joinedload(News.ai_annotation))
            .where(or_(*where_conditions))
            .order_by(desc(News.view_count))
            .limit(limit * 2)
        )

        res = await db.execute(query)
        news_list = list(res.unique().scalars().all())

        # 4. 基于关键词相似度排序
        similar: list[NewsRecommendation] = []

        for n in news_list:
            if len(similar) >= limit:
                break

            # 计算关键词重叠
            n_keywords: list[str] = []
            if n.ai_annotation and n.ai_annotation.keywords:
                keywords_raw = n.ai_annotation.keywords
                if isinstance(keywords_raw, str):
                    import json
                    try:
                        n_keywords = json.loads(keywords_raw)
                    except Exception:
                        pass

            overlap = len(set(keywords) & set(n_keywords))
            score = overlap * 10 + min(cast(int, n.view_count or 0), 100)

            similar.append(NewsRecommendation(
                news_id=cast(int, n.id),
                title=str(n.title or ""),
                category=str(n.category or ""),
                score=score,
                reason="相似内容",
                is_new=False,
                is_high_quality=False,
            ))

        similar.sort(key=lambda x: x.score, reverse=True)

        return similar[:limit]

    async def get_trending_news(
        self,
        db: AsyncSession,
        limit: int = 10,
        hours: int = 24,
    ) -> list[NewsRecommendation]:
        """获取热门新闻"""
        from datetime import timedelta

        # 获取最近活跃的新闻
        res = await db.execute(
            select(News)
            .options(joinedload(News.ai_annotation))
            .where(
                and_(
                    News.is_published,
                    News.review_status == "approved",
                    News.published_at >= datetime.now() - timedelta(hours=hours),
                )
            )
            .order_by(desc(News.view_count))
            .limit(limit)
        )

        news_list = list(res.unique().scalars().all())

        return [
            NewsRecommendation(
                news_id=cast(int, n.id),
                title=str(n.title or ""),
                category=str(n.category or ""),
                score=cast(int, n.view_count or 0),
                reason="热门新闻",
                is_new=False,
                is_high_quality=False,
            )
            for n in news_list
        ]


news_recommendation_service = NewsRecommendationService()
