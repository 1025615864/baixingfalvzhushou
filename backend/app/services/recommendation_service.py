"""个性化推荐服务 - 增强版

提供基于用户历史行为、兴趣标签、地理位置等多维度的个性化推荐。
使用多级缓存优化性能。
"""
from typing import Any, Optional
from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..models.lawfirm import Lawyer, LawyerConsultation, LawyerReview, LawFirm
from ..models.forum import Post
from ..models.news import News
from ..models.knowledge import LegalKnowledge as KnowledgeArticle
from ..services.user_interest_service import user_interest_service
from ..utils.query_optimizer import (
    apply_lawyer_preload,
    apply_post_preload,
    apply_news_preload,
    track_query,
    get_query_optimizer,
)
from ..utils.cache_config import CachePreset, make_cache_key, cache_metrics_collector
from .multi_level_cache import get_recommendation_cache

logger = logging.getLogger(__name__)


# 兴趣标签到擅长领域的映射
INTEREST_TO_SPECIALTY_MAP = {
    "labor": ["劳动法", "劳动纠纷", "劳动合同", "工伤", "社保"],
    "family": ["婚姻法", "离婚", "继承", "抚养", "家庭"],
    "property": ["房产", "房屋买卖", "拆迁", "物业", "不动产"],
    "contract": ["合同法", "合同纠纷", "合同审查", "违约"],
    "criminal": ["刑事", "辩护", "取保候审", "量刑"],
    "traffic": ["交通", "事故", "理赔", "保险"],
    "consumer": ["消费维权", "欺诈", "退货", "三包"],
    "debt": ["借贷", "债务", "催收", "执行"],
    "business": ["公司法", "股权", "并购", "破产"],
    "ip": ["知识产权", "专利", "商标", "版权"],
}


# 热门内容缓存（用于冷启动）
DEFAULT_HOT_LAWYERS = [
    {"lawyer_id": 1, "name": "张律师", "title": "高级合伙人", "specialties": "劳动纠纷、合同纠纷", "rating": 4.9, "review_count": 256, "city": "北京"},
    {"lawyer_id": 2, "name": "李律师", "title": "资深律师", "specialties": "婚姻家庭、房产纠纷", "rating": 4.8, "review_count": 189, "city": "上海"},
    {"lawyer_id": 3, "name": "王律师", "title": "专业律师", "specialties": "刑事辩护、知识产权", "rating": 4.7, "review_count": 156, "city": "深圳"},
]

DEFAULT_HOT_POSTS = [
    {"post_id": 1, "title": "劳动仲裁全流程分享", "author": "资深用户", "view_count": 5680, "like_count": 256, "category": "labor"},
    {"post_id": 2, "title": "离婚财产分割经验谈", "author": "法律达人", "view_count": 4320, "like_count": 189, "category": "family"},
    {"post_id": 3, "title": "合同审查避坑指南", "author": "专业律师", "view_count": 3890, "like_count": 167, "category": "contract"},
]

