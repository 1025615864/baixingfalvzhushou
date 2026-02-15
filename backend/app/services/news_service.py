"""新闻服务

⚠️ 已迁移到 services/news/
⚠️ 本文件仅用于向后兼容，请使用新导入路径

迁移时间: 2026-01-22
"""
from .news import (
    news_service,
    NewsService,
    get_news_service,
    news_topic_service,
    NewsTopicService,
    news_comment_service,
    NewsCommentService,
    news_subscription_service,
    NewsSubscriptionService,
)

__all__ = [
    "news_service",
    "NewsService",
    "get_news_service",
    "news_topic_service",
    "NewsTopicService",
    "news_comment_service",
    "NewsCommentService",
    "news_subscription_service",
    "NewsSubscriptionService",
]
