from __future__ import annotations

import json
import logging
import os
import sys
from datetime import timezone
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...database import get_db
from ...models.user import User
from ...utils.deps import require_admin
from ...utils.wechatpay_v3 import (
    WeChatPayPlatformCert,
    dump_platform_certs_json,
    fetch_platform_certificates,
    load_platform_certs_json,
)
from . import crypto_utils as payment_crypto
from . import helpers as payment_helpers

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


def _get_runtime_settings():
    """获取运行时配置"""
    return settings


class PaymentChannelStatusResponse(BaseModel):
    alipay_configured: bool
    wechatpay_configured: bool
    ikunpay_configured: bool
    payment_webhook_secret_configured: bool
    wechatpay_platform_certs_cached: bool
    wechatpay_platform_certs_total: int
    wechatpay_platform_certs_updated_at: int | None
    wechatpay_cert_refresh_enabled: bool
    details: dict[str, object]


class PublicPaymentChannelStatusResponse(BaseModel):
    alipay_configured: bool
    wechatpay_configured: bool
    ikunpay_configured: bool
    available_methods: list[str]


class WechatPlatformCertImportRequest(BaseModel):
    platform_certs_json: str | None = None
    cert_pem: str | None = None
    serial_no: str | None = None
    expire_time: str | None = None
    merge: bool = True


class PaymentEnvItem(BaseModel):
    key: str
    value: str | None = None


class PaymentEnvUpdateRequest(BaseModel):
    items: list[PaymentEnvItem]