DEFAULT_HOT_NEWS = [
    {"news_id": 1, "title": "2024 年劳动法新规解读", "summary": "最新劳动法修改内容详细解读", "view_count": 12580, "category": "labor"},
    {"news_id": 2, "title": "婚姻家庭纠纷案例分析", "summary": "典型婚姻家庭案例法律分析", "view_count": 8960, "category": "family"},
    {"news_id": 3, "title": "合同纠纷预防指南", "summary": "企业合同风险防控要点", "view_count": 7650, "category": "contract"},
]


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
    """个性化推荐服务
    
    使用多级缓存优化推荐结果：
    - L1: 内存缓存 (30 秒)
    - L2: Redis 缓存 (2 分钟)
    - L3: 数据库查询
    """

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
            user_id: 用户 ID
            limit: 返回数量

        Returns:
            推荐律师列表
        """
        cache = get_recommendation_cache()
        cache_key = make_cache_key("recommendation:lawyer", user_id, limit)
        cache_name = f"recommendation:lawyer:{user_id}"
        
        # 尝试从缓存获取
        cache_metrics_collector.start_timer(cache_name)
        cached_result = await cache.get(cache_key)
        
        if cached_result is not None:
            cache_metrics_collector.record_hit(cache_name)
            cache_metrics_collector.stop_timer(cache_name)
            logger.debug(f"推荐律师缓存命中：user_id={user_id}")
            return cached_result  # type: ignore[return-value]
        
        cache_metrics_collector.record_miss(cache_name)
        
        # 获取用户兴趣标签
        interests = await user_interest_service.get_user_interest_tags(db, user_id)

        # 查询律师 - 使用预加载优化
        query = (
            select(Lawyer)
            .where(Lawyer.is_verified)
            .where(Lawyer.is_active)
            .order_by(desc(Lawyer.rating), desc(Lawyer.review_count))
            .limit(limit * 2)  # 多查询一些，用于后续筛选
        )
        # 应用预加载优化 - 使用 joinedload 预加载律师事务所信息
        query = apply_lawyer_preload(query, level="basic")
        
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

        # 返回前 N 个律师
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

        # 写入缓存
        if recommendations:
            await cache.set(cache_key, recommendations, ttl=CachePreset.RECOMMENDATION_LAWYER.l2_ttl)
            cache_metrics_collector.record_write(cache_name)
        
        cache_metrics_collector.stop_timer(cache_name)
        logger.debug(f"推荐律师缓存写入：user_id={user_id}, count={len(recommendations)}")

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
            user_id: 用户 ID
            limit: 返回数量

        Returns:
            推荐帖子列表
        """
        cache = get_recommendation_cache()
        cache_key = make_cache_key("recommendation:post", user_id, limit)
        cache_name = f"recommendation:post:{user_id}"
        
        # 尝试从缓存获取
        cache_metrics_collector.start_timer(cache_name)
        cached_result = await cache.get(cache_key)
        
        if cached_result is not None:
            cache_metrics_collector.record_hit(cache_name)
            cache_metrics_collector.stop_timer(cache_name)
            logger.debug(f"推荐帖子缓存命中：user_id={user_id}")
            return cached_result  # type: ignore[return-value]
        
        cache_metrics_collector.record_miss(cache_name)
        
        # 获取用户兴趣标签
        interests = await user_interest_service.get_user_interest_tags(db, user_id)

        # 查询热门帖子 - 使用预加载优化
        query = (
            select(Post)
            .where(Post.is_deleted == False)
            .order_by(desc(Post.view_count), desc(Post.created_at))
            .limit(limit * 2)
        )
        # 应用预加载优化 - 使用 joinedload 预加载作者信息
        query = apply_post_preload(query, level="basic")
        
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

        # 返回前 N 个帖子
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

        # 写入缓存
        if recommendations:
            await cache.set(cache_key, recommendations, ttl=CachePreset.RECOMMENDATION_POST.l2_ttl)
            cache_metrics_collector.record_write(cache_name)
        
        cache_metrics_collector.stop_timer(cache_name)
        logger.debug(f"推荐帖子缓存写入：user_id={user_id}, count={len(recommendations)}")

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
            user_id: 用户 ID
            limit: 返回数量

        Returns:
            推荐新闻列表
        """
        cache = get_recommendation_cache()
        cache_key = make_cache_key("recommendation:news", user_id, limit)
        cache_name = f"recommendation:news:{user_id}"
        
        # 尝试从缓存获取
        cache_metrics_collector.start_timer(cache_name)
        cached_result = await cache.get(cache_key)
        
        if cached_result is not None:
            cache_metrics_collector.record_hit(cache_name)
            cache_metrics_collector.stop_timer(cache_name)
            logger.debug(f"推荐新闻缓存命中：user_id={user_id}")
            return cached_result  # type: ignore[return-value]
        
        cache_metrics_collector.record_miss(cache_name)
        
        # 获取用户兴趣标签
        interests = await user_interest_service.get_user_interest_tags(db, user_id)

        # 查询最新新闻 - 使用预加载优化
        query = (
            select(News)
            .where(News.is_published)
            .order_by(desc(News.created_at))
            .limit(limit * 2)
        )
        # 应用预加载优化 - 使用 selectinload 预加载 AI 标注信息
        query = apply_news_preload(query, level="basic")
        
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

        # 返回前 N 个新闻
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

        # 写入缓存
        if recommendations:
            await cache.set(cache_key, recommendations, ttl=CachePreset.RECOMMENDATION_NEWS.l2_ttl)
            cache_metrics_collector.record_write(cache_name)
        
        cache_metrics_collector.stop_timer(cache_name)
        logger.debug(f"推荐新闻缓存写入：user_id={user_id}, count={len(recommendations)}")

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
            user_id: 用户 ID
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
            user_id: 用户 ID
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

    @staticmethod
    async def recommend_lawyers_by_consultation_history(
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        基于用户咨询历史推荐相似领域律师
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            limit: 返回数量
            
        Returns:
            推荐的律师列表
        """
        # 获取用户历史咨询记录
        result = await db.execute(
            select(LawyerConsultation)
            .where(LawyerConsultation.user_id == user_id)
            .order_by(desc(LawyerConsultation.created_at))
            .limit(20)
        )
        consultations = list(result.scalars().all())
        
        if not consultations:
            # 无咨询记录，返回热门律师
            return await RecommendationService.recommend_lawyers(db, user_id, limit)
        
        # 统计用户咨询过的领域
        category_counts: dict[str, int] = {}
        for consultation in consultations:
            if consultation.category:
                category_counts[consultation.category] = category_counts.get(
                    consultation.category, 0) + 1
        
        # 找出最常咨询的领域
        top_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:3]
        
        # 查询这些领域的律师
        recommendations = []
        for category, _ in top_categories:
            query = (
                select(Lawyer)
                .where(Lawyer.is_verified)
                .where(Lawyer.is_active)
                .order_by(desc(Lawyer.rating), desc(Lawyer.review_count))
                .limit(limit)
            )
            result = await db.execute(query)
            lawyers = list(result.scalars().all())
            
            for lawyer in lawyers:
                # 检查是否匹配用户关注的领域
                if lawyer.specialties and category.lower() in lawyer.specialties.lower():
                    recommendations.append({
                        "lawyer_id": lawyer.id,
                        "name": lawyer.name,
                        "avatar": lawyer.avatar,
                        "title": lawyer.title,
                        "specialties": lawyer.specialties,
                        "rating": lawyer.rating,
                        "review_count": lawyer.review_count,
                        "consultation_fee": lawyer.consultation_fee,
                        "match_reason": f"您咨询过的{category}领域专家",
                        "score": lawyer.rating * 0.3 + min(lawyer.review_count / 100, 1.0) * 0.2,
                    })
        
        # 去重并按分数排序
        seen = set()
        unique_recommendations = []
        for lawyer in recommendations:
            if lawyer["lawyer_id"] not in seen:
                seen.add(lawyer["lawyer_id"])
                unique_recommendations.append(lawyer)
        
        unique_recommendations.sort(key=lambda x: x["score"], reverse=True)
        return unique_recommendations[:limit]

    @staticmethod
    async def recommend_lawyers_by_location(
        db: AsyncSession,
        user_id: int,
        city: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        基于地理位置推荐附近律师
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            city: 用户所在城市（可选）
            limit: 返回数量
            
        Returns:
            推荐的律师列表
        """
        if not city:
            return DEFAULT_HOT_LAWYERS[:limit]
        
        # 查询指定城市的律师
        query = (
            select(Lawyer)
            .where(Lawyer.is_verified)
            .where(Lawyer.is_active)
            .order_by(desc(Lawyer.rating), desc(Lawyer.review_count))
            .limit(limit * 2)
        )
        result = await db.execute(query)
        lawyers = list(result.scalars().all())
        
        # 筛选或返回默认
        if not lawyers:
            return DEFAULT_HOT_LAWYERS[:limit]
        
        # 返回本地律师
        recommendations = []
        for lawyer in lawyers[:limit]:
            recommendations.append({
                "lawyer_id": lawyer.id,
                "name": lawyer.name,
                "avatar": lawyer.avatar,
                "title": lawyer.title,
                "specialties": lawyer.specialties,
                "rating": lawyer.rating,
                "review_count": lawyer.review_count,
                "consultation_fee": lawyer.consultation_fee,
                "location": city,
                "match_reason": f"本地{city}律师",
            })
        
        return recommendations

    @staticmethod
    async def recommend_knowledge_by_interests(
        db: AsyncSession,
        user_id: int,
        interests: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        基于兴趣推荐法律知识文章
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            interests: 兴趣标签列表（可选）
            limit: 返回数量
            
        Returns:
            推荐的知識文章列表
        """
        # 如果没有提供兴趣标签，从服务获取
        if not interests:
            interests = await user_interest_service.get_user_interest_tags(db, user_id)
        
        # 查询知识库文章
        query = (
            select(KnowledgeArticle)
            .where(KnowledgeArticle.is_active == True)  # noqa: E712
            .order_by(desc(KnowledgeArticle.weight), desc(KnowledgeArticle.created_at))
            .limit(limit * 2)
        )
        
        try:
            result = await db.execute(query)
            articles = list(result.scalars().all())
        except Exception:
            # 如果表不存在或查询失败，返回默认内容
            articles = []
        
        if not articles:
            return [
                {"knowledge_id": 1, "title": "劳动合同法详解", "category": "劳动法", "view_count": 15000},
                {"knowledge_id": 2, "title": "婚姻家庭法律常识", "category": "婚姻法", "view_count": 12000},
                {"knowledge_id": 3, "title": "合同签订与履行指南", "category": "合同法", "view_count": 9800},
            ][:limit]
        
        # 根据兴趣标签筛选
        recommendations = []
        for article in articles:
            score = 0.0
            
            # 基础分数：权重
            score += min(article.weight / 10, 1.0) * 0.3
            
            # 兴趣匹配分数
            if interests and article.title:
                title_lower = article.title.lower()
                for interest in interests:
                    if interest in title_lower:
                        score += 0.5
                        break
            
            recommendations.append({
                "knowledge_id": article.id,
                "title": article.title,
                "category": getattr(article, "category", "法律知识"),
                "summary": (article.summary or "")[:100] if article.summary else "",
                "weight": article.weight,
                "score": score,
            })
        
        # 按分数排序
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]


recommendation_service = RecommendationService()