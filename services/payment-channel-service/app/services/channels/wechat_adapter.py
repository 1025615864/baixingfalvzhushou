import hashlib
import hmac
import base64
import logging
import os
import time
import json
from typing import Any, Dict

import httpx

from .base import PaymentChannelAdapter

logger = logging.getLogger(__name__)


class WechatAdapter(PaymentChannelAdapter):

    def __init__(
        self,
        mch_id: str,
        private_key: str,
        api_v3_key: str,
        app_id: str = "",
        cert_path: str = "",
        notify_url: str = "",
    ):
        self.mch_id = mch_id
        self.private_key = private_key
        self.api_v3_key = api_v3_key
        self.app_id = app_id
        self.cert_path = cert_path
        self.notify_url = notify_url
        self.base_url = "https://api.mch.weixin.qq.com"

    def _generate_signature(self, method: str, path: str, timestamp: str, nonce: str, body: str = "") -> str:
        message = f"{method}\n{path}\n{timestamp}\n{nonce}\n{body}\n"
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend

            if self.private_key and self.private_key.startswith("-----"):
                private_key_obj = serialization.load_pem_private_key(
                    self.private_key.encode("utf-8"),
                    password=None,
                    backend=default_backend(),
                )
            else:
                private_key_obj = serialization.load_pem_private_key(
                    f"-----BEGIN PRIVATE KEY-----\n{self.private_key}\n-----END PRIVATE KEY-----".encode("utf-8"),
                    password=None,
                    backend=default_backend(),
                )

            signature = private_key_obj.sign(
                message.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return base64.b64encode(signature).decode("utf-8")
        except ImportError:
            logger.warning("cryptography package not installed, falling back to HMAC-SHA256 (not V3 compliant)")
            signature = hmac.new(
                self.api_v3_key.encode("utf-8"),
                message.encode("utf-8"),
                hashlib.sha256,
            ).digest()
            return base64.b64encode(signature).decode("utf-8")
        except Exception as e:
            logger.error(f"RSA signature generation failed: {e}")
            raise

    def _build_auth_header(self, method: str, path: str, body: str = "") -> str:
        timestamp = str(int(time.time()))
        nonce = hashlib.md5(f"{timestamp}{self.mch_id}".encode()).hexdigest()
        signature = self._generate_signature(method, path, timestamp, nonce, body)
        return f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mch_id}",nonce_str="{nonce}",timestamp="{timestamp}",serial_no="",signature="{signature}"'

    async def create_payment(
        self,
        order_no: str,
        amount: int,
        title: str,
        description: str = "",
        notify_url: str = "",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        path = "/v3/pay/transactions/native"
        body = {
            "appid": self.app_id,
            "mchid": self.mch_id,
            "description": title,
            "out_trade_no": order_no,
            "notify_url": notify_url or self.notify_url,
            "amount": {
                "total": amount,
                "currency": "CNY",
            },
        }

        body_str = json.dumps(body)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}{path}",
                    content=body_str,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": self._build_auth_header("POST", path, body_str),
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "qr_code": data.get("code_url", ""),
                        "order_no": order_no,
                        "provider": "wechat",
                    }
                else:
                    logger.error(f"Wechat create_payment failed: {response.status_code} {response.text}")
                    raise Exception(f"Wechat payment creation failed: {response.status_code}")
        except httpx.HTTPError as e:
            logger.error(f"Wechat create_payment HTTP error: {e}")
            raise
        except Exception as e:
            if "Wechat payment creation failed" in str(e):
                raise
            logger.error(f"Wechat API unavailable: {e}")
            raise

    async def verify_callback(self, payload: Dict[str, Any]) -> bool:
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend

            headers = payload.get("headers", {})
            body = payload.get("body", "")

            timestamp = headers.get("wechatpay-timestamp", "")
            nonce = headers.get("wechatpay-nonce", "")
            signature_b64 = headers.get("wechatpay-signature", "")
            serial_no = headers.get("wechatpay-serial", "")

            if not all([timestamp, nonce, signature_b64]):
                logger.warning("Missing required WeChat callback headers")
                return False

            message = f"{timestamp}\n{nonce}\n{body}\n"
            signature = base64.b64decode(signature_b64)

            wechat_public_key = os.getenv("WECHAT_PAY_PUBLIC_KEY", "")
            if not wechat_public_key:
                logger.error("WECHAT_PAY_PUBLIC_KEY not configured, cannot verify callback")
                return False

            if wechat_public_key.startswith("-----"):
                public_key_obj = serialization.load_pem_public_key(
                    wechat_public_key.encode("utf-8"),
                    backend=default_backend(),
                )
            else:
                public_key_obj = serialization.load_pem_public_key(
                    f"-----BEGIN PUBLIC KEY-----\n{wechat_public_key}\n-----END PUBLIC KEY-----".encode("utf-8"),
                    backend=default_backend(),
                )

            try:
                public_key_obj.verify(
                    signature,
                    message.encode("utf-8"),
                    padding.PKCS1v15(),
                    hashes.SHA256(),
                )
                return True
            except Exception:
                logger.exception("WeChat callback signature verification failed")
                return False
        except ImportError:
            logger.error("cryptography package not installed, cannot verify WeChat callback")
            return False
        except Exception as e:
            logger.error(f"Wechat verify_callback failed: {e}")
            return False

    async def query_payment(self, order_no: str) -> Dict[str, Any]:
        path = f"/v3/pay/transactions/out-trade-no/{order_no}?mchid={self.mch_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{path}",
                    headers={
                        "Authorization": self._build_auth_header("GET", path),
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Wechat query_payment failed: {response.status_code}")
                    return {"out_trade_no": order_no, "trade_state": "UNKNOWN"}
        except Exception as e:
            logger.warning(f"Wechat query unavailable: {e}")
            return {"out_trade_no": order_no, "trade_state": "UNKNOWN"}

    async def refund(
        self,
        order_no: str,
        refund_no: str,
        amount: int,
        total_amount: int,
        reason: str = "",
    ) -> Dict[str, Any]:
        path = "/v3/refund/domestic/refunds"
        body = {
            "out_trade_no": order_no,
            "out_refund_no": refund_no,
            "reason": reason,
            "amount": {
                "refund": amount,
                "total": total_amount,
                "currency": "CNY",
            },
        }

        body_str = json.dumps(body)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}{path}",
                    content=body_str,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": self._build_auth_header("POST", path, body_str),
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "refund_no": refund_no,
                        "order_no": order_no,
                        "success": data.get("status") in ("PROCESSING", "SUCCESS"),
                        "provider_refund_no": data.get("refund_id", ""),
                        "raw_response": data,
                    }
                else:
                    logger.error(f"Wechat refund failed: {response.status_code} {response.text}")
                    raise Exception(f"Wechat refund failed: {response.status_code}")
        except httpx.HTTPError as e:
            logger.error(f"Wechat refund HTTP error: {e}")
            raise
        except Exception as e:
            if "Wechat refund failed" in str(e):
                raise
            logger.error(f"Wechat API unavailable for refund: {e}")
            raise
