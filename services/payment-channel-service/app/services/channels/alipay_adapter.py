import logging
from typing import Any, Dict

from .base import PaymentChannelAdapter

logger = logging.getLogger(__name__)


class AlipayAdapter(PaymentChannelAdapter):

    def __init__(
        self,
        app_id: str,
        private_key: str,
        public_key: str,
        gateway_url: str = "https://openapi.alipay.com/gateway.do",
        notify_url: str = "",
    ):
        self.app_id = app_id
        self.private_key = private_key
        self.public_key = public_key
        self.gateway_url = gateway_url
        self.notify_url = notify_url

    async def create_payment(
        self,
        order_no: str,
        amount: int,
        title: str,
        description: str = "",
        notify_url: str = "",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            from alipay import AliPay

            alipay_client = AliPay(
                appid=self.app_id,
                app_private_key_string=self.private_key,
                alipay_public_key_string=self.public_key,
                sign_type="RSA2",
                debug=self.gateway_url.find("openapi") == -1,
            )

            order_string = alipay_client.api_alipay_trade_page_pay(
                out_trade_no=order_no,
                total_amount=str(amount / 100),
                subject=title,
                body=description or title,
                notify_url=notify_url or self.notify_url,
                return_url=kwargs.get("return_url", ""),
            )

            payment_url = f"{self.gateway_url}?{order_string}"

            return {
                "payment_url": payment_url,
                "order_no": order_no,
                "provider": "alipay",
            }
        except ImportError:
            logger.error("alipay-sdk-python not installed, cannot create payment")
            raise RuntimeError("alipay-sdk-python is required for Alipay payments")
        except Exception as e:
            logger.error(f"Alipay create_payment failed: {e}")
            raise

    async def verify_callback(self, payload: Dict[str, Any]) -> bool:
        try:
            from alipay import AliPay

            alipay_client = AliPay(
                appid=self.app_id,
                app_private_key_string=self.private_key,
                alipay_public_key_string=self.public_key,
                sign_type="RSA2",
                debug=self.gateway_url.find("openapi") == -1,
            )

            sign = payload.pop("sign", None)
            sign_type = payload.pop("sign_type", None)

            is_valid = alipay_client.verify(payload, sign)
            if sign is not None:
                payload["sign"] = sign
            if sign_type is not None:
                payload["sign_type"] = sign_type

            return is_valid
        except ImportError:
            logger.error("alipay-sdk-python not installed, cannot verify callback - REJECTING")
            return False
        except Exception as e:
            logger.error(f"Alipay verify_callback failed: {e}")
            return False

    async def query_payment(self, order_no: str) -> Dict[str, Any]:
        try:
            from alipay import AliPay

            alipay_client = AliPay(
                appid=self.app_id,
                app_private_key_string=self.private_key,
                alipay_public_key_string=self.public_key,
                sign_type="RSA2",
                debug=self.gateway_url.find("openapi") == -1,
            )

            result = alipay_client.api_alipay_trade_query(out_trade_no=order_no)
            return result
        except ImportError:
            logger.warning("alipay-sdk-python not installed, returning mock query")
            return {"out_trade_no": order_no, "trade_status": "UNKNOWN"}
        except Exception as e:
            logger.error(f"Alipay query_payment failed: {e}")
            raise

    async def refund(
        self,
        order_no: str,
        refund_no: str,
        amount: int,
        total_amount: int,
        reason: str = "",
    ) -> Dict[str, Any]:
        try:
            from alipay import AliPay

            alipay_client = AliPay(
                appid=self.app_id,
                app_private_key_string=self.private_key,
                alipay_public_key_string=self.public_key,
                sign_type="RSA2",
                debug=self.gateway_url.find("openapi") == -1,
            )

            result = alipay_client.api_alipay_trade_refund(
                out_trade_no=order_no,
                refund_amount=str(amount / 100),
                out_request_no=refund_no,
                refund_reason=reason,
            )

            success = result.get("code") == "10000"

            return {
                "refund_no": refund_no,
                "order_no": order_no,
                "success": success,
                "provider_refund_no": result.get("trade_no", ""),
                "raw_response": result,
            }
        except ImportError:
            logger.error("alipay-sdk-python not installed, cannot process refund")
            raise RuntimeError("alipay-sdk-python is required for Alipay refunds")
        except Exception as e:
            logger.error(f"Alipay refund failed: {e}")
            raise
