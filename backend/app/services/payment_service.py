"""支付服务 - 增强版

集成业务指标收集功能，记录支付成功率、订单转化等指标。
集成熔断器保护，防止支付服务故障导致系统崩溃。
"""
from __future__ import annotations

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.payment import BalanceTransaction, PaymentMethod, PaymentOrder, PaymentStatus, UserBalance
from ..models.lawfirm import LawyerConsultation
from .business_metrics import get_business_metrics_collector
from ..utils.circuit_breaker import (
    CircuitBreaker,
    CircuitConfig,
    CircuitBreakerOpen,
    circuit_breaker_registry,
)

logger = logging.getLogger(__name__)

# 支付服务熔断器配置
# 支付服务对稳定性要求高，设置较严格的熔断阈值
PAYMENT_CIRCUIT_CONFIG = CircuitConfig(
    failure_threshold=3,       # 连续3次失败后打开熔断器
    success_threshold=2,       # 半开状态下需要2次成功才能关闭
    timeout_seconds=30.0,      # 30秒后进入半开状态
    expected_exception=Exception,  # 捕获所有异常
)

# 全局支付服务熔断器
_payment_circuit_breaker: Optional[CircuitBreaker] = None


async def get_payment_circuit_breaker() -> CircuitBreaker:
    """获取支付服务熔断器实例"""
    global _payment_circuit_breaker
    if _payment_circuit_breaker is None:
        _payment_circuit_breaker = await circuit_breaker_registry.get_or_create(
            "payment_service",
            PAYMENT_CIRCUIT_CONFIG,
        )
    return _payment_circuit_breaker


class PaymentErrorCode(str, Enum):
    """支付错误码"""
    ORDER_NOT_FOUND = "PAYMENT_ORDER_NOT_FOUND"
    ORDER_ALREADY_PAID = "PAYMENT_ORDER_ALREADY_PAID"
    ORDER_EXPIRED = "PAYMENT_ORDER_EXPIRED"
    ORDER_CANCELLED = "PAYMENT_ORDER_CANCELLED"
    ORDER_STATUS_INVALID = "PAYMENT_ORDER_STATUS_INVALID"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    BALANCE_NOT_FOUND = "BALANCE_NOT_FOUND"
    PAYMENT_METHOD_NOT_SUPPORTED = "PAYMENT_METHOD_NOT_SUPPORTED"
    PAYMENT_METHOD_INVALID = "PAYMENT_METHOD_INVALID"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_TIMEOUT = "PAYMENT_TIMEOUT"
    PAYMENT_PROCESSING_ERROR = "PAYMENT_PROCESSING_ERROR"
    PAYMENT_CHANNEL_ERROR = "PAYMENT_CHANNEL_ERROR"
    PAYMENT_CONFIG_MISSING = "PAYMENT_CONFIG_MISSING"
    PAYMENT_CONFIG_INVALID = "PAYMENT_CONFIG_INVALID"


ERROR_SUGGESTIONS = {
    PaymentErrorCode.ORDER_NOT_FOUND: "订单不存在，请刷新页面后重试",
    PaymentErrorCode.ORDER_ALREADY_PAID: "该订单已完成支付，请查看我的订单",
    PaymentErrorCode.ORDER_EXPIRED: "订单已过期，请重新下单",
    PaymentErrorCode.ORDER_CANCELLED: "订单已取消，请重新下单",
    PaymentErrorCode.ORDER_STATUS_INVALID: "订单状态异常，请刷新页面后重试",
    PaymentErrorCode.INSUFFICIENT_BALANCE: "余额不足，请先充值或选择其他支付方式",
    PaymentErrorCode.BALANCE_NOT_FOUND: "账户异常，请联系客服处理",
    PaymentErrorCode.PAYMENT_METHOD_NOT_SUPPORTED: "该支付方式暂不支持，请选择其他支付方式",
    PaymentErrorCode.PAYMENT_METHOD_INVALID: "支付方式无效，请刷新页面后重试",
    PaymentErrorCode.PAYMENT_FAILED: "支付失败，请重试或选择其他支付方式",
    PaymentErrorCode.PAYMENT_TIMEOUT: "支付超时，请重试",
    PaymentErrorCode.PAYMENT_PROCESSING_ERROR: "系统处理异常，请稍后重试",
    PaymentErrorCode.PAYMENT_CHANNEL_ERROR: "支付通道异常，请稍后重试或联系客服",
    PaymentErrorCode.PAYMENT_CONFIG_MISSING: "支付配置异常，请联系管理员",
    PaymentErrorCode.PAYMENT_CONFIG_INVALID: "支付配置异常，请联系管理员",
}


