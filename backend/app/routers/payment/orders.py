"""支付订单路由"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...services.payment import PaymentCoreService, wechatpay_service, alipay_service
from ...utils.deps import get_current_user
from ...utils.payment_security import (
    validate_payment_request,
    PaymentAuditLogger,
    PaymentIdempotency
)

router = APIRouter()


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    order_type: str = Field(..., description="订单类型")
    amount: float = Field(..., gt=0, description="订单金额")
    title: str = Field(..., min_length=1, max_length=200, description="订单标题")
    description: str | None = Field(None, max_length=500, description="订单描述")
    payment_method: str = Field(..., description="支付方式: wechat/alipay")
    related_id: int | None = Field(None, description="关联ID")
    related_type: str | None = Field(None, description="关联类型")


class CreateWechatOrderRequest(CreateOrderRequest):
    """创建微信订单请求"""
    openid: str = Field(..., description="用户微信openid")


class OrderResponse(BaseModel):
    """订单响应"""
    order_no: str
    amount: float
    status: str
    payment_method: str | None
    created_at: str


@router.post("/orders", response_model=OrderResponse, summary="创建支付订单")
async def create_order(
    request: CreateOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    http_request: Request,
) -> OrderResponse:
    """创建支付订单（通用）"""
    # 获取客户端信息
    ip_address = http_request.client.host if http_request.client else ""
    user_agent = http_request.headers.get("user-agent", "")

    # 风控检查
    validation = await validate_payment_request(
        db, current_user.id, request.amount, ip_address, user_agent
    )

    # 检查重复订单（60秒内）
    duplicate = await PaymentIdempotency.check_duplicate_order(
        db, current_user.id, request.order_type, request.amount, request.related_id
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请勿重复提交订单"
        )

    order = await PaymentCoreService.create_order(
        db=db,
        user_id=current_user.id,
        order_type=request.order_type,
        amount=request.amount,
        title=request.title,
        description=request.description,
        payment_method=request.payment_method,
        related_id=request.related_id,
        related_type=request.related_type,
    )

    # 记录审计日志
    PaymentAuditLogger.log_payment_created(order, ip_address, user_agent)

    return OrderResponse(
        order_no=order.order_no,
        amount=order.amount,
        status=order.status,
        payment_method=order.payment_method,
        created_at=order.created_at.isoformat() if order.created_at else "",
    )


@router.post("/orders/wechat/jsapi", summary="创建微信支付JSAPI订单")
async def create_wechat_jsapi_order(
    request: CreateWechatOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """创建微信支付JSAPI订单（用于微信公众号/小程序）"""
    try:
        result = await wechatpay_service.create_jsapi_order(
            db=db,
            user_id=current_user.id,
            amount=request.amount,
            title=request.title,
            openid=request.openid,
            order_type=request.order_type,
            description=request.description,
            related_id=request.related_id,
            related_type=request.related_type,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/orders/wechat/native", summary="创建微信支付Native订单")
async def create_wechat_native_order(
    request: CreateOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """创建微信支付Native订单（扫码支付）"""
    try:
        result = await wechatpay_service.create_native_order(
            db=db,
            user_id=current_user.id,
            amount=request.amount,
            title=request.title,
            order_type=request.order_type,
            description=request.description,
            related_id=request.related_id,
            related_type=request.related_type,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/orders/alipay/page", summary="创建支付宝电脑网站支付订单")
async def create_alipay_page_order(
    request: CreateOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """创建支付宝电脑网站支付订单"""
    try:
        result = await alipay_service.create_page_order(
            db=db,
            user_id=current_user.id,
            amount=request.amount,
            title=request.title,
            order_type=request.order_type,
            description=request.description,
            related_id=request.related_id,
            related_type=request.related_type,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/orders/alipay/wap", summary="创建支付宝手机网站支付订单")
async def create_alipay_wap_order(
    request: CreateOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """创建支付宝手机网站支付订单"""
    try:
        result = await alipay_service.create_wap_order(
            db=db,
            user_id=current_user.id,
            amount=request.amount,
            title=request.title,
            order_type=request.order_type,
            description=request.description,
            related_id=request.related_id,
            related_type=request.related_type,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/orders/{order_no}", response_model=OrderResponse, summary="查询订单")
async def get_order(
    order_no: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    """根据订单号查询订单"""
    order = await PaymentCoreService.get_order_by_no(db, order_no)

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此订单")

    return OrderResponse(
        order_no=order.order_no,
        amount=order.amount,
        status=order.status,
        payment_method=order.payment_method,
        created_at=order.created_at.isoformat() if order.created_at else "",
    )


@router.get("/orders", summary="获取用户订单列表")
async def get_user_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> dict[str, Any]:
    """获取当前用户的订单列表"""
    orders, total = await PaymentCoreService.get_user_orders(
        db=db,
        user_id=current_user.id,
        status=status,
        page=page,
        page_size=page_size,
    )

    return {
        "items": [
            OrderResponse(
                order_no=order.order_no,
                amount=order.amount,
                status=order.status,
                payment_method=order.payment_method,
                created_at=order.created_at.isoformat() if order.created_at else "",
            )
            for order in orders
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/orders/{order_no}/cancel", summary="取消订单")
async def cancel_order(
    order_no: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    """取消待支付订单"""
    order = await PaymentCoreService.get_order_by_no(db, order_no)

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此订单")

    try:
        order = await PaymentCoreService.cancel_order(db, order)
        return OrderResponse(
            order_no=order.order_no,
            amount=order.amount,
            status=order.status,
            payment_method=order.payment_method,
            created_at=order.created_at.isoformat() if order.created_at else "",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/orders/{order_no}/query/wechat", summary="查询微信支付订单状态")
async def query_wechat_order(
    order_no: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """从微信支付平台查询订单状态"""
    order = await PaymentCoreService.get_order_by_no(db, order_no)

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此订单")

    try:
        result = await wechatpay_service.query_order(order_no)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/orders/{order_no}/query/alipay", summary="查询支付宝订单状态")
async def query_alipay_order(
    order_no: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """从支付宝平台查询订单状态"""
    order = await PaymentCoreService.get_order_by_no(db, order_no)

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此订单")

    try:
        result = await alipay_service.query_order(order_no)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
