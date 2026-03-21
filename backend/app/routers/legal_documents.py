"""法律文书商城 API 路由

提供法律文书的列表、详情、购买、积分兑换等功能。
"""

from __future__ import annotations

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..utils.deps import get_current_user, get_current_user_optional, require_admin
from ..services.legal_document_service import legal_document_service

router = APIRouter(prefix="/legal-documents", tags=["法律文书商城"])


# ==================== 请求/响应模型 ====================


class DocumentListQuery(BaseModel):
    """法律文书列表查询参数"""
    category: str | None = None
    keyword: str | None = None
    page: int = 1
    page_size: int = 20
    is_featured: bool | None = None
    is_free: bool | None = None


class DocumentListResponse(BaseModel):
    """法律文书列表响应"""
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


class DocumentDetailResponse(BaseModel):
    """法律文书详情响应"""
    id: int
    name: str
    description: str | None
    category: str
    category_name: str
    price: int
    is_free: bool
    is_featured: bool
    view_count: int
    download_count: int
    rating: float
    tags: list[str]
    custom_service_available: bool
    custom_service_price: int
    member_prices: dict | None
    created_at: str | None
    is_favorited: bool = False
    is_purchased: bool = False


class DocumentContentResponse(BaseModel):
    """法律文书内容响应"""
    id: int
    name: str
    content: str
    order_no: str
    purchased_at: str | None


class PriceCalculationResponse(BaseModel):
    """价格计算响应"""
    price: int
    original_price: int
    discount: int
    is_free: bool
    payment_method: str
    tier: str | None = None


class PurchaseRequest(BaseModel):
    """购买请求"""
    payment_method: str = "points"  # points, free, member_free


class PurchaseResponse(BaseModel):
    """购买响应"""
    success: bool
    order_no: str | None = None
    document_id: int | None = None
    document_name: str | None = None
    points_spent: int | None = None
    payment_method: str | None = None
    error: str | None = None
    balance: int | None = None
    required: int | None = None


class OrderListResponse(BaseModel):
    """订单列表响应"""
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


class CategoryResponse(BaseModel):
    """分类响应"""
    name: str
    categories: list[dict[str, str]]


# ==================== API 端点 ====================


@router.get("/categories", response_model=list[CategoryResponse], summary="获取文书分类")
async def get_categories():
    """获取法律文书分类列表（带分组）"""
    categories = await legal_document_service.list_categories()
    return categories


@router.get("", response_model=DocumentListResponse, summary="获取法律文书列表")
async def list_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = Query(None, description="分类"),
    keyword: str | None = Query(None, description="关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_featured: bool | None = Query(None, description="是否推荐"),
    is_free: bool | None = Query(None, description="是否免费"),
):
    """获取法律文书列表"""
    result = await legal_document_service.get_documents(
        db,
        category=category,
        keyword=keyword,
        page=page,
        page_size=page_size,
        is_featured=is_featured,
        is_free=is_free,
    )
    return result


@router.get("/featured", summary="获取推荐文书")
async def get_featured_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(6, ge=1, le=20, description="返回数量"),
):
    """获取推荐的法律文书"""
    documents = await legal_document_service.get_featured_documents(db, limit)
    return {"items": documents}


@router.get("/free", summary="获取免费文书")
async def get_free_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
):
    """获取免费的法律文书"""
    documents = await legal_document_service.get_free_documents(db, limit)
    return {"items": documents}


@router.get("/{document_id}", response_model=DocumentDetailResponse, summary="获取法律文书详情")
async def get_document(
    document_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
):
    """获取法律文书详情"""
    document = await legal_document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")

    # 检查收藏和购买状态
    is_favorited = False
    is_purchased = False

    if current_user:
        is_favorited = await legal_document_service.is_favorited(
            db, int(current_user.id), document_id
        )
        is_purchased = await legal_document_service.is_purchased(
            db, int(current_user.id), document_id
        )

    return {
        **document,
        "is_favorited": is_favorited,
        "is_purchased": is_purchased,
    }


@router.get("/{document_id}/content", summary="获取文书内容")
async def get_document_content(
    db: Annotated[AsyncSession, Depends(get_db)],
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取法律文书内容（需要已购买）"""
    content = await legal_document_service.get_document_content(
        db, document_id, int(current_user.id)
    )
    if not content:
        raise HTTPException(
            status_code=403,
            detail="您尚未购买此文书，请先购买后再查看内容",
        )
    return content


@router.get("/{document_id}/price", response_model=PriceCalculationResponse, summary="计算价格")
async def calculate_price(
    db: Annotated[AsyncSession, Depends(get_db)],
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """计算法律文书价格（考虑会员权益）"""
    price_info = await legal_document_service.calculate_price(
        db, document_id, int(current_user.id)
    )
    if "error" in price_info:
        raise HTTPException(status_code=400, detail=price_info["error"])
    return price_info


@router.post("/{document_id}/purchase", response_model=PurchaseResponse, summary="购买法律文书")
async def purchase_document(
    db: Annotated[AsyncSession, Depends(get_db)],
    document_id: int,
    request: PurchaseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """购买法律文书（积分购买）"""
    result = await legal_document_service.purchase_document(
        db,
        document_id,
        int(current_user.id),
        request.payment_method,
    )
    return result


@router.post("/{document_id}/favorite", summary="添加收藏")
async def add_favorite(
    db: Annotated[AsyncSession, Depends(get_db)],
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """添加收藏"""
    result = await legal_document_service.add_favorite(
        db, int(current_user.id), document_id
    )
    return result


@router.delete("/{document_id}/favorite", summary="取消收藏")
async def remove_favorite(
    db: Annotated[AsyncSession, Depends(get_db)],
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """取消收藏"""
    result = await legal_document_service.remove_favorite(
        db, int(current_user.id), document_id
    )
    return result


@router.get("/user/favorites", summary="获取收藏列表")
async def get_favorites(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取用户收藏的法律文书列表"""
    favorites = await legal_document_service.get_user_favorites(
        db, int(current_user.id)
    )
    return {"items": favorites}


@router.get("/user/orders", response_model=OrderListResponse, summary="获取购买记录")
async def get_user_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取用户购买记录"""
    result = await legal_document_service.get_user_orders(
        db, int(current_user.id), page, page_size
    )
    return result