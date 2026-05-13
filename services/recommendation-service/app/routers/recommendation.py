from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.recommendation_service import recommendation_service

router = APIRouter()


@router.get("/recommendations")
async def get_recommendations(
    type: str = Query("lawyer", description="lawyer|article|service|post|knowledge|homepage|feed"),
    user_id: int = Query(default=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    if type == "lawyer":
        items = await recommendation_service.recommend_lawyers(db, user_id=user_id, limit=limit)
    elif type == "article" or type == "news":
        items = await recommendation_service.recommend_news(db, user_id=user_id, limit=limit)
    elif type == "post":
        items = await recommendation_service.recommend_posts(db, user_id=user_id, limit=limit)
    elif type == "knowledge":
        items = await recommendation_service.recommend_knowledge(db, user_id=user_id, limit=limit)
    elif type == "homepage":
        items = await recommendation_service.recommend_homepage(db, user_id=user_id, limit=limit)
    elif type == "feed":
        items = await recommendation_service.get_personalized_feed(db, user_id=user_id, limit=limit)
    else:
        items = await recommendation_service.recommend_homepage(db, user_id=user_id, limit=limit)

    return {"type": type, "items": items}
