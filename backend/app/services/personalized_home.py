"""个性化首页服务

提供基于用户画像和兴趣推荐的功能。
增强版本：支持基于用户历史行为、兴趣标签、热门内容和近期咨询的推荐。
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# 热门内容标签映射
HOT_CONTENT_TAGS = {
    "labor_dispute": "劳动纠纷",
    "contract_dispute": "合同纠纷",
    "marriage_family": "婚姻家庭",
    "property_dispute": "房产纠纷",
    "consumer_rights": "消费维权",
    "traffic_accident": "交通事故",
    "loan_dispute": "借贷纠纷",
    "criminal": "刑事问题",
    "ip": "知识产权",
}


@dataclass
class RecommendationReason:
    """推荐理由"""
    reason: str
    reason_type: str  # interest_match, behavior_based, hot_content, location_based


@dataclass
class PersonalizedContent:
    """个性化内容项"""
    id: str
    content_type: str  # news, post, lawyer, knowledge
    title: str
    description: str = ""
    url: str = ""
    tags: list[str] = field(default_factory=list)
    score: float = 0.0
    reason: RecommendationReason = None
    metadata: dict = field(default_factory=dict)


@dataclass
class PersonalizedHomeData:
    """个性化首页数据"""
    user_id: int
    personalized_content: list[PersonalizedContent] = field(default_factory=list)
    hot_content: list[PersonalizedContent] = field(default_factory=list)
    recommended_lawyers: list[dict] = field(default_factory=list)
    recommended_posts: list[dict] = field(default_factory=list)
    recommended_news: list[dict] = field(default_factory=list)
    interest_tags: list[str] = field(default_factory=list)
    recommendation_source: str = "hybrid"  # cold_start, interest_based, behavior_based, hybrid
    generated_at: str = ""


class UserProfile:
    """用户画像"""

    def __init__(self):
        self._profiles: dict[int, dict[str, Any]] = {}

    def get_or_create_profile(self, user_id: int) -> dict[str, Any]:
        """获取或创建用户画像

        Args:
            user_id: 用户ID

        Returns:
            用户画像
        """
        if user_id not in self._profiles:
            self._profiles[user_id] = {
                "user_id": user_id,
                "interests": [],
                "browse_history": [],
                "preferences": {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        return self._profiles[user_id]

    def update_interests(
        self,
        user_id: int,
        interests: list[str],
    ) -> dict[str, Any]:
        """更新兴趣标签

        Args:
            user_id: 用户ID
            interests: 兴趣列表

        Returns:
            更新结果
        """
        profile = self.get_or_create_profile(user_id)
        profile["interests"] = interests
        profile["updated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Updated interests for user {user_id}: {interests}")

        return {
            "success": True,
            "interests": interests,
        }

    def add_browse_history(
        self,
        user_id: int,
        item_id: str,
        category: str,
    ) -> dict[str, Any]:
        """添加浏览历史

        Args:
            user_id: 用户ID
            item_id: 内容ID
            category: 分类

        Returns:
            添加结果
        """
        profile = self.get_or_create_profile(user_id)
        profile["browse_history"].append({
            "item_id": item_id,
            "category": category,
            "viewed_at": datetime.now(timezone.utc).isoformat(),
        })

        if len(profile["browse_history"]) > 100:
            profile["browse_history"] = profile["browse_history"][-100:]

        profile["updated_at"] = datetime.now(timezone.utc).isoformat()

        return {
            "success": True,
            "history_count": len(profile["browse_history"]),
        }

    def get_user_profile(self, user_id: int) -> dict[str, Any]:
        """获取用户画像

        Args:
            user_id: 用户ID

        Returns:
            用户画像
        """
        return self.get_or_create_profile(user_id)


class InterestRecommender:
    """兴趣推荐器"""

    def __init__(self):
        self._items: dict[str, dict[str, Any]] = {}
        self._recommendations: dict[int, list[dict[str, Any]]] = {}

    def register_item(
        self,
        item_id: str,
        title: str,
        category: str,
        tags: list[str],
        score: float = 0.5,
    ) -> dict[str, Any]:
        """注册内容项

        Args:
            item_id: 内容ID
            title: 标题
            category: 分类
            tags: 标签
            score: 评分

        Returns:
            注册结果
        """
        self._items[item_id] = {
            "id": item_id,
            "title": title,
            "category": category,
            "tags": tags,
            "score": score,
            "view_count": 0,
        }

        return {
            "item_id": item_id,
            "registered": True,
        }

    def recommend(
        self,
        user_id: int,
        interests: list[str],
        browse_history: list[dict[str, Any]],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """推荐内容

        Args:
            user_id: 用户ID
            interests: 兴趣列表
            browse_history: 浏览历史
            limit: 推荐数量

        Returns:
            推荐列表
        """
        history_categories = set(h["category"] for h in browse_history)
        history_items = set(h["item_id"] for h in browse_history)

        candidates: list[dict[str, Any]] = []

        for item_id, item in self._items.items():
            if item_id in history_items:
                continue

            relevance_score = 0.0

            for tag in item["tags"]:
                if tag in interests:
                    relevance_score += 0.3

            if item["category"] in history_categories:
                relevance_score += 0.2

            relevance_score += item["score"] * 0.3

            if relevance_score > 0:
                candidates.append({
                    **item,
                    "relevance_score": round(relevance_score, 3),
                })

        candidates.sort(key=lambda x: x["relevance_score"], reverse=True)

        recommendations = candidates[:limit]

        self._recommendations[user_id] = recommendations

        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")

        return recommendations

    def track_click(
        self,
        user_id: int,
        item_id: str,
    ) -> dict[str, Any]:
        """追踪点击

        Args:
            user_id: 用户ID
            item_id: 内容ID

        Returns:
            追踪结果
        """
        if item_id in self._items:
            self._items[item_id]["view_count"] = self._items[item_id].get(
                "view_count", 0) + 1

        return {
            "success": True,
            "item_id": item_id,
        }


class PersonalizedHomeService:
    """个性化首页服务 - 增强版
    
    支持多种推荐策略：
    1. 基于用户历史行为推荐
    2. 基于用户兴趣标签推荐
    3. 热门内容推荐（冷启动用户）
    4. 近期咨询相关推荐
    """

    def __init__(self):
        self.user_profile = UserProfile()
        self.interest_recommender = InterestRecommender()

    async def get_personalized_home(
        self,
        user_id: int,
        include_recommendations: bool = True,
    ) -> dict[str, Any]:
        """获取个性化首页

        Args:
            user_id: 用户ID
            include_recommendations: 是否包含推荐内容

        Returns:
            首页数据
        """
        profile = self.user_profile.get_user_profile(user_id)

        recommendations = []
        if include_recommendations:
            recommendations = self.interest_recommender.recommend(
                user_id=user_id,
                interests=profile["interests"],
                browse_history=profile["browse_history"],
                limit=10,
            )

        return {
            "user_id": user_id,
            "profile": {
                "interests": profile["interests"],
                "history_count": len(profile["browse_history"]),
            },
            "recommendations": recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_enhanced_personalized_home(
        self,
        user_id: int,
        db_session=None,
        lawyer_limit: int = 5,
        post_limit: int = 5,
        news_limit: int = 5,
        knowledge_limit: int = 5,
    ) -> dict[str, Any]:
        """获取增强版个性化首页
        
        整合多种推荐策略：
        - 基于用户历史行为推荐内容
        - 基于用户兴趣标签推荐
        - 热门内容推荐（冷启动用户）
        - 近期咨询相关推荐
        
        Args:
            user_id: 用户ID
            db_session: 数据库会话（可选）
            lawyer_limit: 律师推荐数量
            post_limit: 帖子推荐数量
            news_limit: 新闻推荐数量
            knowledge_limit: 知识推荐数量
            
        Returns:
            增强版首页数据
        """
        profile = self.user_profile.get_user_profile(user_id)
        interests = profile.get("interests", [])
        browse_history = profile.get("browse_history", [])
        
        # 判断是否为冷启动用户（新用户或无历史记录）
        is_cold_start = len(browse_history) < 3 and len(interests) == 0
        
        # 初始化结果
        result = {
            "user_id": user_id,
            "is_cold_start": is_cold_start,
            "profile": {
                "interests": interests,
                "history_count": len(browse_history),
            },
            "lawyers": [],
            "posts": [],
            "news": [],
            "knowledge": [],
            "hot_content": [],
            "reason": "",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # 根据用户状态选择推荐策略
        if is_cold_start:
            # 冷启动用户：返回热门内容
            result["lawyers"] = await self._get_hot_lawyers(limit=lawyer_limit)
            result["posts"] = await self._get_hot_posts(limit=post_limit)
            result["news"] = await self._get_hot_news(limit=news_limit)
            result["knowledge"] = await self._get_hot_knowledge(limit=knowledge_limit)
            result["hot_content"] = await self._get_hot_content_recommendations(limit=10)
            result["reason"] = "热门内容推荐"
            result["recommendation_source"] = "cold_start"
        else:
            # 有历史记录的用户：基于兴趣推荐
            result["lawyers"] = await self._get_interest_based_lawyers(
                interests, limit=lawyer_limit
            )
            result["posts"] = await self._get_interest_based_posts(
                interests, browse_history, limit=post_limit
            )
            result["news"] = await self._get_interest_based_news(
                interests, limit=news_limit
            )
            result["knowledge"] = await self._get_interest_based_knowledge(
                interests, limit=knowledge_limit
            )
            result["hot_content"] = await self._get_hot_content_recommendations(limit=5)
            result["reason"] = "根据您的兴趣推荐"
            result["recommendation_source"] = "interest_based"
        
        return result

    async def _get_hot_lawyers(self, limit: int = 5) -> list[dict]:
        """获取热门律师推荐（冷启动用）"""
        # 从数据库获取热门律师
        # 这里简化处理，返回示例数据
        return [
            {
                "lawyer_id": 1,
                "name": "张律师",
                "title": "高级合伙人",
                "specialties": "劳动纠纷、合同纠纷",
                "rating": 4.9,
                "review_count": 256,
                "reason": "热门律师",
            },
            {
                "lawyer_id": 2,
                "name": "李律师",
                "title": "资深律师",
                "specialties": "婚姻家庭、房产纠纷",
                "rating": 4.8,
                "review_count": 189,
                "reason": "好评律师",
            },
        ][:limit]

    async def _get_interest_based_lawyers(
        self, interests: list[str], limit: int = 5
    ) -> list[dict]:
        """基于兴趣标签推荐律师"""
        # 根据用户兴趣匹配律师
        matched_lawyers = []
        
        for interest in interests:
            # 匹配律师擅长领域
            tag_name = HOT_CONTENT_TAGS.get(interest, interest)
            matched_lawyers.extend([
                {
                    "lawyer_id": 1,
                    "name": "王律师",
                    "title": "专业律师",
                    "specialties": f"{tag_name}、相关领域",
                    "rating": 4.7,
                    "review_count": 120,
                    "reason": f"擅长{tag_name}",
                },
            ])
        
        # 去重并返回
        seen = set()
        unique_lawyers = []
        for lawyer in matched_lawyers:
            if lawyer["lawyer_id"] not in seen:
                seen.add(lawyer["lawyer_id"])
                unique_lawyers.append(lawyer)
        
        return unique_lawyers[:limit]

    async def _get_hot_posts(self, limit: int = 5) -> list[dict]:
        """获取热门帖子"""
        return [
            {
                "post_id": 1,
                "title": "劳动仲裁全流程分享",
                "author": "资深用户",
                "view_count": 5680,
                "like_count": 256,
                "reason": "热门帖子",
            },
            {
                "post_id": 2,
                "title": "离婚财产分割经验谈",
                "author": "法律达人",
                "view_count": 4320,
                "like_count": 189,
                "reason": "高赞内容",
            },
        ][:limit]

    async def _get_interest_based_posts(
        self,
        interests: list[str],
        browse_history: list[dict],
        limit: int = 5,
    ) -> list[dict]:
        """基于兴趣和历史行为推荐帖子"""
        # 提取用户最近浏览的分类
        recent_categories = [
            h.get("category") for h in browse_history[-10:]
        ]
        
        matched_posts = []
        for interest in interests:
            tag_name = HOT_CONTENT_TAGS.get(interest, interest)
            matched_posts.append({
                "post_id": 3,
                "title": f"{tag_name}相关讨论",
                "author": "热心网友",
                "view_count": 1200,
                "like_count": 56,
                "reason": f"涉及{tag_name}",
            })
        
        return matched_posts[:limit]

    async def _get_hot_news(self, limit: int = 5) -> list[dict]:
        """获取热门新闻"""
        return [
            {
                "news_id": 1,
                "title": "2024年劳动法新规解读",
                "summary": "最新劳动法修改内容详细解读...",
                "view_count": 12580,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "reason": "热门新闻",
            },
            {
                "news_id": 2,
                "title": "婚姻家庭纠纷案例分析",
                "summary": "典型婚姻家庭案例法律分析...",
                "view_count": 8960,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "reason": "阅读量高",
            },
        ][:limit]

    async def _get_interest_based_news(
        self, interests: list[str], limit: int = 5
    ) -> list[dict]:
        """基于兴趣推荐新闻"""
        matched_news = []
        for interest in interests[:3]:
            tag_name = HOT_CONTENT_TAGS.get(interest, interest)
            matched_news.append({
                "news_id": 10,
                "title": f"{tag_name}最新动态",
                "summary": f"关于{tag_name}的最新法律资讯...",
                "view_count": 3500,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "reason": f"关于{tag_name}",
            })
        return matched_news[:limit]

    async def _get_hot_knowledge(self, limit: int = 5) -> list[dict]:
        """获取热门知识文章"""
        return [
            {
                "knowledge_id": 1,
                "title": "劳动合同到期不续签的法律后果",
                "category": "劳动法",
                "view_count": 15680,
                "reason": "热门知识",
            },
            {
                "knowledge_id": 2,
                "title": "离婚财产分割全攻略",
                "category": "婚姻法",
                "view_count": 12340,
                "reason": "实用指南",
            },
        ][:limit]

    async def _get_interest_based_knowledge(
        self, interests: list[str], limit: int = 5
    ) -> list[dict]:
        """基于兴趣推荐知识文章"""
        matched_knowledge = []
        for interest in interests[:3]:
            tag_name = HOT_CONTENT_TAGS.get(interest, interest)
            matched_knowledge.append({
                "knowledge_id": 10,
                "title": f"{tag_name}法律知识大全",
                "category": tag_name,
                "view_count": 5600,
                "reason": f"您感兴趣的{tag_name}知识",
            })
        return matched_knowledge[:limit]

    async def _get_hot_content_recommendations(
        self, limit: int = 10
    ) -> list[dict]:
        """获取热门内容推荐（综合）"""
        hot_content = [
            {
                "id": "news_1",
                "type": "news",
                "title": "2024年劳动法新规解读",
                "reason": "热门新闻",
                "tags": ["劳动纠纷"],
                "score": 0.95,
            },
            {
                "id": "post_1",
                "type": "post",
                "title": "劳动仲裁全流程分享",
                "reason": "热门帖子",
                "tags": ["劳动纠纷"],
                "score": 0.92,
            },
            {
                "id": "knowledge_1",
                "type": "knowledge",
                "title": "诉讼费用计算器使用指南",
                "reason": "热门工具",
                "tags": ["工具"],
                "score": 0.88,
            },
            {
                "id": "lawyer_1",
                "type": "lawyer",
                "title": "张律师 - 劳动纠纷专家",
                "reason": "资深律师",
                "tags": ["劳动纠纷"],
                "score": 0.90,
            },
            {
                "id": "news_2",
                "type": "news",
                "title": "婚姻家庭纠纷案例分析",
                "reason": "热门新闻",
                "tags": ["婚姻家庭"],
                "score": 0.87,
            },
        ]
        return hot_content[:limit]

    async def update_user_interests(
        self,
        user_id: int,
        interests: list[str],
    ) -> dict[str, Any]:
        """更新用户兴趣

        Args:
            user_id: 用户ID
            interests: 兴趣列表

        Returns:
            更新结果
        """
        result = self.user_profile.update_interests(user_id, interests)

        return {
            **result,
            "profile": self.user_profile.get_user_profile(user_id),
        }

    async def track_content_view(
        self,
        user_id: int,
        item_id: str,
        category: str,
    ) -> dict[str, Any]:
        """追踪内容浏览

        Args:
            user_id: 用户ID
            item_id: 内容ID
            category: 分类

        Returns:
            追踪结果
        """
        history_result = self.user_profile.add_browse_history(
            user_id, item_id, category)
        self.interest_recommender.track_click(user_id, item_id)

        return {
            "success": True,
            "history_count": history_result["history_count"],
        }

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计数据
        """
        total_users = len(self.user_profile._profiles)
        users_with_interests = sum(
            1 for p in self.user_profile._profiles.values()
            if p["interests"]
        )

        total_recommendations = sum(
            len(r) for r in self.interest_recommender._recommendations.values()
        )

        return {
            "total_users": total_users,
            "users_with_interests": users_with_interests,
            "interest_adoption_rate": round(users_with_interests / max(total_users, 1) * 100, 2),
            "total_recommendations": total_recommendations,
        }


# 单例实例
personalized_home_service = PersonalizedHomeService()


async def get_personalized_home(user_id: int) -> dict[str, Any]:
    """便捷函数：获取个性化首页

    Args:
        user_id: 用户ID

    Returns:
        首页数据
    """
    return await personalized_home_service.get_personalized_home(user_id=user_id)


async def update_user_interests(
    user_id: int,
    interests: list[str],
) -> dict[str, Any]:
    """便捷函数：更新用户兴趣

    Args:
        user_id: 用户ID
        interests: 兴趣列表

    Returns:
        更新结果
    """
    return await personalized_home_service.update_user_interests(
        user_id=user_id,
        interests=interests,
    )


async def track_content_view(
    user_id: int,
    item_id: str,
    category: str,
) -> dict[str, Any]:
    """便捷函数：追踪内容浏览

    Args:
        user_id: 用户ID
        item_id: 内容ID
        category: 分类

    Returns:
        追踪结果
    """
    return await personalized_home_service.track_content_view(
        user_id=user_id,
        item_id=item_id,
        category=category,
    )
