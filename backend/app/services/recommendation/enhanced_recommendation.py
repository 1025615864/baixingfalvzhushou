"""增强的推荐服务

整合冷启动服务和兴趣图谱，提供个性化推荐能力。
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .cold_start import ColdStartService, UserInterestProfile, get_cold_start_service
from .interest_graph import InterestGraph, get_interest_graph

logger = logging.getLogger(__name__)


@dataclass
class RecommendationItem:
    """推荐项"""
    item_id: str
    item_type: str  # news, forum_post, lawyer, document_template
    title: str
    description: Optional[str] = None
    score: float = 0.0
    reason: str = ""
    metadata: Optional[Dict] = None


@dataclass
class RecommendationResult:
    """推荐结果"""
    items: List[RecommendationItem]
    total: int
    source: str  # cold_start, collaborative, content_based, hybrid
    user_id: Optional[int] = None


class EnhancedRecommendationService:
    """增强的推荐服务

    整合多种推荐策略：
    1. 冷启动推荐（新用户）
    2. 协同过滤（相似用户）
    3. 内容推荐（基于标签）
    4. 混合推荐（综合多种策略）
    """

    def __init__(self):
        self._cold_start_service = get_cold_start_service()
        self._interest_graph = get_interest_graph()

    # 热门内容（全局）
    HOT_NEWS: List[Dict] = [
        {"id": "news_001",
         "title": "2024年劳动法新规解读",
         "type": "news",
         "tags": ["labor_dispute"],
         "score": 0.95},
        {"id": "news_002", "title": "婚姻家庭纠纷案例分析", "type": "news",
            "tags": ["marriage_family"], "score": 0.90},
        {"id": "news_003", "title": "合同纠纷预防指南", "type": "news",
            "tags": ["contract_dispute"], "score": 0.88},
    ]

    HOT_POSTS: List[Dict] = [
        {"id": "post_001",
         "title": "劳动仲裁全流程分享",
         "type": "forum_post",
         "tags": ["labor_dispute"],
         "score": 0.92},
        {"id": "post_002",
         "title": "离婚财产分割经验谈",
         "type": "forum_post",
         "tags": ["marriage_family"],
         "score": 0.87},
        {"id": "post_003",
         "title": "合同审查避坑指南",
         "type": "forum_post",
         "tags": ["contract_dispute"],
         "score": 0.85},
    ]

    POPULAR_TOOLS: List[Dict] = [
        {"id": "tool_001",
         "title": "诉讼费用计算器",
         "type": "tool",
         "tags": ["calculator"],
         "score": 0.90},
        {"id": "tool_002",
         "title": "诉讼时效查询",
         "type": "tool",
         "tags": ["limitation"],
         "score": 0.85},
        {"id": "tool_003",
         "title": "经济补偿金计算",
         "type": "tool",
         "tags": ["severance"],
         "score": 0.82},
    ]

    async def get_recommendations(
        self,
        user_id: Optional[int],
        recommendation_type: str = "hybrid",
        limit: int = 10,
    ) -> RecommendationResult:
        """获取推荐结果

        Args:
            user_id: 用户ID（可选）
            recommendation_type: 推荐类型
            limit: 返回数量限制
        """
        if user_id is None:
            # 未登录用户，返回热门内容
            return await self._get_hot_recommendations(limit)

        # 检查用户画像
        profile = self._cold_start_service.get_user_profile(user_id)

        if not profile or not profile.onboarding_completed:
            # 未完成引导，返回冷启动推荐
            return await self._get_cold_start_recommendations(user_id, limit)

        # 根据类型选择推荐策略
        if recommendation_type == "cold_start":
            return await self._get_cold_start_recommendations(user_id, limit)
        elif recommendation_type == "collaborative":
            return await self._get_collaborative_recommendations(user_id, limit)
        elif recommendation_type == "content_based":
            return await self._get_content_based_recommendations(user_id, limit)
        else:
            return await self._get_hybrid_recommendations(user_id, limit)

    async def _get_hot_recommendations(
            self, limit: int) -> RecommendationResult:
        """获取热门内容推荐（未登录用户）"""
        items = []

        # 混合热门新闻和帖子
        all_hot = self.HOT_NEWS + self.HOT_POSTS + self.POPULAR_TOOLS
        for i, item in enumerate(all_hot[:limit]):
            items.append(RecommendationItem(
                item_id=item["id"],
                item_type=item["type"],
                title=item["title"],
                score=item["score"],
                reason="热门内容",
                metadata={"tags": item.get("tags", [])},
            ))

        return RecommendationResult(
            items=items,
            total=len(items),
            source="hot_content",
        )

    async def _get_cold_start_recommendations(
        self,
        user_id: int,
        limit: int,
    ) -> RecommendationResult:
        """获取冷启动推荐"""
        items = []

        # 根据用户当前行为，推荐相关内容
        profile = self._cold_start_service.get_user_profile(user_id)
        top_tags = []

        if profile:
            # 使用已知的兴趣标签
            top_tags = list(profile.interest_weights.keys())[:3]

        # 如果没有标签，使用默认热门
        if not top_tags:
            top_tags = ["labor_dispute", "contract_dispute", "marriage_family"]

        # 推荐热门内容
        for i, tag in enumerate(top_tags):
            # 匹配标签的新闻
            for news in self.HOT_NEWS:
                if tag in news.get("tags", []):
                    score = 1.0 - (i * 0.1)  # 按标签顺序递减
                    items.append(RecommendationItem(
                        item_id=news["id"],
                        item_type=news["type"],
                        title=news["title"],
                        score=score,
                        reason=f"因为您对{self._get_tag_name(tag)}感兴趣",
                        metadata={"tags": news.get("tags", [])},
                    ))

        # 如果项目不足，补充热门工具
        tools = list(self.POPULAR_TOOLS)
        tool_idx = 0
        while len(items) < limit and tool_idx < len(tools):
            tool = tools[tool_idx]
            tool_idx += 1
            items.append(RecommendationItem(
                item_id=tool["id"],
                item_type=tool["type"],
                title=tool["title"],
                score=tool["score"] * 0.8,
                reason="热门工具推荐",
                metadata={"tags": tool.get("tags", [])},
            ))

        return RecommendationResult(
            items=items[:limit],
            total=len(items[:limit]),
            source="cold_start",
            user_id=user_id,
        )

    async def _get_collaborative_recommendations(
        self,
        user_id: int,
        limit: int,
    ) -> RecommendationResult:
        """获取协同过滤推荐"""
        items = []

        # 获取相似用户
        similar_users = self._interest_graph.get_user_similar_users(
            user_id, top_k=10)

        if not similar_users:
            return await self._get_content_based_recommendations(user_id, limit)

        # 获取相似用户喜欢的内容
        seen_contents = set(
            self._interest_graph._user_content_matrix.get(
                user_id, {}).keys())
        content_scores: Dict[str, float] = {}

        for other_id, similarity in similar_users:
            other_contents = self._interest_graph._user_content_matrix.get(
                other_id, {})
            for content_id, weight in other_contents.items():
                if content_id in seen_contents:
                    continue

                current_score = content_scores.get(content_id, 0)
                content_scores[content_id] = current_score + \
                    similarity * weight

        # 排序并返回
        sorted_contents = sorted(
            content_scores.items(),
            key=lambda x: x[1],
            reverse=True)

        for content_id, score in sorted_contents[:limit]:
            items.append(RecommendationItem(
                item_id=content_id,
                item_type="content",
                title=f"内容 {content_id}",
                score=score,
                reason="与你相似的用户也喜欢",
            ))

        return RecommendationResult(
            items=items,
            total=len(items),
            source="collaborative",
            user_id=user_id,
        )

    async def _get_content_based_recommendations(
        self,
        user_id: int,
        limit: int,
    ) -> RecommendationResult:
        """获取基于内容的推荐"""
        items = []

        # 获取用户偏好标签
        preferred_tags = self._interest_graph.get_user_preferred_tags(
            user_id, top_k=5)

        if not preferred_tags:
            return await self._get_cold_start_recommendations(user_id, limit)

        # 根据标签匹配内容
        for tag, tag_score in preferred_tags:
            tag_name = self._get_tag_name(tag)

            # 匹配新闻
            for news in self.HOT_NEWS:
                if tag in news.get("tags", []) or any(
                        tag in t for t in news.get("tags", [])):
                    items.append(RecommendationItem(
                        item_id=news["id"],
                        item_type=news["type"],
                        title=news["title"],
                        score=tag_score * news["score"],
                        reason=f"因为您对{tag_name}感兴趣",
                        metadata={"tags": news.get("tags", [])},
                    ))

        # 去重并排序
        seen = set()
        unique_items = []
        for item in items:
            if item.item_id not in seen:
                seen.add(item.item_id)
                unique_items.append(item)

        unique_items.sort(key=lambda x: x.score, reverse=True)

        return RecommendationResult(
            items=unique_items[:limit],
            total=len(unique_items[:limit]),
            source="content_based",
            user_id=user_id,
        )

    async def _get_hybrid_recommendations(
        self,
        user_id: int,
        limit: int,
    ) -> RecommendationResult:
        """获取混合推荐"""
        items = []

        # 获取各策略推荐
        cold_items = await self._get_cold_start_recommendations(user_id, limit=5)
        content_items = await self._get_content_based_recommendations(user_id, limit=5)

        # 合并并去重
        seen = set()
        for source_items in [cold_items.items, content_items.items]:
            for item in source_items:
                if item.item_id not in seen:
                    seen.add(item.item_id)
                    items.append(item)

        # 按分数排序
        items.sort(key=lambda x: x.score, reverse=True)

        return RecommendationResult(
            items=items[:limit],
            total=len(items[:limit]),
            source="hybrid",
            user_id=user_id,
        )

    def _get_tag_name(self, tag: str) -> str:
        """获取标签名称"""
        tag_names = {
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
        return tag_names.get(tag, tag)

    async def get_onboarding_survey(self) -> List[Dict[str, Any]]:
        """获取引导问卷"""
        return self._cold_start_service.get_onboarding_survey()

    async def complete_onboarding(
        self,
        user_id: int,
        answers: Dict[str, Any],
    ) -> UserInterestProfile:
        """完成引导"""
        return self._cold_start_service.process_onboarding_answers(
            user_id, answers)

    def record_interaction(
        self,
        user_id: int,
        content_id: str,
        content_type: str,
        tags: List[str],
        interaction_type: str = "viewed",
        weight: float = 1.0,
    ) -> None:
        """记录用户交互"""
        self._interest_graph.add_interaction(
            user_id=user_id,
            content_id=content_id,
            content_type=content_type,
            tags=tags,
            interaction_type=interaction_type,
            weight=weight,
        )

    def should_show_onboarding(self, user_id: int) -> bool:
        """判断是否应该显示引导"""
        return self._cold_start_service.should_show_onboarding(user_id)

    def get_recommendation_weights(self, user_id: int) -> Dict[str, float]:
        """获取推荐权重"""
        return self._cold_start_service.get_recommendation_weights(user_id)


# 获取增强推荐服务单例
_recommendation_service: Optional[EnhancedRecommendationService] = None


def get_enhanced_recommendation_service() -> EnhancedRecommendationService:
    """获取增强推荐服务单例"""
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = EnhancedRecommendationService()
    return _recommendation_service
