import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SERVICES = {
    "user-service": os.getenv("USER_SERVICE_URL", "http://user-service:8001"),
    "order-service": os.getenv("ORDER_SERVICE_URL", "http://order-service:8004"),
    "payment-channel-service": os.getenv("PAYMENT_CHANNEL_SERVICE_URL", "http://payment-channel-service:8002"),
    "ai-service": os.getenv("AI_SERVICE_URL", "http://ai-service:8005"),
    "embedding-service": os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8003"),
    "news-service": os.getenv("NEWS_SERVICE_URL", "http://news-service:8006"),
    "community-service": os.getenv("COMMUNITY_SERVICE_URL", "http://community-service:8007"),
    "legal-service": os.getenv("LEGAL_SERVICE_URL", "http://legal-service:8008"),
    "search-service": os.getenv("SEARCH_SERVICE_URL", "http://search-service:8009"),
    "recommendation-service": os.getenv("RECOMMENDATION_SERVICE_URL", "http://recommendation-service:8010"),
    "notification-service": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8011"),
    "points-service": os.getenv("POINTS_SERVICE_URL", "http://points-service:8012"),
    "archive-service": os.getenv("ARCHIVE_SERVICE_URL", "http://archive-service:8013"),
    "knowledge-service": os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8081"),
}


async def check_service_health(client: httpx.AsyncClient, name: str, url: str) -> dict:
    try:
        resp = await client.get(f"{url}/health/ready", timeout=5)
        if resp.status_code == 200:
            return {"name": name, "status": "healthy", "details": resp.json()}
        return {"name": name, "status": "degraded", "details": resp.json()}
    except httpx.TimeoutException:
        return {"name": name, "status": "timeout", "details": None}
    except Exception as e:
        return {"name": name, "status": "unreachable", "details": str(e)}


async def check_all_services() -> dict:
    async with httpx.AsyncClient() as client:
        tasks = [check_service_health(client, name, url) for name, url in SERVICES.items()]
        results = await asyncio.gather(*tasks)

    healthy = [r for r in results if r["status"] == "healthy"]
    degraded = [r for r in results if r["status"] == "degraded"]
    unhealthy = [r for r in results if r["status"] not in ("healthy", "degraded")]

    overall = "healthy"
    if unhealthy:
        overall = "unhealthy"
    elif degraded:
        overall = "degraded"

    return {
        "overall": overall,
        "total": len(results),
        "healthy": len(healthy),
        "degraded": len(degraded),
        "unhealthy": len(unhealthy),
        "services": results,
    }


def register_health_routes(app):
    @app.get("/health/cluster")
    async def cluster_health():
        result = await check_all_services()
        status_code = 200 if result["overall"] in ("healthy", "degraded") else 503
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=status_code, content=result)
