import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class SmsService:
    def __init__(self):
        self.provider = os.getenv("SMS_PROVIDER", "")
        self.access_key_id = os.getenv("SMS_ACCESS_KEY_ID", "")
        self.access_key_secret = os.getenv("SMS_ACCESS_KEY_SECRET", "")
        self.sign_name = os.getenv("SMS_SIGN_NAME", "")
        self.template_code = os.getenv("SMS_TEMPLATE_CODE", "")
        self._enabled = bool(self.provider and self.access_key_id)

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    async def send_sms(
        self,
        phone: str,
        template_code: Optional[str] = None,
        template_params: Optional[dict] = None,
    ) -> bool:
        if not self._enabled:
            logger.info(f"SMS disabled, would send to {phone}")
            return False

        code = template_code or self.template_code
        if not code:
            logger.warning("SMS template code not configured")
            return False

        try:
            if self.provider == "aliyun":
                return await self._send_aliyun_sms(phone, code, template_params or {})
            elif self.provider == "tencent":
                return await self._send_tencent_sms(phone, code, template_params or {})
            else:
                logger.warning(f"Unknown SMS provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False

    async def _send_aliyun_sms(
        self, phone: str, template_code: str, template_params: dict
    ) -> bool:
        try:
            import httpx
            import hmac
            import hashlib
            import base64
            import time
            import uuid

            params = {
                "PhoneNumbers": phone,
                "SignName": self.sign_name,
                "TemplateCode": template_code,
                "TemplateParam": str(template_params) if template_params else "",
                "Action": "SendSms",
                "Version": "2017-05-25",
                "Format": "JSON",
                "AccessKeyId": self.access_key_id,
                "SignatureMethod": "HMAC-SHA1",
                "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "SignatureVersion": "1.0",
                "SignatureNonce": str(uuid.uuid4()),
                "RegionId": "cn-hangzhou",
            }

            sorted_params = sorted(params.items())
            query_string = "&".join(
                f"{k}={v}" for k, v in sorted_params
            )
            string_to_sign = f"GET&%2F&{query_string}"
            signature = base64.b64encode(
                hmac.new(
                    (self.access_key_secret + "&").encode("utf-8"),
                    string_to_sign.encode("utf-8"),
                    hashlib.sha1,
                ).digest()
            ).decode("utf-8")

            params["Signature"] = signature

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://dysmsapi.aliyuncs.com/",
                    params=params,
                    timeout=10.0,
                )
                result = response.json()
                if result.get("Code") == "OK":
                    logger.info(f"Aliyun SMS sent to {phone}")
                    return True
                else:
                    logger.error(f"Aliyun SMS failed: {result}")
                    return False
        except Exception as e:
            logger.error(f"Aliyun SMS error: {e}")
            return False

    async def _send_tencent_sms(
        self, phone: str, template_code: str, template_params: dict
    ) -> bool:
        logger.info(f"Tencent SMS to {phone} (stub): template={template_code}")
        return True


sms_service = SmsService()
