"""订阅路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_subscriptions(user_id: int):
    return {"items": []}


@router.post("/")
async def create_subscription(user_id: int, category: str):
    return {"id": 1, "user_id": user_id, "category": category}


@router.delete("/{subscription_id}")
async def delete_subscription(subscription_id: int):
    return {"success": True}
