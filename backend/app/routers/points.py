"""积分系统 API 路由"""

import logging
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..database import get_db
from ..utils.deps import get_current_user
from ..services.points import (
    get_points_service,
    get_points_product_service,
    PointsProduct,
    PointsExchangeOrder,
)
from ..services.points_manager import get_points_manager
from ..database import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/points", tags=["积分系统"])


class AwardPointsRequest(BaseModel):
    """奖励积分请求"""
    action: str
    description: Optional[str] = None
    metadata: Optional[dict] = None


class RedeemRequest(BaseModel):
    """消耗积分请求"""
    product_id: str


class CreateProductRequest(BaseModel):
    """创建商品请求"""
    id: str
    name: str
    description: str
    points_required: int
    product_type: str
    image_url: Optional[str] = None
    stock: int = -1


@router.get("/balance", summary="获取积分余额")
async def get_balance(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取当前用户的积分余额"""
    service = get_points_service()
    return {
        "balance": service.get_balance(current_user.id),
        "continuous_days": service.get_continuous_days(current_user.id),
    }


@router.get("/history", summary="获取积分历史")
async def get_history(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """获取积分变动历史"""
    service = get_points_service()
    history = service.get_history(current_user.id, limit=limit, offset=offset)
    return {
        "history": [
            {
                "id": item.id,
                "action": item.action,
                "points": item.points,
                "balance_after": item.balance_after,
                "description": item.description,
                "created_at": item.created_at.isoformat(),
            }
            for item in history
        ],
    }


@router.get("/daily-stats", summary="获取今日统计")
async def get_daily_stats(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取今日各动作的完成次数"""
    service = get_points_service()
    return {
        "stats": service.get_daily_stats(current_user.id),
    }


@router.get("/rules", summary="获取积分规则")
async def get_rules():
    """获取所有积分规则"""
    service = get_points_service()
    return {
        "rules": service.get_rules(),
    }


@router.post("/check-in", summary="每日签到")
async def check_in(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """每日签到获取积分"""
    manager = get_points_manager()
    result = await manager.daily_signin(db, current_user.id)
    if result["success"]:
        return {
            "message": "签到成功",
            "points_earned": result["points"],
            "continuous_days": result["continuous_days"],
            "total_points": result["total_points"],
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "签到失败")
        )


@router.get("/leaderboard", summary="获取积分排行榜")
async def get_leaderboard(
    top_k: int = Query(100, ge=1, le=500),
):
    """获取积分排行榜"""
    service = get_points_service()
    return {
        "leaderboard": service.get_leaderboard(top_k),
    }


# === 积分兑换相关 ===

@router.get("/products", summary="获取积分商品列表")
async def list_products(
    product_type: Optional[str] = None,
):
    """获取可兑换的商品列表"""
    service = get_points_product_service()
    products = service.list_products(product_type=product_type)
    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "points_required": p.points_required,
                "product_type": p.product_type,
                "image_url": p.image_url,
                "stock": p.stock,
                "status": p.status,
            }
            for p in products
        ],
    }


@router.get("/products/{product_id}", summary="获取商品详情")
async def get_product(product_id: str):
    """获取单个商品的详情"""
    service = get_points_product_service()
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {
        "product": {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "points_required": product.points_required,
            "product_type": product.product_type,
            "image_url": product.image_url,
            "stock": product.stock,
            "status": product.status,
            "metadata": product.metadata,
        }
    }


@router.post("/redeem", summary="兑换商品")
async def redeem_product(
    request: RedeemRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """使用积分兑换商品"""
    service = get_points_product_service()
    order, error = await service.create_order(
        user_id=current_user.id,
        product_id=request.product_id,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    if order is None:
        raise HTTPException(status_code=500, detail="兑换订单创建失败")
    assert order is not None
    return {
        "success": True,
        "order": {
            "id": order.id,
            "product_id": order.product_id,
            "product_name": order.product_name,
            "points_spent": order.points_spent,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
        },
    }


@router.get("/orders", summary="获取兑换订单")
async def get_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
):
    """获取用户的兑换订单"""
    service = get_points_product_service()
    orders = service.get_user_orders(
        current_user.id, status=status, limit=limit)
    return {
        "orders": [
            {
                "id": o.id,
                "product_id": o.product_id,
                "product_name": o.product_name,
                "points_spent": o.points_spent,
                "status": o.status,
                "created_at": o.created_at.isoformat(),
                "completed_at": o.completed_at.isoformat() if o.completed_at else None,
            }
            for o in orders
        ],
    }


# === 管理端接口 ===

@router.post("/admin/products", summary="创建积分商品")
async def create_product(
    request: CreateProductRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """创建新的积分商品（需要管理员权限）"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = get_points_product_service()
    product = PointsProduct(
        id=request.id,
        name=request.name,
        description=request.description,
        points_required=request.points_required,
        product_type=request.product_type,
        image_url=request.image_url,
        stock=request.stock,
    )
    service.add_product(product)
    return {"success": True, "product_id": request.id}


@router.put("/admin/products/{product_id}", summary="更新积分商品")
async def update_product(
    product_id: str,
    request: CreateProductRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """更新积分商品信息（需要管理员权限）"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = get_points_product_service()
    success = service.update_product(product_id, request.model_dump())
    if not success:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {"success": True}


@router.delete("/admin/products/{product_id}", summary="删除积分商品")
async def delete_product(
    product_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """删除积分商品（需要管理员权限）"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = get_points_product_service()
    success = service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {"success": True}