@router.get("/admin/wechat/platform-certs", summary="管理员-微信平台证书")
async def admin_wechat_platform_certs(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    _ = current_user
    cfg_raw = await payment_helpers._get_system_config_value(db, "WECHATPAY_PLATFORM_CERTS_JSON")
    certs = load_platform_certs_json(cfg_raw or "")
    items: list[dict[str, object]] = []
    for serial, cert in certs.items():
        items.append({"serial_no": serial, "expire_time": cert.expire_time})
    items.sort(key=lambda x: str(x.get("serial_no") or ""))
    return {"items": items, "total": len(items)}


@router.get("/admin/channel-status",
            response_model=PaymentChannelStatusResponse,
            summary="管理员-支付渠道配置状态")
async def admin_payment_channel_status(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user
    s = _get_runtime_settings()

    alipay_app_id_set = bool((s.alipay_app_id or "").strip())
    alipay_public_key_set = bool((s.alipay_public_key or "").strip())
    alipay_private_key_set = bool((s.alipay_private_key or "").strip())
    alipay_notify_url_set = bool((s.alipay_notify_url or "").strip())

    wechatpay_mch_id_set = bool((s.wechatpay_mch_id or "").strip())
    wechatpay_serial_no_set = bool((s.wechatpay_mch_serial_no or "").strip())
    wechatpay_private_key_set = bool((s.wechatpay_private_key or "").strip())
    wechatpay_api_v3_key_set = bool((s.wechatpay_api_v3_key or "").strip())

    ikunpay_pid_set = bool((s.ikunpay_pid or "").strip())
    ikunpay_key_set = bool((s.ikunpay_key or "").strip())
    ikunpay_notify_url_set = bool((s.ikunpay_notify_url or "").strip())

    payment_webhook_secret_set = bool((s.payment_webhook_secret or "").strip())

    cfg_raw = await payment_helpers._get_system_config_value(db, "WECHATPAY_PLATFORM_CERTS_JSON")
    certs_map = load_platform_certs_json(cfg_raw or "")

    updated_at: int | None = None
    try:
        obj_raw: object = cast(object, json.loads(cfg_raw or ""))
        if isinstance(obj_raw, dict):
            obj_dict = cast(dict[str, object], obj_raw)
            v = obj_dict.get("updated_at")
            if isinstance(v, bool):
                updated_at = None
            elif isinstance(v, (int, float)):
                updated_at = int(v)
            elif isinstance(v, str) and v.strip():
                updated_at = int(v.strip())
    except Exception:
        logger.exception("Failed to parse updated_at from platform certs config")
        updated_at = None

    refresh_enabled_raw = os.getenv(
        "WECHATPAY_CERT_REFRESH_ENABLED",
        "").strip().lower()
    refresh_enabled = refresh_enabled_raw in {"1", "true", "yes", "on"}

    frontend_base = str(
        getattr(
            s,
            "frontend_base_url",
            "") or "").strip().rstrip("/")

    alipay_configured = bool(
        alipay_app_id_set and alipay_public_key_set and alipay_private_key_set and alipay_notify_url_set)
    wechatpay_configured = bool(
        wechatpay_mch_id_set and wechatpay_serial_no_set and wechatpay_private_key_set and wechatpay_api_v3_key_set)
    ikunpay_configured = bool(
        ikunpay_pid_set and ikunpay_key_set and ikunpay_notify_url_set)

    alipay_return_url = (s.alipay_return_url or "").strip() or None
    alipay_effective_return_url = alipay_return_url
    if alipay_effective_return_url is None and frontend_base:
        alipay_effective_return_url = f"{frontend_base}/payment/return"

    return PaymentChannelStatusResponse(
        alipay_configured=alipay_configured,
        wechatpay_configured=wechatpay_configured,
        ikunpay_configured=ikunpay_configured,
        payment_webhook_secret_configured=payment_webhook_secret_set,
        wechatpay_platform_certs_cached=len(certs_map) > 0,
        wechatpay_platform_certs_total=len(certs_map),
        wechatpay_platform_certs_updated_at=updated_at,
        wechatpay_cert_refresh_enabled=refresh_enabled,
        details={
            "alipay": {
                "app_id_set": alipay_app_id_set,
                "public_key_set": alipay_public_key_set,
                "private_key_set": alipay_private_key_set,
                "notify_url_set": alipay_notify_url_set,
                "public_key_check": payment_crypto._alipay_public_key_check(
                    s.alipay_public_key),
                "private_key_check": payment_crypto._alipay_private_key_check(
                    s.alipay_private_key),
                "gateway_url": (
                    s.alipay_gateway_url or "").strip() or None,
                "notify_url": (
                    s.alipay_notify_url or "").strip() or None,
                "return_url": alipay_return_url,
                "effective_return_url": alipay_effective_return_url,
            },
            "ikunpay": {
                "pid_set": ikunpay_pid_set,
                "key_set": ikunpay_key_set,
                "notify_url_set": ikunpay_notify_url_set,
                "gateway_url": (
                    s.ikunpay_gateway_url or "").strip() or None,
                "notify_url": (
                    s.ikunpay_notify_url or "").strip() or None,
                "return_url": (
                    s.ikunpay_return_url or "").strip() or None,
                "default_type": (
                    s.ikunpay_default_type or "").strip() or None,
            },
            "wechatpay": {
                "mch_id_set": wechatpay_mch_id_set,
                "serial_no_set": wechatpay_serial_no_set,
                "private_key_set": wechatpay_private_key_set,
                "api_v3_key_set": wechatpay_api_v3_key_set,
            },
        },
    )


@router.post("/admin/env", summary="管理员-更新支付环境变量（写入 env 文件并热加载）")
async def admin_update_payment_env(
    req: PaymentEnvUpdateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> dict[str, Any]:
    _ = current_user

    updates: dict[str, str | None] = {}
    for item in (req.items or []):
        k = str(getattr(item, "key", "") or "").strip().upper()
        v_obj = getattr(item, "value", None)
        v = None if v_obj is None else str(v_obj)
        if not k:
            continue
        updates[k] = v

    running_tests = bool(
        os.getenv("PYTEST_CURRENT_TEST")) or (
        "pytest" in sys.modules)

    env_file_name = "in-memory"
    updated_keys: list[str] = []
    if not running_tests:
        env_path = payment_helpers._resolve_env_file_path()
        updated_keys = payment_helpers._update_env_file(
            updates=updates, env_path=env_path)
        env_file_name = str(env_path.name)
    else:
        updated_keys = sorted([str(k).strip().upper()
                              for k in updates.keys() if str(k).strip()])

    if not updated_keys:
        raise HTTPException(status_code=400, detail="未提供可更新的配置项")

    for k in updated_keys:
        v = updates.get(k)
        if v is None or not str(v).strip():
            try:
                if k in os.environ:
                    del os.environ[k]
            except Exception:
                logger.exception("Failed to delete environment variable: %s", k)
        else:
            os.environ[k] = str(v)

    global settings
    get_settings.cache_clear()
    settings = get_settings()

    await payment_helpers._log_config_change(
        db,
        user_id=int(getattr(current_user, "id", 0) or 0),
        module=payment_helpers.LogModule.SYSTEM,
        action=payment_helpers.LogAction.UPDATE,
        request=request,
        description=f"更新支付 env: {', '.join(updated_keys)}",
    )
    await db.commit()

    status = await admin_payment_channel_status(current_user=current_user, db=db)
    return {
        "message": "OK",
        "env_file": env_file_name,
        "updated_keys": updated_keys,
        "channel_status": status,
    }


@router.get("/channel-status",
            response_model=PublicPaymentChannelStatusResponse,
            summary="支付渠道配置状态")
async def payment_channel_status():
    s = _get_runtime_settings()
    alipay_configured = bool(
        (s.alipay_app_id or "").strip()
        and (s.alipay_public_key or "").strip()
        and (s.alipay_private_key or "").strip()
        and (s.alipay_notify_url or "").strip()
    )
    ikunpay_configured = bool(
        (s.ikunpay_pid or "").strip()
        and (s.ikunpay_key or "").strip()
        and (s.ikunpay_notify_url or "").strip()
    )
    wechatpay_configured = bool(
        (s.wechatpay_mch_id or "").strip()
        and (s.wechatpay_mch_serial_no or "").strip()
        and (s.wechatpay_private_key or "").strip()
        and (s.wechatpay_api_v3_key or "").strip()
    )

    available_methods: list[str] = ["balance"]
    if alipay_configured:
        available_methods.append("alipay")
    if ikunpay_configured:
        available_methods.append("ikunpay")

    return PublicPaymentChannelStatusResponse(
        alipay_configured=alipay_configured,
        wechatpay_configured=wechatpay_configured,
        ikunpay_configured=ikunpay_configured,
        available_methods=available_methods,
    )


@router.post("/admin/wechat/platform-certs/import", summary="管理员-导入微信平台证书")
async def admin_import_wechat_platform_certs(
    req: WechatPlatformCertImportRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    existing_raw = await payment_helpers._get_system_config_value(db, "WECHATPAY_PLATFORM_CERTS_JSON")
    existing_map = load_platform_certs_json(existing_raw or "")
    merged: dict[str, WeChatPayPlatformCert] = dict(existing_map)

    if req.platform_certs_json and str(req.platform_certs_json).strip():
        incoming_raw = str(req.platform_certs_json)
        incoming_map = load_platform_certs_json(incoming_raw)
        if not incoming_map:
            raise HTTPException(
                status_code=400,
                detail="platform_certs_json 无法解析或为空（需为 dump_platform_certs_json 输出格式）")
        if req.merge:
            merged.update(incoming_map)
        else:
            merged = dict(incoming_map)

        raw = dump_platform_certs_json(list(merged.values()))
        await payment_helpers._set_system_config_value(
            db,
            key="WECHATPAY_PLATFORM_CERTS_JSON",
            value=raw,
            category="payment",
            description="WeChatPay platform certificates cache",
            updated_by=getattr(current_user, "id", None),
        )
        await db.commit()
        return cast(dict[str, Any], {"message": "OK", "count": len(merged)})

    if req.cert_pem and str(req.cert_pem).strip():
        cert_pem = str(req.cert_pem).strip()
        serial_no = str(req.serial_no or "").strip()
        expire_time = str(req.expire_time or "").strip() or None

        if not serial_no or not expire_time:
            try:
                from cryptography import x509

                cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"))
                if not serial_no:
                    serial_no = format(int(cert.serial_number), "X").upper()
                if not expire_time:
                    dt = getattr(cert, "not_valid_after_utc",
                                 None) or cert.not_valid_after
                    expire_time = dt.replace(tzinfo=timezone.utc).isoformat()
            except Exception:
                logger.exception("Failed to parse certificate expire_time")

        if not serial_no:
            raise HTTPException(
                status_code=400,
                detail="无法从证书解析 serial_no，请手动填写")

        merged[serial_no] = WeChatPayPlatformCert(
            serial_no=serial_no, pem=cert_pem, expire_time=expire_time)
        raw = dump_platform_certs_json(list(merged.values()))
        await payment_helpers._set_system_config_value(
            db,
            key="WECHATPAY_PLATFORM_CERTS_JSON",
            value=raw,
            category="payment",
            description="WeChatPay platform certificates cache",
            updated_by=getattr(current_user, "id", None),
        )
        await db.commit()
        return cast(dict[str, Any], {"message": "OK", "count": len(merged)})

    raise HTTPException(
        status_code=400,
        detail="请提供 platform_certs_json 或 cert_pem")


@router.post("/admin/wechat/platform-certs/refresh", summary="管理员-刷新微信平台证书")
async def admin_refresh_wechat_platform_certs(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    s = _get_runtime_settings()
    if not s.wechatpay_mch_id or not s.wechatpay_mch_serial_no:
        raise HTTPException(
            status_code=400,
            detail="WECHATPAY_MCH_ID/WECHATPAY_MCH_SERIAL_NO 未设置")
    if not s.wechatpay_private_key:
        raise HTTPException(
            status_code=400,
            detail="WECHATPAY_PRIVATE_KEY 未设置")
    if not s.wechatpay_api_v3_key:
        raise HTTPException(status_code=400, detail="WECHATPAY_API_V3_KEY 未设置")

    payment_mod = sys.modules.get("app.routers.payment")
    fetch_fn: Callable[..., Awaitable[list[WeChatPayPlatformCert]]
                       ] = fetch_platform_certificates
    if payment_mod is not None:
        candidate = getattr(payment_mod, "fetch_platform_certificates", None)
        if callable(candidate):
            fetch_fn = cast(
                Callable[..., Awaitable[list[WeChatPayPlatformCert]]], candidate)

    certs = await fetch_fn(
        certificates_url=s.wechatpay_certificates_url,
        mch_id=s.wechatpay_mch_id,
        mch_serial_no=s.wechatpay_mch_serial_no,
        mch_private_key_pem=s.wechatpay_private_key,
        api_v3_key=s.wechatpay_api_v3_key,
    )
    raw = dump_platform_certs_json(certs)
    await payment_helpers._set_system_config_value(
        db,
        key="WECHATPAY_PLATFORM_CERTS_JSON",
        value=raw,
        category="payment",
        description="WeChatPay platform certificates cache",
        updated_by=getattr(current_user, "id", None),
    )
    await db.commit()

    return cast(dict[str, Any], {"message": "OK", "count": len(certs)})
