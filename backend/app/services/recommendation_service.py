"""个性化推荐服务"""
from typing import Any

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lawfirm import Lawyer, LawyerConsultation, LawyerReview
from ..models.forum import Post
from ..models.news import News
from ..services.user_interest_service import user_interest_service


def _generate_lawyer_reason(
        lawyer: Lawyer, interests: list[str], score: float) -> str:
    """生成律师推荐理由"""
    reasons = []

    # 评分理由
    if lawyer.rating >= 4.5:
        reasons.append("评分高")
    elif lawyer.rating >= 4.0:
        reasons.append("评分良好")

    # 经验理由
    if lawyer.experience_years >= 10:
        reasons.append("资深律师")
    elif lawyer.experience_years >= 5:
        reasons.append("经验丰富")

    # 擅长领域匹配
    if lawyer.specialties and interests:
        for interest in interests:
            if interest in lawyer.specialties.lower():
                reasons.append(f"擅长{interest}")
                break

    # 评价数
    if lawyer.review_count >= 50:
        reasons.append("广受好评")
    elif lawyer.review_count >= 10:
        reasons.append("评价良好")

    if reasons:
        return " | ".join(reasons[:2])
    return "为您推荐"


def _generate_post_reason(
        post: Post, interests: list[str], score: float) -> str:
    """生成帖子推荐理由"""
    reasons = []

    # 热度理由
    if post.view_count >= 1000:
        reasons.append("热门帖子")
    elif post.view_count >= 500:
        reasons.append("较多浏览")

    # 点赞理由
    if post.like_count >= 50:
        reasons.append("高赞内容")
    elif post.like_count >= 10:
        reasons.append("受大家喜爱")

    # 兴趣匹配
    if interests:
        for interest in interests:
            if interest in post.title.lower() or interest in (post.content or "").lower():
                reasons.append(f"涉及{interest}")
                break

    if reasons:
        return " | ".join(reasons[:2])
    return "值得关注"


def _generate_news_reason(
        news: News, interests: list[str], score: float) -> str:
    """生成新闻推荐理由"""
    reasons = []

    # 热度理由
    if news.view_count >= 1000:
        reasons.append("热门新闻")
    elif news.view_count >= 500:
        reasons.append("阅读量高")

    # 兴趣匹配
    if interests:
        for interest in interests:
            if interest in news.title.lower() or interest in (news.content or "").lower():
                reasons.append(f"关于{interest}")
                break

    if reasons:
        return " | ".join(reasons[:2])
    return "最新资讯"


