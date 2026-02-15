"""支付宝支付服务"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...models.payment import PaymentOrder, PaymentStatus
from .core import PaymentCoreService

logger = logging.getLogger(__name__)
settings = get_settings()


class AlipayService:
    """支付宝支付服务"""

    def __init__(self):
        self.app_id = settings.alipay_app_id
        self.private_key = settings.alipay_private_key
        self.public_key = settings.alipay_public_key
        self.gateway_url = settings.alipay_gateway_url
        self.notify_url = settings.alipay_notify_url

    def _is_configured(self) -> bool:
        """检查是否已配置"""
        return all([
            self.app_id,
            self.private_key,
            self.public_key
        ])

    async def create_page_order(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        title: str,
        order_type: str = "recharge",
        description: Optional[str] = None,
        related_id: Optional[int] = None,
        related_type: Optional[str] = None,
        return_url: Optional[str] = None
    ) -> dict[str, Any]:
        """
        创建支付宝电脑网站支付订单

        Returns:
            {
                "order_no": "订单号",
                "pay_form": "HTML表单字符串"
            }
        """
        if not self._is_configured():
            raise ValueError("支付宝未配置")

        # 创建订单
        order = await PaymentCoreService.create_order(
            db=db,
            user_id=user_id,
            order_type=order_type,
            amount=amount,
            title=title,
            description=description,
            payment_method="alipay",
            related_id=related_id,
            related_type=related_type
        )

        # 构建请求参数
        biz_content = {
            "out_trade_no": order.order_no,
            "total_amount": str(amount),
            "subject": title[:256],
            "product_code": "FAST_INSTANT_TRADE_PAY"
        }

        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.page.pay",
            "format": "JSON",
            "return_url": return_url or settings.alipay_return_url or "",
            "notify_url": self.notify_url or "",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps(biz_content, ensure_ascii=False)
        }

        # 生成签名
        sign = self._generate_sign(params)
        params["sign"] = sign

        # 构建表单
        form_action = f"{self.gateway_url}?charset=utf-8"
        form_items = [f'<input type="hidden" name="{k}" value="{v}"/>' for k, v in params.items()]
        pay_form = f"""
        <form action="{form_action}" method="POST" id="alipay_form">
            {''.join(form_items)}
        </form>
        <script>document.getElementById('alipay_form').submit();</script>
        """

        return {
            "order_no": order.order_no,
            "pay_form": pay_form
        }

    async def create_wap_order(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        title: str,
        order_type: str = "recharge",
        description: Optional[str] = None,
        related_id: Optional[int] = None,
        related_type: Optional[str] = None,
        return_url: Optional[str] = None
    ) -> dict[str, Any]:
        """创建支付宝手机网站支付订单"""
        if not self._is_configured():
            raise ValueError("支付宝未配置")

        order = await PaymentCoreService.create_order(
            db=db,
            user_id=user_id,
            order_type=order_type,
            amount=amount,
            title=title,
            description=description,
            payment_method="alipay",
            related_id=related_id,
            related_type=related_type
        )

        biz_content = {
            "out_trade_no": order.order_no,
            "total_amount": str(amount),
            "subject": title[:256],
            "product_code": "QUICK_WAP_WAY"
        }

        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.wap.pay",
            "format": "JSON",
            "return_url": return_url or settings.alipay_return_url or "",
            "notify_url": self.notify_url or "",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps(biz_content, ensure_ascii=False)
        }

        sign = self._generate_sign(params)
        params["sign"] = sign

        form_action = f"{self.gateway_url}?charset=utf-8"
        form_items = [f'<input type="hidden" name="{k}" value="{v}"/>' for k, v in params.items()]
        pay_form = f"""
        <form action="{form_action}" method="POST" id="alipay_form">
            {''.join(form_items)}
        </form>
        <script>document.getElementById('alipay_form').submit();</script>
        """

        return {
            "order_no": order.order_no,
            "pay_form": pay_form
        }

    def _generate_sign(self, params: dict[str, Any]) -> str:
        """生成支付宝签名"""
        # 过滤空值和sign字段
        filtered_params = {k: v for k, v in params.items() if v is not None and k != "sign"}

        # 按字母排序
        sorted_params = sorted(filtered_params.items())

        # 构建签名字符串
        content = "&".join([f"{k}={v}" for k, v in sorted_params])

        # RSA签名
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        import base64

        private_key_obj = load_pem_private_key(self.private_key.encode(), password=None)
        signature = private_key_obj.sign(content.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())

        return base64.b64encode(signature).decode()

    def _verify_sign(self, params: dict[str, Any], sign: str) -> bool:
        """验证支付宝签名"""
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
            import base64

            # 过滤sign字段
            filtered_params = {k: v for k, v in params.items() if k != "sign"}
            sorted_params = sorted(filtered_params.items())
            content = "&".join([f"{k}={v}" for k, v in sorted_params])

            # 加载公钥
            public_key_obj = load_pem_public_key(self.public_key.encode())

            # 验证签名
            signature = base64.b64decode(sign)
            public_key_obj.verify(signature, content.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())

            return True
        except Exception as e:
            logger.error(f"Alipay signature verification failed: {e}")
            return False

    async def process_callback(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        处理支付宝回调

        Returns:
            {"success": True, "order_no": "订单号"} 或 {"success": False, "error": "错误信息"}
        """
        try:
            sign = params.get("sign")
            if not sign:
                return {"success": False, "error": "Missing sign"}

            # 验证签名
            if not self._verify_sign(params, sign):
                return {"success": False, "error": "Invalid signature"}

            # 获取订单信息
            order_no = params.get("out_trade_no")
            trade_no = params.get("trade_no")
            trade_status = params.get("trade_status")

            if trade_status in ["TRADE_SUCCESS", "TRADE_FINISHED"]:
                return {"success": True, "order_no": order_no, "trade_no": trade_no}
            else:
                return {"success": True, "order_no": order_no, "status": trade_status}

        except Exception as e:
            logger.exception("Alipay callback processing failed")
            return {"success": False, "error": str(e)}

    async def query_order(self, order_no: str) -> dict[str, Any]:
        """查询订单状态"""
        if not self._is_configured():
            raise ValueError("支付宝未配置")

        # 构建请求参数
        biz_content = {"out_trade_no": order_no}

        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.query",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps(biz_content)
        }

        params["sign"] = self._generate_sign(params)

        # 发送请求
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(self.gateway_url, data=params)

        if response.status_code != 200:
            raise Exception(f"查询订单失败: {response.text}")

        result = response.json()
        alipay_response = result.get("alipay_trade_query_response", {})

        if alipay_response.get("code") != "10000":
            raise Exception(f"查询订单失败: {alipay_response.get('msg')}")

        return {
            "order_no": alipay_response.get("out_trade_no"),
            "trade_no": alipay_response.get("trade_no"),
            "status": alipay_response.get("trade_status"),
            "amount": alipay_response.get("total_amount")
        }

    async def create_refund(
        self,
        order_no: str,
        refund_no: str,
        amount: float,
        reason: Optional[str] = None
    ) -> dict[str, Any]:
        """创建退款"""
        if not self._is_configured():
            raise ValueError("支付宝未配置")

        biz_content = {
            "out_trade_no": order_no,
            "out_request_no": refund_no,
            "refund_amount": str(amount),
            "refund_reason": reason or "用户申请退款"
        }

        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.refund",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": json.dumps(biz_content)
        }

        params["sign"] = self._generate_sign(params)

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(self.gateway_url, data=params)

        if response.status_code != 200:
            raise Exception(f"退款失败: {response.text}")

        result = response.json()
        alipay_response = result.get("alipay_trade_refund_response", {})

        if alipay_response.get("code") != "10000":
            raise Exception(f"退款失败: {alipay_response.get('msg')}")

        return {
            "refund_no": refund_no,
            "order_no": order_no,
            "refund_fee": alipay_response.get("refund_fee"),
            "gmt_refund_pay": alipay_response.get("gmt_refund_pay")
        }


# 全局实例
alipay_service = AlipayService()
