"""新闻AI流水线服务

⚠️ 已迁移到 services/news_ai/
⚠️ 本文件仅用于向后兼容，请使用新导入路径

迁移时间: 2026-01-22
"""
from .news_ai import (
    news_ai_pipeline_service,
    NewsAIPipelineService,
    get_news_ai_pipeline_service,
    news_ai_summarization_service,
    NewsAISummarizationService,
)

__all__ = [
    "news_ai_pipeline_service",
    "NewsAIPipelineService",
    "get_news_ai_pipeline_service",
    "news_ai_summarization_service",
    "NewsAISummarizationService",
]