class RecommendationService:
    """个性化推荐服务"""

    @staticmethod
    async def recommend_lawyers(
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        推荐律师

        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 返回数量

        Returns:
            推荐律师列表
        """
        # 获取用户兴趣标签
        interests = await user_interest_service.get_user_interest_tags(db, user_id)

        # 查询律师
        query = (
            select(Lawyer)
            .where(Lawyer.is_verified)
            .where(Lawyer.is_active)
            .order_by(desc(Lawyer.rating), desc(Lawyer.review_count))
            .limit(limit * 2)  # 多查询一些，用于后续筛选
        )
        result = await db.execute(query)
        lawyers = list(result.scalars().all())

        # 根据兴趣标签筛选和排序
        scored_lawyers: list[tuple[Lawyer, float]] = []

        for lawyer in lawyers:
            score = 0.0

            # 基础分数：评分和评价数
            score += lawyer.rating * 0.3
            score += min(lawyer.review_count / 100, 1.0) * 0.2

            # 兴趣匹配分数
            if lawyer.specialties and interests:
                specialties_lower = lawyer.specialties.lower()
                for interest in interests:
                    if interest in specialties_lower:
                        score += 0.5

            scored_lawyers.append((lawyer, score))

        # 按分数排序
        scored_lawyers.sort(key=lambda x: x[1], reverse=True)

        # 返回前N个律师
        recommendations = []
        for lawyer, score in scored_lawyers[:limit]:
            recommendations.append({
                "lawyer_id": lawyer.id,
                "name": lawyer.name,
                "avatar": lawyer.avatar,
                "title": lawyer.title,
                "specialties": lawyer.specialties,
                "rating": lawyer.rating,
                "review_count": lawyer.review_count,
                "consultation_fee": lawyer.consultation_fee,
                "score": score,
                "reason": _generate_lawyer_reason(lawyer, interests, score),
            })

        return recommendations

    @staticmethod
    async def recommend_forum_posts(
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        推荐论坛帖子

        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 返回数量

        Returns:
            推荐帖子列表
        """
        # 获取用户兴趣标签
        interests = await user_interest_service.get_user_interest_tags(db, user_id)

        # 查询热门帖子
        query = (
            select(Post)
            .where(Post.is_deleted == False)
            .order_by(desc(Post.view_count), desc(Post.created_at))
            .limit(limit * 2)
        )
        result = await db.execute(query)
        posts = list(result.scalars().all())

        # 根据兴趣标签筛选和排序
        scored_posts: list[tuple[Post, float]] = []

        for post in posts:
            score = 0.0

            # 基础分数：浏览量和点赞数
            score += min(post.view_count / 1000, 1.0) * 0.3
            score += min(post.like_count / 100, 1.0) * 0.2

            # 兴趣匹配分数
            if interests:
                title_lower = post.title.lower()
                content_lower = post.content.lower() if post.content else ""
                for interest in interests:
                    if interest in title_lower or interest in content_lower:
                        score += 0.5

            scored_posts.append((post, score))

        # 按分数排序
        scored_posts.sort(key=lambda x: x[1], reverse=True)

        # 返回前N个帖子
        recommendations = []
        for post, score in scored_posts[:limit]:
            recommendations.append({
                "post_id": post.id,
                "title": post.title,
                "content": post.content[:200] if post.content else "",
                "author_id": post.user_id,
                "view_count": post.view_count,
                "like_count": post.like_count,
                "comment_count": post.comment_count,
                "created_at": post.created_at,
                "score": score,
                "reason": _generate_post_reason(post, interests, score),
            })

        return recommendations

    @staticmethod
    async def recommend_news(
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        推荐新闻

        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 返回数量

        Returns:
            推荐新闻列表
        """
        # 获取用户兴趣标签
        interests = await user_interest_service.get_user_interest_tags(db, user_id)

        # 查询最新新闻
        query = (
            select(News)
            .where(News.is_published)
            .order_by(desc(News.created_at))
            .limit(limit * 2)
        )
        result = await db.execute(query)
        news_list = list(result.scalars().all())

        # 根据兴趣标签筛选和排序
        scored_news: list[tuple[News, float]] = []

        for news in news_list:
            score = 0.0

            # 基础分数：浏览量
            score += min(news.view_count / 1000, 1.0) * 0.3

            # 兴趣匹配分数
            if interests:
                title_lower = news.title.lower()
                content_lower = news.content.lower() if news.content else ""
                for interest in interests:
                    if interest in title_lower or interest in content_lower:
                        score += 0.5

            scored_news.append((news, score))

        # 按分数排序
        scored_news.sort(key=lambda x: x[1], reverse=True)

        # 返回前N个新闻
        recommendations = []
        for news, score in scored_news[:limit]:
            recommendations.append({
                "news_id": news.id,
                "title": news.title,
                "summary": news.summary[:200] if news.summary else "",
                "cover_image": news.cover_image,
                "view_count": news.view_count,
                "created_at": news.created_at,
                "score": score,
                "reason": _generate_news_reason(news, interests, score),
            })

        return recommendations

    @staticmethod
    async def get_personalized_recommendations(
        db: AsyncSession,
        user_id: int,
        lawyer_limit: int = 5,
        post_limit: int = 5,
        news_limit: int = 5,
    ) -> dict[str, Any]:
        """
        获取个性化推荐（综合）

        Args:
            db: 数据库会话
            user_id: 用户ID
            lawyer_limit: 律师推荐数量
            post_limit: 帖子推荐数量
            news_limit: 新闻推荐数量

        Returns:
            综合推荐结果
        """
        # 获取用户兴趣标签
        interests = await user_interest_service.get_user_interest_tags(db, user_id)

        # 获取各类推荐
        lawyers = await RecommendationService.recommend_lawyers(db, user_id, lawyer_limit)
        posts = await RecommendationService.recommend_forum_posts(db, user_id, post_limit)
        news = await RecommendationService.recommend_news(db, user_id, news_limit)

        return {
            "user_id": user_id,
            "interests": interests,
            "lawyers": lawyers,
            "posts": posts,
            "news": news,
        }

    @staticmethod
    async def recommend_similar_users_content(
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        推荐相似用户喜欢的内容

        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 返回数量

        Returns:
            推荐内容列表
        """
        # 获取相似用户
        similar_user_ids = await user_interest_service.get_similar_users(db, user_id, limit=10)

        if not similar_user_ids:
            return []

        # 查询相似用户浏览过的帖子
        from ..models.analytics import UserBehaviorLog

        result = await db.execute(
            select(UserBehaviorLog)
            .where(UserBehaviorLog.user_id.in_(similar_user_ids))
            .where(UserBehaviorLog.resource_type == "forum_post")
            .order_by(desc(UserBehaviorLog.created_at))
            .limit(limit * 2)
        )
        behaviors = list(result.scalars().all())

        # 统计帖子出现次数
        post_counts: dict[int, int] = {}
        for behavior in behaviors:
            if behavior.resource_id:
                post_counts[behavior.resource_id] = post_counts.get(
                    behavior.resource_id, 0) + 1

        # 按出现次数排序
        sorted_posts = sorted(
            post_counts.items(),
            key=lambda x: x[1],
            reverse=True)

        # 获取帖子详情
        recommendations = []
        for post_id, count in sorted_posts[:limit]:
            post_result = await db.execute(
                select(Post).where(Post.id == post_id)
            )
            post = post_result.scalar_one_or_none()
            if post and not post.is_deleted:
                recommendations.append({
                    "post_id": post.id,
                    "title": post.title,
                    "content": post.content[:200] if post.content else "",
                    "view_count": post.view_count,
                    "like_count": post.like_count,
                    "comment_count": post.comment_count,
                    "similar_users_count": count,
                })

        return recommendations


recommendation_service = RecommendationService()
