"""推荐系统服务

提供冷启动、兴趣图谱、个性化推荐等功能。
"""

from .cold_start import (
    ColdStartService,
    UserInterestProfile,
    OnboardingQuestion,
    get_cold_start_service,
)

from .interest_graph import (
    InterestGraph,
    InterestNode,
    InterestEdge,
    get_interest_graph,
    record_user_interaction,
)

from .enhanced_recommendation import (
    EnhancedRecommendationService,
    RecommendationItem,
    RecommendationResult,
    get_enhanced_recommendation_service,
)

__all__ = [
    # 冷启动
    "ColdStartService",
    "UserInterestProfile",
    "OnboardingQuestion",
    "get_cold_start_service",

    # 兴趣图谱
    "InterestGraph",
    "InterestNode",
    "InterestEdge",
    "get_interest_graph",
    "record_user_interaction",

    # 推荐服务
    "EnhancedRecommendationService",
    "RecommendationItem",
    "RecommendationResult",
    "get_enhanced_recommendation_service",
]
