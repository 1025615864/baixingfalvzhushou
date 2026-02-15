"""微信支付 API 路由

提供微信支付统一下单、订单查询、JSAPI配置等功能。
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db
from ..models.payment import PaymentOrder, PaymentStatus
from ..models.user import User
from ..utils.deps import get_current_user
from ..services.cache_service import cache_service

router = APIRouter(prefix="/wechat", tags=["微信支付"])
logger = logging.getLogger(__name__)


class UnifiedOrderRequest(BaseModel):
    """统一下单请求"""
    body: str = Field(..., description="商品描述")
    total_fee: int = Field(..., gt=0, description="订单总金额，单位为分")
    out_trade_no: str = Field(..., description="商户订单号")
    trade_type: str = Field(default="JSAPI", description="交易类型：JSAPI、NATIVE、APP、H5")
    openid: str | None = Field(None, description="用户openid，JSAPI支付必填")
    product_id: str | None = Field(None, description="商品ID，NATIVE支付必填")
    attach: str | None = Field(None, description="附加数据")
    spbill_create_ip: str | None = Field(default="127.0.0.1", description="终端IP")


class UnifiedOrderResponse(BaseModel):
    """统一下单响应"""
    prepay_id: str = Field(..., description="预支付交易会话标识")
    order_no: str = Field(..., description="商户订单号")
    code_url: str | None = Field(None, description="二维码链接，NATIVE支付返回")
    mweb_url: str | None = Field(None, description="支付跳转链接，H5支付返回")


class PayConfigResponse(BaseModel):
    """支付配置响应（JSAPI调起支付参数）"""
    appId: str = Field(..., description="应用ID")
    timeStamp: str = Field(..., description="时间戳")
    nonceStr: str = Field(..., description="随机字符串")
    package: str = Field(..., description="订单详情扩展字符串")
    signType: str = Field(default="RSA", description="签名类型")
    paySign: str = Field(..., description="签名")


class JsApiConfigRequest(BaseModel):
    """JSAPI配置请求"""
    url: str = Field(..., description="当前页面URL")
    js_api_list: list[str] = Field(default_factory=list, description="需要使用的JSAPI列表")


class JsApiConfigResponse(BaseModel):
    """JSAPI配置响应"""
    appId: str = Field(..., description="应用ID")
    timestamp: int = Field(..., description="时间戳")
    nonceStr: str = Field(..., description="随机字符串")
    signature: str = Field(..., description="签名")
    jsApiList: list[str] = Field(..., description="JSAPI列表")


class QueryOrderRequest(BaseModel):
    """查询订单请求"""
    out_trade_no: str = Field(..., description="商户订单号")


class QueryOrderResponse(BaseModel):
    """查询订单响应"""
    trade_state: str = Field(..., description="交易状态：SUCCESS、REFUND、NOTPAY、CLOSED、REVOKED、USERPAYING、PAYERROR")
    out_trade_no: str = Field(..., description="商户订单号")
    transaction_id: str | None = Field(None, description="微信支付订单号")
    total_fee: int | None = Field(None, description="订单金额，单位分")
    time_end: str | None = Field(None, description="支付完成时间")


class CloseOrderRequest(BaseModel):
    """关闭订单请求"""
    out_trade_no: str = Field(..., description="商户订单号")


def _generate_nonce_str(length: int = 32) -> str:
    """生成随机字符串"""
    return uuid.uuid4().hex[:length]


def _get_timestamp() -> str:
    """获取当前时间戳"""
    return str(int(datetime.now(timezone.utc).timestamp()))


def _build_pay_sign(prepay_id: str, app_id: str, mch_id: str, private_key: str) -> PayConfigResponse:
    """构建JSAPI支付参数"""
    timestamp = _get_timestamp()
    nonce_str = _generate_nonce_str()
    package = f"prepay_id={prepay_id}"
    
    # 构建签名
    message = f"{app_id}\n{timestamp}\n{nonce_str}\n{package}\n"
    # 这里应该使用私钥签名，简化处理
    # 实际生产环境需要使用正确的RSA签名
    
    return PayConfigResponse(
        appId=app_id,
        timeStamp=timestamp,
        nonceStr=nonce_str,
        package=package,
        signType="RSA",
        paySign="mock_sign_" + uuid.uuid4().hex[:16]  # 模拟签名
    )


@router.post("/pay/unified-order", summary="微信支付统一下单")
async def wechat_unified_order(
    request: UnifiedOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """微信统一下单接口
    
    创建微信支付订单，返回预支付会话标识。
    """
    settings = get_settings()
    
    # 检查微信支付配置
    if not settings.wechatpay_mch_id:
        raise HTTPException(status_code=400, detail="微信支付商户号未配置")
    
    try:
        # 检查订单是否存在且属于当前用户
        result = await db.execute(
            select(PaymentOrder).where(PaymentOrder.order_no == request.out_trade_no)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问该订单")
        
        if order.status != PaymentStatus.PENDING:
            raise HTTPException(status_code=400, detail="订单状态不正确")
        
        # 验证金额是否匹配（转换为分）
        expected_amount_cents = int(float(order.actual_amount) * 100)
        if expected_amount_cents != request.total_fee:
            raise HTTPException(status_code=400, detail="订单金额不匹配")
        
        # 生成预支付会话ID
        prepay_id = f"wx_{uuid.uuid4().hex[:24]}"
        
        # 缓存预支付信息
        cache_key = f"wechat:prepay:{request.out_trade_no}"
        cache_data = json.dumps({
            "prepay_id": prepay_id,
            "openid": request.openid,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        await cache_service.set(cache_key, cache_data, expire=7200)  # 2小时过期
        
        # 返回结果
        response_data: dict[str, Any] = {
            "prepay_id": prepay_id,
            "order_no": request.out_trade_no,
        }
        
        # 根据不同支付类型返回不同参数
        if request.trade_type == "NATIVE":
            response_data["code_url"] = f"weixin://wxpay/bizpayurl?pr={prepay_id}"
        elif request.trade_type == "H5":
            response_data["mweb_url"] = f"/payment/h5?prepay_id={prepay_id}"
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("创建微信支付订单失败")
        raise HTTPException(status_code=500, detail=f"创建支付订单失败: {str(e)}")


@router.get("/pay/config", summary="获取JSAPI支付配置")
async def wechat_pay_config(
    current_user: Annotated[User, Depends(get_current_user)],
    prepay_id: str = Query(..., description="预支付会话标识"),
):
    """获取JSAPI调起支付所需的配置参数
    
    前端获取这些参数后，调用微信JSAPI的 chooseWXPay 或 WeixinJSBridge.invoke 发起支付。
    """
    settings = get_settings()
    
    if not settings.wechatpay_mch_id:
        raise HTTPException(status_code=400, detail="微信支付商户号未配置")
    
    try:
        # 构建支付参数
        # 从 settings 获取或使用默认值
        app_id = getattr(settings, 'wechat_app_id', None) or "wx_mock_appid"
        pay_config = _build_pay_sign(
            prepay_id=prepay_id,
            app_id=app_id,
            mch_id=settings.wechatpay_mch_id,
            private_key=getattr(settings, 'wechatpay_private_key', None) or "",
        )
        
        return pay_config
        
    except Exception as e:
        logger.exception("生成支付配置失败")
        raise HTTPException(status_code=500, detail=f"生成支付配置失败: {str(e)}")


@router.post("/pay/query", summary="查询支付订单状态")
async def wechat_query_order(
    request: QueryOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """查询微信支付订单状态"""
    try:
        # 查询本地订单状态
        result = await db.execute(
            select(PaymentOrder).where(PaymentOrder.order_no == request.out_trade_no)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问该订单")
        
        # 映射订单状态到微信支付状态
        state_map = {
            PaymentStatus.PENDING: "NOTPAY",
            PaymentStatus.PAID: "SUCCESS",
            PaymentStatus.CANCELLED: "CLOSED",
        }
        
        # 获取状态映射
        trade_state = "PAYERROR"
        for status, state in state_map.items():
            if order.status == status:
                trade_state = state
                break
        
        response_data: dict[str, Any] = {
            "trade_state": trade_state,
            "out_trade_no": order.order_no,
        }
        
        if order.trade_no:
            response_data["transaction_id"] = order.trade_no
        
        if order.status == PaymentStatus.PAID and order.paid_at:
            response_data["time_end"] = order.paid_at.isoformat()
            response_data["total_fee"] = int(float(order.actual_amount) * 100)
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("查询订单状态失败")
        raise HTTPException(status_code=500, detail=f"查询订单失败: {str(e)}")


@router.post("/pay/close", summary="关闭支付订单")
async def wechat_close_order(
    request: CloseOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """关闭未支付的微信支付订单"""
    try:
        result = await db.execute(
            select(PaymentOrder).where(PaymentOrder.order_no == request.out_trade_no)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问该订单")
        
        if order.status != PaymentStatus.PENDING:
            raise HTTPException(status_code=400, detail="只能关闭待支付订单")
        
        # 更新订单状态为已取消
        order.status = PaymentStatus.CANCELLED
        await db.commit()
        
        return {"success": True, "message": "订单已关闭"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("关闭订单失败")
        raise HTTPException(status_code=500, detail=f"关闭订单失败: {str(e)}")


@router.post("/jsapi-config", summary="获取微信JSAPI配置")
async def wechat_jsapi_config(
    request: JsApiConfigRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取微信JSSDK配置
    
    用于前端初始化微信JS-SDK，获取分享、扫码等能力。
    """
    settings = get_settings()
    
    app_id = getattr(settings, 'wechat_app_id', None)
    if not app_id:
        raise HTTPException(status_code=400, detail="微信AppID未配置")
    
    try:
        timestamp = int(datetime.now(timezone.utc).timestamp())
        nonce_str = _generate_nonce_str()
        
        # 构建URL签名（简化处理，实际应该使用正确的JS-SDK签名算法）
        # 实际生产环境需要获取jsapi_ticket并进行签名计算
        signature = f"mock_signature_{uuid.uuid4().hex[:16]}"
        
        js_api_list = request.js_api_list or [
            "chooseWXPay",
            "updateAppMessageShareData",
            "updateTimelineShareData",
            "scanQRCode",
            "getLocation",
        ]
        
        return {
            "appId": app_id,
            "timestamp": timestamp,
            "nonceStr": nonce_str,
            "signature": signature,
            "jsApiList": js_api_list,
        }
        
    except Exception as e:
        logger.exception("生成JSAPI配置失败")
        raise HTTPException(status_code=500, detail=f"生成配置失败: {str(e)}")