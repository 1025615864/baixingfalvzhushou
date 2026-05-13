import base64
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ImageModerationResult:
    def __init__(self, passed: bool, reason: Optional[str] = None, label: Optional[str] = None):
        self.passed = passed
        self.reason = reason
        self.label = label


class AliyunModerationService:
    def __init__(self):
        self.access_key_id = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
        self.access_key_secret = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
        self.endpoint = os.getenv("ALIYUN_GREEN_ENDPOINT", "green.cn-shanghai.aliyuncs.com")
        self._enabled = bool(self.access_key_id and self.access_key_secret)

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def moderate(self, content: bytes, content_type: Optional[str] = None) -> ImageModerationResult:
        if not self._enabled:
            return ImageModerationResult(passed=True)

        try:
            url = f"https://{self.endpoint}/green/image/scan"
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            nonce = str(uuid.uuid4())

            body = json.dumps({
                "scenes": ["porn", "terrorism", "ad"],
                "tasks": [{
                    "dataId": str(uuid.uuid4()),
                    "content": base64.b64encode(content).decode(),
                }]
            })

            string_to_sign = f"POST\napplication/json\n{timestamp}\nx-acs-signature-nonce:{nonce}\n/green/image/scan"
            signature = base64.b64encode(
                hmac.new(
                    self.access_key_secret.encode(),
                    string_to_sign.encode(),
                    hashlib.sha1,
                ).digest()
            ).decode()

            headers = {
                "Content-Type": "application/json",
                "x-acs-signature-nonce": nonce,
                "x-acs-signature-method": "HMAC-SHA1",
                "x-acs-signature-version": "1.0",
                "x-acs-accesskey-id": self.access_key_id,
                "x-acs-timestamp": timestamp,
                "Authorization": f"acs {self.access_key_id}:{signature}",
            }

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, content=body, headers=headers)
                result = resp.json()

            for data_item in result.get("data", []):
                code = data_item.get("code", -1)
                if code != 200:
                    continue
                results = data_item.get("results", [])
                for r in results:
                    suggestion = r.get("suggestion", "pass")
                    label = r.get("label", "")
                    rate = r.get("rate", 0)
                    if suggestion == "block":
                        return ImageModerationResult(
                            passed=False,
                            reason=f"内容审核未通过: {label}",
                            label=label,
                        )
                    if suggestion == "review" and rate > 90:
                        return ImageModerationResult(
                            passed=False,
                            reason=f"内容疑似违规: {label}",
                            label=label,
                        )

            return ImageModerationResult(passed=True)

        except Exception as e:
            logger.error(f"Aliyun moderation failed: {e}")
            return ImageModerationResult(passed=True)


class TencentModerationService:
    def __init__(self):
        self.secret_id = os.getenv("TENCENT_SECRET_ID", "")
        self.secret_key = os.getenv("TENCENT_SECRET_KEY", "")
        self._enabled = bool(self.secret_id and self.secret_key)

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def moderate(self, content: bytes, content_type: Optional[str] = None) -> ImageModerationResult:
        if not self._enabled:
            return ImageModerationResult(passed=True)

        try:
            url = "https://ims.tencentcloudapi.com"
            timestamp = int(time.time())
            date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))

            body = json.dumps({
                "FileContent": base64.b64encode(content).decode(),
                "Scenes": ["PORN", "POLITICS", "TERRORISM"],
            })

            service = "ims"
            action = "ImageModeration"
            version = "2020-12-29"

            canonical_request = f"POST\n/\n\ncontent-type:application/json\nhost:{service}.tencentcloudapi.com\n\ncontent-type;host\n{hashlib.sha256(body.encode()).hexdigest()}"

            credential_scope = f"{date}/{service}/tc3_request"
            string_to_sign = f"TC3-HMAC-SHA256\n{timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"

            def _hmac_sha256(key: bytes, msg: str) -> bytes:
                return hmac.new(key, msg.encode(), hashlib.sha256).digest()

            secret_date = _hmac_sha256(f"TC3{self.secret_key}".encode(), date)
            secret_service = _hmac_sha256(secret_date, service)
            secret_signing = _hmac_sha256(secret_service, "tc3_request")
            signature = hmac.new(secret_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "Host": f"{service}.tencentcloudapi.com",
                "X-TC-Action": action,
                "X-TC-Version": version,
                "X-TC-Timestamp": str(timestamp),
                "Authorization": f"TC3-HMAC-SHA256 Credential={self.secret_id}/{credential_scope}, SignedHeaders=content-type;host, Signature={signature}",
            }

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, content=body, headers=headers)
                result = resp.json()

            response = result.get("Response", {})
            suggestion = response.get("Suggestion", "Pass")
            label = response.get("Label", "")

            if suggestion == "Block":
                return ImageModerationResult(
                    passed=False,
                    reason=f"内容审核未通过: {label}",
                    label=label,
                )
            if suggestion == "Review":
                return ImageModerationResult(
                    passed=False,
                    reason=f"内容疑似违规: {label}",
                    label=label,
                )

            return ImageModerationResult(passed=True)

        except Exception as e:
            logger.error(f"Tencent moderation failed: {e}")
            return ImageModerationResult(passed=True)


_moderation_service = None


def get_moderation_service():
    global _moderation_service
    if _moderation_service is not None:
        return _moderation_service

    provider = os.getenv("IMAGE_MODERATION_PROVIDER", "").strip().lower()

    if provider == "aliyun":
        _moderation_service = AliyunModerationService()
    elif provider == "tencent":
        _moderation_service = TencentModerationService()
    else:
        aliyun = AliyunModerationService()
        tencent = TencentModerationService()
        if aliyun.enabled:
            _moderation_service = aliyun
        elif tencent.enabled:
            _moderation_service = tencent
        else:
            _moderation_service = None

    return _moderation_service


async def moderate_image(content: bytes, content_type: Optional[str] = None) -> tuple[bool, Optional[str]]:
    service = get_moderation_service()
    if service is None or not service.enabled:
        logger.warning("Image moderation: no real provider configured, using pass-through")
        return True, None

    result = await service.moderate(content, content_type)
    return result.passed, result.reason
