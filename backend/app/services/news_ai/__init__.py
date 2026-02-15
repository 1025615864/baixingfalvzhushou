"""新闻AI服务模块

向后兼容导出（2026-01-22）
"""
from .core import NewsAIPipelineService, get_news_ai_pipeline_service, news_ai_pipeline_service
from .summarization import NewsAISummarizationService, news_ai_summarization_service

__all__ = [
    "NewsAIPipelineService",
    "get_news_ai_pipeline_service",
    "news_ai_pipeline_service",
    "NewsAISummarizationService",
    "news_ai_summarization_service",
]
