"""微信支付服务"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...models.payment import PaymentOrder, PaymentStatus
from ...utils.wechatpay_v3 import (
    wechatpay_build_authorization,
    wechatpay_decrypt_resource,
    wechatpay_verify_signature,
    fetch_platform_certificates,
    WeChatPayPlatformCert,
)
from .core import PaymentCoreService

logger = logging.getLogger(__name__)
settings = get_settings()


class WechatPayService:
    """微信支付V3服务"""

    def __init__(self):
        self.mch_id = settings.wechatpay_mch_id
        self.mch_serial_no = settings.wechatpay_mch_serial_no
        self.private_key = settings.wechatpay_private_key
        self.api_v3_key = settings.wechatpay_api_v3_key
        self.base_url = "https://api.mch.weixin.qq.com"

    def _is_configured(self) -> bool:
        """检查是否已配置"""
        return all([
            self.mch_id,
            self.mch_serial_no,
            self.private_key,
            self.api_v3_key
        ])

    async def create_jsapi_order(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        title: str,
        openid: str,
        order_type: str = "recharge",
        description: Optional[str] = None,
        related_id: Optional[int] = None,
        related_type: Optional[str] = None
    ) -> dict[str, Any]:
        """
        创建微信支付JSAPI订单

        Args:
            openid: 用户在微信的openid

        Returns:
            {
                "order_no": "订单号",
                "prepay_id": "预支付交易会话标识",
                "appId": "应用ID",
                "timeStamp": "时间戳",
                "nonceStr": "随机字符串",
                "package": "订单详情扩展字符串",
                "signType": "签名方式",
                "paySign": "支付签名"
            }
        """
        if not self._is_configured():
            raise ValueError("微信支付未配置")

        # 创建订单
        order = await PaymentCoreService.create_order(
            db=db,
            user_id=user_id,
            order_type=order_type,
            amount=amount,
            title=title,
            description=description,
            payment_method="wechat",
            related_id=related_id,
            related_type=related_type
        )

        # 调用微信支付API
        url = f"{self.base_url}/v3/pay/transactions/jsapi"

        body = {
            "mchid": self.mch_id,
            "out_trade_no": order.order_no,
            "appid": settings.wechat_app_id if hasattr(settings, 'wechat_app_id') else "",
            "description": title[:60],  # 商品描述，最长60字符
            "notify_url": settings.wechatpay_notify_url or "",
            "amount": {
                "total": int(amount * 100),  # 金额转换为分
                "currency": "CNY"
            },
            "payer": {
                "openid": openid
            }
        }

        body_json = json.dumps(body, ensure_ascii=False)

        authorization = wechatpay_build_authorization(
            mch_id=self.mch_id,
            serial_no=self.mch_serial_no,
            private_key_pem=self.private_key,
            method="POST",
            url_path="/v3/pay/transactions/jsapi",
            body=body_json
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, content=body_json)

        if response.status_code != 200:
            logger.error(f"WechatPay create order failed: {response.text}")
            raise Exception(f"微信支付下单失败: {response.text}")

        result = response.json()
        prepay_id = result.get("prepay_id")

        # 生成前端调起支付所需的参数
        timestamp = str(int(datetime.now().timestamp()))
        nonce_str = uuid.uuid4().hex[:32]
        package = f"prepay_id={prepay_id}"

        # 构建支付签名
        sign_message = f"{settings.wechat_app_id}\n{timestamp}\n{nonce_str}\n{package}\n"
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        private_key_obj = load_pem_private_key(self.private_key.encode(), password=None)
        signature = private_key_obj.sign(sign_message.encode(), padding.PKCS1v15(), hashes.SHA256())
        import base64
        pay_sign = base64.b64encode(signature).decode()

        return {
            "order_no": order.order_no,
            "prepay_id": prepay_id,
            "appId": settings.wechat_app_id if hasattr(settings, 'wechat_app_id') else "",
            "timeStamp": timestamp,
            "nonceStr": nonce_str,
            "package": package,
            "signType": "RSA",
            "paySign": pay_sign
        }

    async def create_native_order(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        title: str,
        order_type: str = "recharge",
        description: Optional[str] = None,
        related_id: Optional[int] = None,
        related_type: Optional[str] = None
    ) -> dict[str, Any]:
        """
        创建微信支付Native订单（扫码支付）

        Returns:
            {
                "order_no": "订单号",
                "code_url": "二维码链接"
            }
        """
        if not self._is_configured():
            raise ValueError("微信支付未配置")

        # 创建订单
        order = await PaymentCoreService.create_order(
            db=db,
            user_id=user_id,
            order_type=order_type,
            amount=amount,
            title=title,
            description=description,
            payment_method="wechat",
            related_id=related_id,
            related_type=related_type
        )

        url = f"{self.base_url}/v3/pay/transactions/native"

        body = {
            "mchid": self.mch_id,
            "out_trade_no": order.order_no,
            "appid": settings.wechat_app_id if hasattr(settings, 'wechat_app_id') else "",
            "description": title[:60],
            "notify_url": settings.wechatpay_notify_url or "",
            "amount": {
                "total": int(amount * 100),
                "currency": "CNY"
            }
        }

        body_json = json.dumps(body, ensure_ascii=False)

        authorization = wechatpay_build_authorization(
            mch_id=self.mch_id,
            serial_no=self.mch_serial_no,
            private_key_pem=self.private_key,
            method="POST",
            url_path="/v3/pay/transactions/native",
            body=body_json
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, content=body_json)

        if response.status_code != 200:
            logger.error(f"WechatPay native order failed: {response.text}")
            raise Exception(f"微信支付Native下单失败: {response.text}")

        result = response.json()
        code_url = result.get("code_url")

        return {
            "order_no": order.order_no,
            "code_url": code_url
        }

    async def query_order(self, order_no: str) -> dict[str, Any]:
        """查询订单状态"""
        if not self._is_configured():
            raise ValueError("微信支付未配置")

        url = f"{self.base_url}/v3/pay/transactions/out-trade-no/{order_no}"

        authorization = wechatpay_build_authorization(
            mch_id=self.mch_id,
            serial_no=self.mch_serial_no,
            private_key_pem=self.private_key,
            method="GET",
            url_path=f"/v3/pay/transactions/out-trade-no/{order_no}",
            body=""
        )

        headers = {
            "Authorization": authorization,
            "Accept": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 404:
            return {"status": "NOT_FOUND"}

        if response.status_code != 200:
            logger.error(f"WechatPay query order failed: {response.text}")
            raise Exception(f"查询订单失败: {response.text}")

        return response.json()

    async def close_order(self, order_no: str) -> bool:
        """关闭订单"""
        if not self._is_configured():
            raise ValueError("微信支付未配置")

        url = f"{self.base_url}/v3/pay/transactions/out-trade-no/{order_no}/close"

        body = json.dumps({"mchid": self.mch_id})

        authorization = wechatpay_build_authorization(
            mch_id=self.mch_id,
            serial_no=self.mch_serial_no,
            private_key_pem=self.private_key,
            method="POST",
            url_path=f"/v3/pay/transactions/out-trade-no/{order_no}/close",
            body=body
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, content=body)

        return response.status_code == 204

    async def process_callback(
        self,
        db: AsyncSession,
        headers: dict[str, str],
        body: bytes
    ) -> dict[str, Any]:
        """
        处理微信支付回调

        Returns:
            {"success": True, "order_no": "订单号"} 或 {"success": False, "error": "错误信息"}
        """
        try:
            # 验证签名
            wechatpay_serial = headers.get("Wechatpay-Serial")
            wechatpay_timestamp = headers.get("Wechatpay-Timestamp")
            wechatpay_nonce = headers.get("Wechatpay-Nonce")
            wechatpay_signature = headers.get("Wechatpay-Signature")

            if not all([wechatpay_serial, wechatpay_timestamp, wechatpay_nonce, wechatpay_signature]):
                return {"success": False, "error": "Missing required headers"}

            # 获取平台证书并验证签名
            certs = await fetch_platform_certificates(
                certificates_url=settings.wechatpay_certificates_url,
                mch_id=self.mch_id,
                mch_serial_no=self.mch_serial_no,
                mch_private_key_pem=self.private_key,
                api_v3_key=self.api_v3_key
            )

            # 找到对应的证书
            cert = None
            for c in certs:
                if c.serial_no == wechatpay_serial:
                    cert = c
                    break

            if not cert:
                return {"success": False, "error": "Certificate not found"}

            # 验证签名
            is_valid = wechatpay_verify_signature(
                cert_pem=cert.pem,
                timestamp=wechatpay_timestamp,
                nonce=wechatpay_nonce,
                body=body,
                signature_b64=wechatpay_signature
            )

            if not is_valid:
                return {"success": False, "error": "Invalid signature"}

            # 解析回调数据
            callback_data = json.loads(body)
            resource = callback_data.get("resource", {})

            # 解密资源
            decrypted_data = wechatpay_decrypt_resource(
                api_v3_key=self.api_v3_key,
                nonce=resource.get("nonce"),
                associated_data=resource.get("associated_data"),
                ciphertext=resource.get("ciphertext")
            )

            payment_data = json.loads(decrypted_data)

            # 处理支付结果
            order_no = payment_data.get("out_trade_no")
            trade_no = payment_data.get("transaction_id")
            trade_state = payment_data.get("trade_state")

            if trade_state == "SUCCESS":
                # 查找订单并标记为已支付
                order = await PaymentCoreService.get_order_by_no(db, order_no)
                if order and order.status == PaymentStatus.PENDING:
                    success_time = payment_data.get("success_time")
                    paid_at = datetime.fromisoformat(success_time.replace("Z", "+00:00")) if success_time else None

                    await PaymentCoreService.mark_order_paid(db, order, trade_no, paid_at)

                    # 如果是充值订单，充值余额
                    if order.order_type == "recharge":
                        await PaymentCoreService.recharge_balance(
                            db=db,
                            user_id=order.user_id,
                            amount=order.actual_amount,
                            order_id=order.id,
                            description=f"微信支付充值"
                        )

                return {"success": True, "order_no": order_no}
            else:
                return {"success": True, "order_no": order_no, "status": trade_state}

        except Exception as e:
            logger.exception("WechatPay callback processing failed")
            return {"success": False, "error": str(e)}

    async def create_refund(
        self,
        db: AsyncSession,
        order_no: str,
        refund_no: str,
        amount: float,
        reason: Optional[str] = None
    ) -> dict[str, Any]:
        """创建退款"""
        if not self._is_configured():
            raise ValueError("微信支付未配置")

        url = f"{self.base_url}/v3/refund/domestic/refunds"

        body = {
            "out_trade_no": order_no,
            "out_refund_no": refund_no,
            "reason": reason or "用户申请退款",
            "amount": {
                "refund": int(amount * 100),
                "total": int(amount * 100),
                "currency": "CNY"
            }
        }

        body_json = json.dumps(body, ensure_ascii=False)

        authorization = wechatpay_build_authorization(
            mch_id=self.mch_id,
            serial_no=self.mch_serial_no,
            private_key_pem=self.private_key,
            method="POST",
            url_path="/v3/refund/domestic/refunds",
            body=body_json
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, content=body_json)

        if response.status_code != 200:
            logger.error(f"WechatPay refund failed: {response.text}")
            raise Exception(f"微信退款失败: {response.text}")

        return response.json()


# 全局实例
wechatpay_service = WechatPayService()
