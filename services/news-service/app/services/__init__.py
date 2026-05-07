"""新闻服务层"""
from .news_service import news_service
from .comment_service import comment_service
from .subscription_service import subscription_service

__all__ = ["news_service", "comment_service", "subscription_service"]
