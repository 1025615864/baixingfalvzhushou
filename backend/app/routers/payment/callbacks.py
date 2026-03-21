"""支付回调路由"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...database import get_db
from ...models.payment import PaymentCallbackEvent, PaymentOrder, PaymentStatus, RefundStatus, PaymentRefund
from ...services.payment import PaymentCoreService, wechatpay_service, alipay_service
from ...config import get_settings
from ...utils.ip_whitelist import validate_callback_ip

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/callbacks/wechat", summary="微信支付回调")
async def wechat_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """
    微信支付回调接口
    
    微信会在支付成功后主动调用此接口通知支付结果
    """
    # 验证来源IP
    client_ip = request.client.host if request.client else None
    if not validate_callback_ip(client_ip, "wechat"):
        logger.warning(f"微信支付回调IP验证失败: {client_ip}")
        # 返回成功避免微信重试，但记录安全事件
        return Response(
            content='{"code": "SUCCESS", "message": "OK"}',
            media_type="application/json"
        )
    
    # 获取请求头
    headers = {
        "Wechatpay-Serial": request.headers.get("Wechatpay-Serial", ""),
        "Wechatpay-Timestamp": request.headers.get("Wechatpay-Timestamp", ""),
        "Wechatpay-Nonce": request.headers.get("Wechatpay-Nonce", ""),
        "Wechatpay-Signature": request.headers.get("Wechatpay-Signature", ""),
    }
    
    # 获取请求体
    body = await request.body()
    
    # 记录回调事件
    callback_event = PaymentCallbackEvent(
        provider="wechat",
        raw_payload=body.decode("utf-8") if body else None,
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(callback_event)
    await db.flush()
    
    try:
        # 处理回调
        result = await wechatpay_service.process_callback(db, headers, body)
        
        # 更新回调事件状态
        callback_event.verified = result.get("success", False)
        if not result.get("success"):
            callback_event.error_message = result.get("error")
        else:
            callback_event.order_no = result.get("order_no")
        
        await db.commit()
        
        if result.get("success"):
            # 返回成功响应给微信
            return Response(
                content='{"code": "SUCCESS", "message": "OK"}',
                media_type="application/json"
            )
        else:
            logger.error(f"Wechat callback processing failed: {result.get('error')}")
            # 仍然返回成功，避免微信重试
            return Response(
                content='{"code": "SUCCESS", "message": "OK"}',
                media_type="application/json"
            )
    
    except Exception as e:
        logger.exception("Wechat callback exception")
        callback_event.error_message = str(e)
        await db.commit()
        
        # 返回成功，避免微信重试
        return Response(
            content='{"code": "SUCCESS", "message": "OK"}',
            media_type="application/json"
        )


@router.post("/callbacks/alipay", summary="支付宝回调")
async def alipay_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """
    支付宝回调接口
    
    支付宝会在支付成功后主动调用此接口通知支付结果
    """
    # 验证来源IP
    client_ip = request.client.host if request.client else None
    if not validate_callback_ip(client_ip, "alipay"):
        logger.warning(f"支付宝回调IP验证失败: {client_ip}")
        # 返回成功避免支付宝重试，但记录安全事件
        return Response(content="success")
    
    # 获取表单数据
    form_data = await request.form()
    params = dict(form_data)
    
    # 记录回调事件
    callback_event = PaymentCallbackEvent(
        provider="alipay",
        raw_payload=str(params),
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(callback_event)
    await db.flush()
    
    try:
        # 处理回调
        result = await alipay_service.process_callback(params)
        
        # 更新回调事件状态
        callback_event.verified = result.get("success", False)
        if not result.get("success"):
            callback_event.error_message = result.get("error")
        else:
            callback_event.order_no = result.get("order_no")
            callback_event.trade_no = result.get("trade_no")
        
        await db.commit()
        
        if result.get("success"):
            order_no = result.get("order_no")
            trade_no = result.get("trade_no")
            callback_amount = result.get("amount")  # 支付宝回调金额（元）

            # 查找订单
            order = await PaymentCoreService.get_order_by_no(db, order_no)
            if not order:
                logger.warning(f"Order not found for Alipay callback: {order_no}")
                return Response(content="success")

            # 检查订单是否已支付（幂等处理）
            if order.status == PaymentStatus.PAID:
                logger.info(f"Order already paid (idempotent): {order_no}")
                return Response(content="success")

            # 安全检查：验证回调金额与订单金额一致
            if callback_amount is not None:
                order_amount = order.actual_amount
                # 允许 0.01 元的浮点数误差
                if abs(callback_amount - order_amount) > 0.01:
                    logger.error(
                        "Alipay amount mismatch: order_no=%s, callback=%s, order=%s",
                        order_no, callback_amount, order_amount
                    )
                    # 记录异常但返回 success 避免重试
                    return Response(content="success")

            try:
                await PaymentCoreService.mark_order_paid(db, order, trade_no)
            except ValueError as e:
                # 订单已被其他请求处理，这是正常的幂等情况
                logger.info(f"Order payment race condition handled: {order_no}, {e}")
                return Response(content="success")

            # 如果是充值订单，充值余额
            if order.order_type == "recharge":
                await PaymentCoreService.recharge_balance(
                    db=db,
                    user_id=order.user_id,
                    amount=order.actual_amount,
                    order_id=order.id,
                    description=f"支付宝支付充值"
                )
            
            # 返回成功响应给支付宝
            return Response(content="success")
        else:
            logger.error(f"Alipay callback processing failed: {result.get('error')}")
            return Response(content="success")  # 仍然返回success避免支付宝重试
    
    except Exception as e:
        logger.exception("Alipay callback exception")
        callback_event.error_message = str(e)
        await db.commit()
        
        return Response(content="success")  # 返回success避免支付宝重试


@router.post("/callbacks/wechat/refund", summary="微信退款回调")
async def wechat_refund_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """微信退款回调接口"""
    # 验证来源IP
    client_ip = request.client.host if request.client else None
    if not validate_callback_ip(client_ip, "wechat"):
        logger.warning(f"微信退款回调IP验证失败: {client_ip}")
        return Response(
            content='{"code": "SUCCESS", "message": "OK"}',
            media_type="application/json"
        )

    # 获取请求头
    headers = {
        "Wechatpay-Serial": request.headers.get("Wechatpay-Serial", ""),
        "Wechatpay-Timestamp": request.headers.get("Wechatpay-Timestamp", ""),
        "Wechatpay-Nonce": request.headers.get("Wechatpay-Nonce", ""),
        "Wechatpay-Signature": request.headers.get("Wechatpay-Signature", ""),
    }

    # 获取请求体
    body = await request.body()

    # 记录回调事件
    callback_event = PaymentCallbackEvent(
        provider="wechat_refund",
        raw_payload=body.decode("utf-8") if body else None,
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(callback_event)
    await db.flush()

    try:
        # 处理回调（验证签名并解密数据）
        result = await wechatpay_service.process_callback(db, headers, body)

        # 更新回调事件状态
        callback_event.verified = result.get("success", False)
        if not result.get("success"):
            callback_event.error_message = result.get("error")
        else:
            callback_event.order_no = result.get("order_no")

        await db.commit()

        if not result.get("success"):
            logger.error(f"Wechat refund callback processing failed: {result.get('error')}")
            return Response(
                content='{"code": "SUCCESS", "message": "OK"}',
                media_type="application/json"
            )

        # 解密后的数据在 result 中
        from ...utils.wechatpay_v3 import wechatpay_decrypt_resource

        # 重新解析body获取resource进行解密
        callback_data = json.loads(body)
        resource = callback_data.get("resource", {})

        decrypted_data = wechatpay_decrypt_resource(
            api_v3_key=wechatpay_service.api_v3_key,
            nonce=resource.get("nonce"),
            associated_data=resource.get("associated_data"),
            ciphertext=resource.get("ciphertext")
        )

        refund_data = json.loads(decrypted_data)

        # 获取退款信息
        out_refund_no = refund_data.get("out_refund_no")
        refund_status = refund_data.get("refund_status")
        refund_trade_no = refund_data.get("refund_id")

        # 查找退款记录
        refund_result = await db.execute(
            select(PaymentRefund).where(PaymentRefund.refund_no == out_refund_no)
        )
        refund_record = refund_result.scalar_one_or_none()

        if not refund_record:
            logger.warning(f"Refund record not found: {out_refund_no}")
            return Response(
                content='{"code": "SUCCESS", "message": "OK"}',
                media_type="application/json"
            )

        # 更新退款状态
        if refund_status == "SUCCESS":
            refund_record.status = RefundStatus.SUCCESS
            refund_record.refund_trade_no = refund_trade_no
            refund_record.processed_at = datetime.now()

            # 如果是充值订单退款，扣减用户余额
            order = await PaymentCoreService.get_order_by_no(db, refund_record.order_no)
            if order and order.order_type == "recharge":
                try:
                    await PaymentCoreService.deduct_balance_for_refund(
                        db=db,
                        user_id=order.user_id,
                        amount=refund_record.amount,
                        order_id=order.id,
                        description=f"微信退款-充值订单退款"
                    )
                except ValueError as e:
                    logger.warning(f"Failed to deduct balance for refund: {e}")
                    # 余额不足时仍标记退款成功，但记录警告

            logger.info(f"Refund success: {out_refund_no}")
        else:
            refund_record.status = RefundStatus.FAILED
            refund_record.error_message = f"Refund status: {refund_status}"
            logger.warning(f"Refund failed: {out_refund_no}, status: {refund_status}")

        await db.commit()

        return Response(
            content='{"code": "SUCCESS", "message": "OK"}',
            media_type="application/json"
        )

    except Exception as e:
        logger.exception("Wechat refund callback exception")
        callback_event.error_message = str(e)
        await db.commit()

        return Response(
            content='{"code": "SUCCESS", "message": "OK"}',
            media_type="application/json"
        )


@router.post("/callbacks/alipay/refund", summary="支付宝退款回调")
async def alipay_refund_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """支付宝退款回调接口

    支付宝退款通常是同步返回结果，但需要支持异步通知
    """
    # 验证来源IP
    client_ip = request.client.host if request.client else None
    if not validate_callback_ip(client_ip, "alipay"):
        logger.warning(f"支付宝退款回调IP验证失败: {client_ip}")
        return Response(content="success")

    # 获取表单数据
    form_data = await request.form()
    params = dict(form_data)

    # 记录回调事件
    callback_event = PaymentCallbackEvent(
        provider="alipay_refund",
        raw_payload=str(params),
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(callback_event)
    await db.flush()

    try:
        # 处理回调（验证签名）
        result = await alipay_service.process_callback(params)

        # 更新回调事件状态
        callback_event.verified = result.get("success", False)
        if not result.get("success"):
            callback_event.error_message = result.get("error")
        else:
            callback_event.order_no = result.get("order_no")
            callback_event.trade_no = result.get("trade_no")

        await db.commit()

        if not result.get("success"):
            logger.error(f"Alipay refund callback processing failed: {result.get('error')}")
            return Response(content="success")

        # 获取退款相关参数
        # 支付宝退款回调参数：
        # - out_request_no: 退款请求号（对应我们的 refund_no）
        # - out_trade_no: 商户订单号
        # - trade_no: 支付宝交易号
        # - refund_fee: 退款金额
        # - gmt_refund: 退款时间
        # - refund_status: 退款状态（REFUND_SUCCESS）
        out_request_no = params.get("out_request_no")
        refund_status = params.get("refund_status")
        refund_fee = params.get("refund_fee")

        if not out_request_no:
            logger.warning("Alipay refund callback missing out_request_no")
            return Response(content="success")

        # 查找退款记录
        refund_result = await db.execute(
            select(PaymentRefund).where(PaymentRefund.refund_no == out_request_no)
        )
        refund_record = refund_result.scalar_one_or_none()

        if not refund_record:
            logger.warning(f"Refund record not found: {out_request_no}")
            return Response(content="success")

        # 更新退款状态
        if refund_status == "REFUND_SUCCESS":
            refund_record.status = RefundStatus.SUCCESS
            refund_record.processed_at = datetime.now()

            # 如果是充值订单退款，扣减用户余额
            order = await PaymentCoreService.get_order_by_no(db, refund_record.order_no)
            if order and order.order_type == "recharge":
                try:
                    await PaymentCoreService.deduct_balance_for_refund(
                        db=db,
                        user_id=order.user_id,
                        amount=refund_record.amount,
                        order_id=order.id,
                        description=f"支付宝退款-充值订单退款"
                    )
                except ValueError as e:
                    logger.warning(f"Failed to deduct balance for refund: {e}")
                    # 余额不足时仍标记退款成功，但记录警告

            logger.info(f"Alipay refund success: {out_request_no}")
        else:
            refund_record.status = RefundStatus.FAILED
            refund_record.error_message = f"Refund status: {refund_status}"
            logger.warning(f"Alipay refund failed: {out_request_no}, status: {refund_status}")

        await db.commit()

        return Response(content="success")

    except Exception as e:
        logger.exception("Alipay refund callback exception")
        callback_event.error_message = str(e)
        await db.commit()

        return Response(content="success")