class PaymentException(Exception):
    """支付异常基类"""
    def __init__(self, message: str, error_code: PaymentErrorCode, suggestion: Optional[str] = None, details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code
        self.suggestion = suggestion or ERROR_SUGGESTIONS.get(error_code, "请稍后重试或联系客服")
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {"message": self.message, "error_code": self.error_code.value, "suggestion": self.suggestion, "details": self.details}


class InsufficientBalanceError(PaymentException):
    """余额不足异常"""
    def __init__(self, required: float, available: float):
        super().__init__(
            message=f"余额不足，需要 {required} 元，当前可用 {available} 元",
            error_code=PaymentErrorCode.INSUFFICIENT_BALANCE,
            details={"required": required, "available": available}
        )


class PaymentCircuitOpenError(PaymentException):
    """熔断器打开异常"""
    def __init__(self):
        super().__init__(
            message="支付服务暂时不可用，请稍后重试",
            error_code=PaymentErrorCode.PAYMENT_CHANNEL_ERROR,
            suggestion="支付服务正在恢复中，请等待30秒后重试"
        )


class PaymentService:
    """支付服务 - 带熔断保护"""
    
    async def _with_circuit_breaker(
        self,
        operation: str,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs,
    ) -> Any:
        """使用熔断器包装操作
        
        Args:
            operation: 操作名称（用于日志）
            func: 要执行的函数
            fallback: 降级函数（可选）
            
        Returns:
            函数执行结果
            
        Raises:
            PaymentCircuitOpenError: 熔断器打开时抛出
        """
        cb = await get_payment_circuit_breaker()
        
        try:
            return await cb.call(func, *args, **kwargs)
        except CircuitBreakerOpen:
            logger.warning(f"Payment service circuit breaker open for operation: {operation}")
            if fallback:
                return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
            raise PaymentCircuitOpenError()

    async def create_order(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        amount: float,
        order_type: str,
        description: str | None = None,
        title: str | None = None,
    ) -> PaymentOrder:
        """创建支付订单（带熔断保护）"""
        
        async def _create():
            logger.info(f"创建支付订单: user_id={user_id}, amount={amount}, order_type={order_type}")
            order = PaymentOrder(
                order_no=str(uuid.uuid4()),
                user_id=int(user_id),
                order_type=str(order_type),
                amount=float(amount),
                actual_amount=float(amount),
                status=PaymentStatus.PENDING,
                title=title or "支付订单",
                description=description,
            )
            db.add(order)
            await db.commit()
            await db.refresh(order)
            logger.info(f"订单创建成功: order_no={order.order_no}, id={order.id}")
            return order
        
        return await self._with_circuit_breaker("create_order", _create)

    async def process_payment(
        self,
        db: AsyncSession,
        *,
        order_no: str,
        payment_method: str,
    ) -> PaymentOrder:
        logger.info(f"开始处理支付: order_no={order_no}, payment_method={payment_method}")
        
        result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == str(order_no)))
        order = result.scalar_one_or_none()
        
        if not order:
            logger.error(f"订单不存在: order_no={order_no}")
            raise PaymentException(
                message=f"订单不存在: {order_no}",
                error_code=PaymentErrorCode.ORDER_NOT_FOUND,
                details={"order_no": order_no}
            )
        
        logger.info(f"订单状态: order_no={order_no}, status={order.status}")
        
        if order.status == PaymentStatus.PAID:
            logger.info(f"订单已支付: order_no={order_no}")
            return order
        
        if order.status != PaymentStatus.PENDING:
            logger.warning(f"订单状态异常: order_no={order_no}, status={order.status}")
            raise PaymentException(
                message=f"订单状态异常: {order.status}",
                error_code=PaymentErrorCode.ORDER_STATUS_INVALID,
                details={"order_no": order_no, "status": order.status}
            )

        method = payment_method.value if hasattr(payment_method, 'value') else str(payment_method)
        
        if method == PaymentMethod.BALANCE.value:
            logger.info(f"使用余额支付: order_no={order_no}, user_id={order.user_id}")
            balance_res = await db.execute(
                select(UserBalance).where(UserBalance.user_id == int(order.user_id))
            )
            balance = balance_res.scalar_one_or_none()
            
            available_balance = float(balance.balance or 0.0) if balance else 0.0
            required_amount = float(order.actual_amount)
            
            if not balance or available_balance < required_amount:
                logger.warning(f"余额不足: user_id={order.user_id}, required={required_amount}, available={available_balance}")
                raise InsufficientBalanceError(required=required_amount, available=available_balance)
            
            before = available_balance
            balance.balance = before - required_amount
            
            transaction = BalanceTransaction(
                user_id=int(order.user_id),
                order_id=int(order.id),
                type="consume",
                amount=-required_amount,
                balance_before=before,
                balance_after=float(balance.balance),
                description=f"支付订单 {order.order_no}",
            )
            db.add(transaction)
            logger.info(f"余额扣减成功: user_id={order.user_id}, before={before}, after={balance.balance}")

        # 更新订单状态为已支付
        order.status = PaymentStatus.PAID
        order.payment_method = method
        order.paid_at = datetime.now(timezone.utc)

        logger.info(f"订单状态更新为已支付: order_no={order_no}")

        # 如果是咨询订单，更新咨询状态为confirmed
        if order.order_type == "consultation" and order.related_id:
            logger.info(f"处理咨询订单关联: order_no={order_no}, related_id={order.related_id}")
            consultation_result = await db.execute(
                select(LawyerConsultation).where(LawyerConsultation.id == order.related_id)
            )
            consultation = consultation_result.scalar_one_or_none()
            if consultation and consultation.status == "pending":
                consultation.status = "confirmed"
                logger.info(f"咨询订单状态更新: consultation_id={order.related_id}, new_status=confirmed")

        await db.commit()
        await db.refresh(order)
        logger.info(f"支付处理完成: order_no={order_no}, trade_no={order.trade_no}")
        
        # 记录支付成功指标
        collector = get_business_metrics_collector()
        collector.record_payment_success(
            order_no=order.order_no,
            amount=float(order.actual_amount),
            payment_method=method,
            order_type=order.order_type,
            user_id=order.user_id,
        )
        
        return order

    async def refund_payment(
        self,
        db: AsyncSession,
        *,
        order_no: str,
    ) -> PaymentOrder:
        """退款"""
        logger.info(f"开始处理退款: order_no={order_no}")
        
        result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == str(order_no)))
        order = result.scalar_one_or_none()
        
        if not order:
            logger.error(f"退款失败 - 订单不存在: order_no={order_no}")
            raise PaymentException(
                message=f"订单不存在: {order_no}",
                error_code=PaymentErrorCode.ORDER_NOT_FOUND,
                details={"order_no": order_no}
            )
        
        if order.status != PaymentStatus.PAID:
            logger.warning(f"退款失败 - 订单未支付或已退款: order_no={order_no}, status={order.status}")
            raise PaymentException(
                message="订单未支付或已退款",
                error_code=PaymentErrorCode.ORDER_STATUS_INVALID,
                details={"order_no": order_no, "status": order.status}
            )

        # 退款到余额
        balance_res = await db.execute(
            select(UserBalance).where(UserBalance.user_id == int(order.user_id))
        )
        balance = balance_res.scalar_one_or_none()
        
        if not balance:
            logger.error(f"退款失败 - 用户余额不存在: user_id={order.user_id}")
            raise PaymentException(
                message="用户余额不存在",
                error_code=PaymentErrorCode.BALANCE_NOT_FOUND,
                details={"user_id": order.user_id}
            )

        before = float(balance.balance)
        refund_amount = float(order.actual_amount)
        balance.balance = before + refund_amount
        
        transaction = BalanceTransaction(
            user_id=int(order.user_id),
            order_id=int(order.id),
            type="refund",
            amount=refund_amount,
            balance_before=before,
            balance_after=float(balance.balance),
            description=f"退款订单 {order.order_no}",
        )
        db.add(transaction)
        
        logger.info(f"退款成功: order_no={order_no}, amount={refund_amount}, before={before}, after={balance.balance}")

        order.status = PaymentStatus.REFUNDED
        await db.commit()
        await db.refresh(order)
        logger.info(f"退款处理完成: order_no={order_no}")
        
        # 记录退款指标
        collector = get_business_metrics_collector()
        collector.record_refund(
            order_no=order_no,
            amount=refund_amount,
            user_id=order.user_id,
        )
        
        return order


payment_service = PaymentService()
