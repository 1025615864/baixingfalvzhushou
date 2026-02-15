from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import cast
from urllib.parse import urlencode, parse_qsl

logger = logging.getLogger(__name__)

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key


def _normalize_pem(value: str) -> str:
    if not value:
        return ""
    return value.strip().replace("\\n", "\n")


def mask_payload(raw: str | None) -> str | None:
    """脱敏支付载荷数据"""
    if raw is None:
        return None
    s = str(raw)
    if not s.strip():
        return s

    sensitive_keys = {
        "sign",
        "signature",
        "sign_data",
        "sign_info",
        "app_cert_sn",
        "alipay_cert_sn",
        "card_no",
        "cvv",
        "password",
    }

    def _mask_value(v: object) -> object:
        if v is None:
            return None
        if isinstance(v, (int, float, bool)):
            return v
        ss = str(v)
        if not ss:
            return ss
        if len(ss) <= 8:
            return "*" * len(ss)
        return f"{ss[:3]}***{ss[-3:]}"

    def _mask_obj(obj: object) -> object:
        if isinstance(obj, dict):
            obj_dict = cast(dict[object, object], obj)
            out: dict[object, object] = {}
            for k, v in obj_dict.items():
                ks = str(k).strip().lower()
                if ks in sensitive_keys:
                    out[k] = _mask_value(v)
                else:
                    out[k] = _mask_obj(v)
            return out
        if isinstance(obj, list):
            obj_list = cast(list[object], obj)
            return [_mask_obj(x) for x in obj_list]
        return obj

    try:
        obj = cast(object, json.loads(s))
        masked = _mask_obj(obj)
        return json.dumps(masked, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("Failed to mask payload as JSON")

    try:
        pairs = parse_qsl(s, keep_blank_values=True)
        if pairs:
            obj2: dict[str, object] = {}
            for k, v in pairs:
                obj2[k] = v
            masked2 = _mask_obj(obj2)
            return json.dumps(masked2, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("Failed to mask payload as query string")

    return s


def mask_sensitive_data(payload: dict) -> dict:
    """对字典数据进行脱敏处理"""
    sensitive_keys = {"card_no", "cvv", "password", "sign", "signature"}
    out = {}
    for k, v in payload.items():
        ks = str(k).lower()
        if ks in sensitive_keys:
            if v is None:
                out[k] = None
            else:
                ss = str(v)
                if len(ss) <= 8:
                    out[k] = "*" * len(ss)
                else:
                    out[k] = f"{ss[:3]}***{ss[-3:]}"
        elif isinstance(v, dict):
            out[k] = mask_sensitive_data(v)
        else:
            out[k] = v
    return out


def _alipay_build_sign_string(params: dict[str, str]) -> str:
    items: list[tuple[str, str]] = []
    for k, v in params.items():
        if k in {"sign", "sign_type"}:
            continue
        s = str(v)
        if s == "":
            continue
        items.append((k, s))
    items.sort(key=lambda x: x[0])
    return "&".join([f"{k}={v}" for k, v in items])


def _alipay_sign_rsa2(params: dict[str, str], private_key_pem: str) -> str:
    sign_content = _alipay_build_sign_string(params)
    key = cast(
        RSAPrivateKey,
        load_pem_private_key(
            _normalize_pem(private_key_pem).encode("utf-8"),
            password=None),
    )
    signature = key.sign(
        sign_content.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def build_page_pay_url(
    *,
    gateway_url: str,
    app_id: str,
    private_key: str,
    notify_url: str,
    return_url: str | None,
    out_trade_no: str,
    total_amount: Decimal,
    subject: str,
) -> str:
    params: dict[str, str] = {
        "app_id": app_id,
        "method": "alipay.trade.page.pay",
        "format": "JSON",
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "notify_url": notify_url,
        "biz_content": json.dumps(
            {
                "out_trade_no": out_trade_no,
                "product_code": "FAST_INSTANT_TRADE_PAY",
                "total_amount": str(total_amount),
                "subject": subject,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    if return_url:
        params["return_url"] = return_url
    params["sign"] = _alipay_sign_rsa2(params, private_key)
    return f"{gateway_url}?{urlencode(params)}"


def _ikunpay_build_sign_string(params: dict[str, str]) -> str:
    items: list[tuple[str, str]] = []
    for k, v in params.items():
        if k in {"sign", "sign_type"}:
            continue
        s = str(v)
        if s == "":
            continue
        items.append((k, s))
    items.sort(key=lambda x: x[0])
    return "&".join([f"{k}={v}" for k, v in items])


def _ikunpay_sign_md5(params: dict[str, str], key: str) -> str:
    sign_content = _ikunpay_build_sign_string(params)
    raw = (sign_content + str(key)).encode("utf-8")
    return hashlib.md5(raw).hexdigest().lower()


def build_submit_pay_url(
    *,
    gateway_url: str,
    pid: str,
    pay_type: str | None,
    out_trade_no: str,
    notify_url: str,
    return_url: str | None,
    name: str,
    money: Decimal,
    key: str,
) -> str:
    quantized = Decimal(
        str(money)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP)
    params: dict[str, str] = {
        "pid": str(pid).strip(),
        "out_trade_no": str(out_trade_no).strip(),
        "notify_url": str(notify_url).strip(),
        "name": str(name).strip(),
        "money": str(quantized),
        "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
        "sign_type": "MD5",
    }
    if pay_type:
        params["type"] = str(pay_type).strip()
    if return_url:
        params["return_url"] = str(return_url).strip()
    params["sign"] = _ikunpay_sign_md5(params, key)
    return f"{gateway_url}?{urlencode(params)}"


def verify_ikunpay_signature(params: dict[str, str], key: str) -> bool:
    """验证爱坤支付签名"""
    sign = str(params.get("sign") or "").strip().lower()
    if not sign:
        return False
    expected = _ikunpay_sign_md5(params, key)
    return hmac.compare_digest(expected, sign)


def _ikunpay_verify_md5(params: dict[str, str], key: str) -> bool:
    """爱坤支付签名验证 (别名支持)"""
    return verify_ikunpay_signature(params, key)


def _alipay_verify_rsa2(params: dict[str, str], public_key_pem: str) -> bool:
    """验证支付宝 RSA2 签名"""
    try:
        sign = params.get("sign")
        if not sign:
            return False

        # 1. 准备待验签字符串
        sign_content = _alipay_build_sign_string(params)

        # 2. 加载公钥
        key = cast(
            RSAPublicKey,
            load_pem_public_key(
                _normalize_pem(public_key_pem).encode("utf-8")),
        )

        # 3. 验证签名
        key.verify(
            base64.b64decode(sign),
            sign_content.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        logger.exception("Alipay RSA2 signature verification failed")
        return False


def _alipay_public_key_check(public_key_pem: str | None) -> bool:
    """检查支付宝公钥格式是否正确"""
    if not public_key_pem or not str(public_key_pem).strip():
        return False
    try:
        load_pem_public_key(
            _normalize_pem(
                str(public_key_pem)).encode("utf-8"))
        return True
    except Exception:
        logger.exception("Alipay public key check failed")
        return False


def _alipay_private_key_check(private_key_pem: str | None) -> bool:
    """检查支付宝私钥格式是否正确"""
    if not private_key_pem or not str(private_key_pem).strip():
        return False
    try:
        load_pem_private_key(
            _normalize_pem(str(private_key_pem)).encode("utf-8"), password=None
        )
        return True
    except Exception:
        logger.exception("Alipay private key check failed")
        return False
