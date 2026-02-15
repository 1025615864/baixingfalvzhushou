"""支付安全工具模块"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..config import get_settings
from ..models.payment import PaymentOrder, PaymentRefund
from ..models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


class PaymentSecurityError(Exception):
    """支付安全异常"""
    pass


class PaymentRiskControl:
    """支付风控"""

    # 风控阈值配置
    MAX_DAILY_AMOUNT = 50000  # 单日最大支付金额（元）
    MAX_SINGLE_AMOUNT = 20000  # 单笔最大支付金额（元）
    MAX_HOURLY_TRANSACTIONS = 10  # 每小时最大交易次数
    MAX_DAILY_TRANSACTIONS = 50  # 单日最大交易次数
    SUSPICIOUS_IP_THRESHOLD = 5  # 同一IP可疑交易阈值

    @classmethod
    async def check_payment_risk(
        cls,
        db: AsyncSession,
        user_id: int,
        amount: float,
        ip_address: str,
        user_agent: str
    ) -> dict:
        """
        检查支付风险

        Returns:
            {"allowed": True} 或 {"allowed": False, "reason": "原因"}
        """
        # 1. 检查单笔金额限制
        if amount > cls.MAX_SINGLE_AMOUNT:
            return {
                "allowed": False,
                "reason": f"单笔支付金额不能超过{cls.MAX_SINGLE_AMOUNT}元",
                "risk_level": "high"
            }

        # 2. 检查单日金额限制
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.sum(PaymentOrder.amount))
            .where(
                PaymentOrder.user_id == user_id,
                PaymentOrder.created_at >= today,
                PaymentOrder.status.in_(["paid", "pending"])
            )
        )
        daily_amount = result.scalar() or 0

        if daily_amount + amount > cls.MAX_DAILY_AMOUNT:
            return {
                "allowed": False,
                "reason": f"今日支付金额已达上限{cls.MAX_DAILY_AMOUNT}元",
                "risk_level": "high"
            }

        # 3. 检查交易频率
        one_hour_ago = datetime.now() - timedelta(hours=1)
        result = await db.execute(
            select(func.count(PaymentOrder.id))
            .where(
                PaymentOrder.user_id == user_id,
                PaymentOrder.created_at >= one_hour_ago
            )
        )
        hourly_count = result.scalar() or 0

        if hourly_count >= cls.MAX_HOURLY_TRANSACTIONS:
            return {
                "allowed": False,
                "reason": "支付过于频繁，请稍后再试",
                "risk_level": "medium"
            }

        # 4. 检查单日交易次数
        result = await db.execute(
            select(func.count(PaymentOrder.id))
            .where(
                PaymentOrder.user_id == user_id,
                PaymentOrder.created_at >= today
            )
        )
        daily_count = result.scalar() or 0

        if daily_count >= cls.MAX_DAILY_TRANSACTIONS:
            return {
                "allowed": False,
                "reason": "今日支付次数已达上限",
                "risk_level": "medium"
            }

        # 5. 检查IP风险
        result = await db.execute(
            select(func.count(PaymentOrder.id))
            .where(
                PaymentOrder.source_ip == ip_address,
                PaymentOrder.created_at >= one_hour_ago,
                PaymentOrder.status.in_(["failed", "cancelled"])
            )
        )
        failed_count = result.scalar() or 0

        if failed_count >= cls.SUSPICIOUS_IP_THRESHOLD:
            return {
                "allowed": False,
                "reason": "检测到异常支付行为，请稍后再试",
                "risk_level": "high"
            }

        # 6. 检查User-Agent异常
        if not user_agent or len(user_agent) < 10:
            return {
                "allowed": False,
                "reason": "检测到异常请求",
                "risk_level": "medium"
            }

        return {"allowed": True, "risk_level": "low"}

    @classmethod
    async def require_additional_verification(
        cls,
        db: AsyncSession,
        user_id: int,
        amount: float
    ) -> bool:
        """判断是否需要额外验证（短信/密码）"""
        # 大额支付需要验证
        if amount >= 1000:
            return True

        # 新用户需要验证（注册7天内）
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user and user.created_at:
            days_since_registration = (datetime.now() - user.created_at).days
            if days_since_registration < 7:
                return True

        # 检查历史支付成功率
        result = await db.execute(
            select(func.count(PaymentOrder.id))
            .where(PaymentOrder.user_id == user_id)
        )
        total_orders = result.scalar() or 0

        if total_orders < 3:
            return True

        return False


class PaymentIPWhitelist:
    """支付回调IP白名单"""

    @staticmethod
    def is_alipay_ip(ip: str) -> bool:
        """检查是否为支付宝回调IP"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for network_str in settings.alipay_callback_ips:
                network = ipaddress.ip_network(network_str, strict=False)
                if ip_obj in network:
                    return True
            return False
        except ValueError:
            return False

    @staticmethod
    def is_wechatpay_ip(ip: str) -> bool:
        """检查是否为微信支付回调IP"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for network_str in settings.wechatpay_callback_ips:
                network = ipaddress.ip_network(network_str, strict=False)
                if ip_obj in network:
                    return True
            return False
        except ValueError:
            return False


class PaymentIdempotency:
    """支付幂等性控制"""

    @staticmethod
    def generate_idempotency_key(*args) -> str:
        """生成幂等性密钥"""
        content = "|".join(str(arg) for arg in args)
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    @classmethod
    async def check_duplicate_order(
        cls,
        db: AsyncSession,
        user_id: int,
        order_type: str,
        amount: float,
        related_id: Optional[int] = None,
        time_window_seconds: int = 60
    ) -> Optional[PaymentOrder]:
        """检查重复订单"""
        time_threshold = datetime.now() - timedelta(seconds=time_window_seconds)

        query = select(PaymentOrder).where(
            PaymentOrder.user_id == user_id,
            PaymentOrder.order_type == order_type,
            PaymentOrder.amount == amount,
            PaymentOrder.created_at >= time_threshold,
            PaymentOrder.status.in_(["pending", "paid"])
        )

        if related_id:
            query = query.where(PaymentOrder.related_id == related_id)

        result = await db.execute(query.order_by(PaymentOrder.created_at.desc()))
        return result.scalar_one_or_none()


class PaymentSignature:
    """支付签名工具"""

    @staticmethod
    def hmac_sign(secret: str, data: str) -> str:
        """HMAC签名"""
        return hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_hmac_sign(secret: str, data: str, signature: str) -> bool:
        """验证HMAC签名"""
        expected = PaymentSignature.hmac_sign(secret, data)
        return hmac.compare_digest(expected, signature)


class PaymentAuditLogger:
    """支付审计日志"""

    @staticmethod
    def log_payment_created(order: PaymentOrder, ip: str, user_agent: str):
        """记录支付创建日志"""
        logger.info(
            "Payment created: order_no=%s, user_id=%d, amount=%.2f, ip=%s, ua=%s",
            order.order_no, order.user_id, order.amount, ip, user_agent
        )

    @staticmethod
    def log_payment_completed(order: PaymentOrder, trade_no: str):
        """记录支付完成日志"""
        logger.info(
            "Payment completed: order_no=%s, trade_no=%s, user_id=%d, amount=%.2f",
            order.order_no, trade_no, order.user_id, order.actual_amount
        )

    @staticmethod
    def log_payment_failed(order: PaymentOrder, reason: str):
        """记录支付失败日志"""
        logger.warning(
            "Payment failed: order_no=%s, user_id=%d, amount=%.2f, reason=%s",
            order.order_no, order.user_id, order.amount, reason
        )

    @staticmethod
    def log_refund_created(refund: PaymentRefund):
        """记录退款创建日志"""
        logger.info(
            "Refund created: refund_no=%s, order_no=%s, user_id=%d, amount=%.2f",
            refund.refund_no, refund.order_no, refund.user_id, refund.amount
        )

    @staticmethod
    def log_refund_completed(refund: PaymentRefund):
        """记录退款完成日志"""
        logger.info(
            "Refund completed: refund_no=%s, order_no=%s, user_id=%d, amount=%.2f",
            refund.refund_no, refund.order_no, refund.user_id, refund.amount
        )

    @staticmethod
    def log_suspicious_activity(user_id: int, activity: str, details: dict):
        """记录可疑活动日志"""
        logger.warning(
            "Suspicious activity detected: user_id=%d, activity=%s, details=%s",
            user_id, activity, details
        )


async def validate_payment_request(
    db: AsyncSession,
    user_id: int,
    amount: float,
    ip_address: str,
    user_agent: str
) -> dict:
    """
    验证支付请求

    执行完整的风控检查，返回检查结果
    """
    # 风控检查
    risk_check = await PaymentRiskControl.check_payment_risk(
        db, user_id, amount, ip_address, user_agent
    )

    if not risk_check["allowed"]:
        PaymentAuditLogger.log_suspicious_activity(
            user_id,
            "payment_blocked",
            {"reason": risk_check["reason"], "amount": amount, "ip": ip_address}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=risk_check["reason"]
        )

    # 检查是否需要额外验证
    need_verification = await PaymentRiskControl.require_additional_verification(
        db, user_id, amount
    )

    return {
        "allowed": True,
        "risk_level": risk_check["risk_level"],
        "need_verification": need_verification
    }
