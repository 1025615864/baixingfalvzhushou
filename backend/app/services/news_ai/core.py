from app.services.news_ai_pipeline_service import NewsAIPipelineService, news_ai_pipeline_service


def get_news_ai_pipeline_service() -> NewsAIPipelineService:
    return news_ai_pipeline_service


__all__ = ["NewsAIPipelineService", "news_ai_pipeline_service", "get_news_ai_pipeline_service"]
