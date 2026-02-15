"""新闻服务模块

向后兼容导出（2026-01-22）
"""
from .core import NewsService, get_news_service, news_service
from .topics import NewsTopicService, news_topic_service
from .comments import NewsCommentService, news_comment_service
from .subscriptions import NewsSubscriptionService, news_subscription_service

__all__ = [
    "NewsService",
    "get_news_service",
    "news_service",
    "NewsTopicService",
    "news_topic_service",
    "NewsCommentService",
    "news_comment_service",
    "NewsSubscriptionService",
    "news_subscription_service",
]
