from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import cast, Any
from urllib.parse import urlencode, parse_qsl, urlsplit, urlunsplit

from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, IllegalStateChangeError
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.payment import PaymentCallbackEvent, PaymentOrder, PaymentStatus
from ...models.system import SystemConfig, AdminLog, LogAction, LogModule
from ...models.user import User
from ...config import get_settings, Settings
from ...utils.cache_strategy import cache_strategy
from . import crypto_utils as payment_crypto

logger = logging.getLogger(__name__)

# AI 次数包关联类型
AI_PACK_RELATED_TYPES = {"ai_chat", "document_generate"}

# Global cache for alipay client
_alipay_client_cache: dict[str, Any] = {}


def resolve_env_file_path() -> Path:
    """解析 .env 文件路径"""
    explicit = os.getenv("ENV_FILE", "").strip()
    here = Path(__file__).resolve()
    backend_dir = here.parents[2]
    repo_root = here.parents[3]

    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            backend_candidate = backend_dir / explicit
            repo_candidate = repo_root / explicit
            if backend_candidate.exists():
                return backend_candidate
            if repo_candidate.exists():
                return repo_candidate
            return backend_candidate
        return p

    backend_env = backend_dir / ".env"
    if backend_env.exists():
        return backend_env
    repo_env = repo_root / ".env"
    if repo_env.exists():
        return repo_env
    return backend_env


def format_env_value(_key: str, value: str) -> str:
    """格式化环境变量值"""
    raw = str(value)
    raw = raw.replace("\r\n", "\n").strip()
    raw = raw.replace("\\", "\\\\")
    raw = raw.replace('"', '\\"')
    if "\n" in raw:
        raw = raw.replace("\n", "\\n")
    return f'"{raw}"'


def update_env_file(updates: dict[str, str | None],
                    env_path: Path | None = None) -> list[str]:
    """更新 .env 文件"""
    path = env_path or resolve_env_file_path()

    allowed = {
        "PAYMENT_WEBHOOK_SECRET",
        "ALIPAY_APP_ID",
        "ALIPAY_PRIVATE_KEY",
        "ALIPAY_PUBLIC_KEY",
        "ALIPAY_GATEWAY_URL",
        "ALIPAY_NOTIFY_URL",
        "ALIPAY_RETURN_URL",
        "ALIPAY_APP_CERT_SN",
        "ALIPAY_ROOT_CERT_SN",
        "IKUNPAY_PID",
        "IKUNPAY_KEY",
        "IKUNPAY_GATEWAY_URL",
        "IKUNPAY_NOTIFY_URL",
        "IKUNPAY_RETURN_URL",
        "IKUNPAY_DEFAULT_TYPE",
        "WECHATPAY_MCH_ID",
        "WECHATPAY_MCH_SERIAL_NO",
        "WECHATPAY_PRIVATE_KEY",
        "WECHATPAY_API_V3_KEY",
        "WECHATPAY_CERTIFICATES_URL",
        "FRONTEND_BASE_URL",
    }

    normalized: dict[str, str | None] = {}
    for k, v in updates.items():
        kk = str(k or "").strip().upper()
        if not kk or kk not in allowed:
            continue
        if v is None:
            normalized[kk] = None
        else:
            vv = str(v).strip()
            normalized[kk] = vv if vv else None

    if not normalized:
        return []

    lines = []
    if path.exists():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            logger.exception("Failed to read env file, using fallback")
            lines = path.read_text(
                encoding="utf-8",
                errors="ignore").splitlines()

    key_re = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=.*$")

    used: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            out.append(line)
            continue
        m = key_re.match(line)
        if not m:
            out.append(line)
            continue
        k = str(m.group(1) or "").strip().upper()
        if k not in normalized:
            out.append(line)
            continue

        used.add(k)
        v = normalized.get(k)
        if v is None:
            continue
        out.append(f"{k}={format_env_value(k, v)}")

    for k, v in normalized.items():
        if k in used:
            continue
        if v is None:
            continue
        out.append(f"{k}={format_env_value(k, v)}")

    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(out).rstrip("\n") + "\n"
    path.write_text(text, encoding="utf-8")

    return sorted(list(normalized.keys()))


def get_alipay_client():
    """获取支付宝客户端（带缓存）"""
    settings = get_settings()
    if not settings.alipay_app_id or not settings.alipay_private_key:
        return None

    cache_key = f"{settings.alipay_app_id}:{hash(settings.alipay_private_key)}"
    if cache_key in _alipay_client_cache:
        return _alipay_client_cache[cache_key]

    try:
        from alipay import AliPay
        client = AliPay(
            appid=settings.alipay_app_id,
            app_notify_url=settings.alipay_notify_url,
            app_private_key_string=settings.alipay_private_key.replace(
                "\\n", "\n"),
            alipay_public_key_string=settings.alipay_public_key.replace(
                "\\n", "\n"),
            sign_type="RSA2",
            debug=settings.debug,
        )
        _alipay_client_cache[cache_key] = client
        return client
    except Exception as e:
        logger.error(f"Failed to create alipay client: {e}")
        return None


async def get_order_by_out_trade_no(
        db: AsyncSession, out_trade_no: str) -> PaymentOrder | None:
    """根据订单号查询订单（带缓存）"""
    cache_key = f"payment_order:{out_trade_no}"

    async def _load_from_db():
        res = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == out_trade_no))
        return res.scalar_one_or_none()

    return await cache_strategy.get_or_load(cache_key, _load_from_db, expire=300)


async def update_order_status(
    db: AsyncSession,
    order_no: str,
    status: PaymentStatus,
    trade_no: str | None = None,
    paid_at: datetime | None = None
) -> bool:
    """更新订单状态（幂等）"""
    stmt = (
        update(PaymentOrder)
        .where(PaymentOrder.order_no == order_no)
        .where(PaymentOrder.status != status)  # 幂等检查
        .values(
            status=status,
            trade_no=trade_no,
            paid_at=paid_at or (datetime.now(timezone.utc)
                                if status == PaymentStatus.PAID else None),
            updated_at=datetime.now(timezone.utc)
        )
    )
    res = await db.execute(stmt)
    await db.flush()

    if getattr(res, "rowcount", 0) > 0:
        # 失效缓存
        await cache_strategy.invalidate_pattern(f"payment_order:{order_no}")
        return True
    return False


async def log_callback_event(
    db: AsyncSession,
    *,
    provider: str,
    order_no: str | None,
    trade_no: str | None,
    amount: Decimal | float | None,
    verified: bool,
    error_message: str | None,
    raw_payload: str | None,
    source_ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """记录支付回调事件"""
    amount_float = float(amount) if amount is not None else None

    payload_hash = None
    raw_payload_src = raw_payload
    if raw_payload_src:
        payload_hash = hashlib.sha256(raw_payload_src.encode("utf-8")).hexdigest()

    allow_raw = bool(get_settings().debug) or os.getenv(
        "PAYMENT_CALLBACK_STORE_RAW",
        "false",
    ).strip().lower() in {"1", "true", "yes", "on"}
    if raw_payload_src and not allow_raw:
        raw_payload = payment_crypto.mask_payload(raw_payload_src)

    evt = PaymentCallbackEvent(
        provider=provider,
        order_no=order_no,
        trade_no=trade_no,
        amount=amount_float,
        verified=verified,
        error_message=error_message,
        raw_payload=raw_payload,
        raw_payload_hash=payload_hash,
        source_ip=source_ip[:45] if source_ip else None,
        user_agent=user_agent[:512] if user_agent else None,
    )

    db.add(evt)
    # 这里通常不 commit，因为回调函数外部会有事务管理
    # 使用 try-except 处理并发 flush 的情况
    try:
        await db.flush()
    except Exception:
        # 如果 flush 失败（例如 session 已经在 flushing），则忽略
        # 这在并发场景下可能发生，事件记录失败不影响支付处理
        logger.exception("Failed to flush callback event (may be concurrent)")


def generate_order_no() -> str:
    """生成订单号"""
    now = datetime.now(timezone.utc)
    return f"{now.strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"


def _quantize_amount(amount: float | Decimal | str | int) -> Decimal:
    """金额舍入到2位小数"""
    return Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal_to_cents(amount: Decimal) -> int:
    """将 Decimal 金额转换为分（整数）"""
    return int((amount * Decimal("100")).quantize(Decimal("1"),
               rounding=ROUND_HALF_UP))


def _append_query_param(url: str, key: str, value: str) -> str:
    """向 URL 添加查询参数"""
    scheme, netloc, path, query, fragment = urlsplit(url)
    params = dict(parse_qsl(query))
    params[key] = value
    return urlunsplit((scheme, netloc, path, urlencode(params), fragment))


async def _get_system_config_value(db: AsyncSession, key: str) -> str | None:
    res = await db.execute(select(SystemConfig.value).where(SystemConfig.key == str(key).strip()))
    v = res.scalar_one_or_none()
    return str(v) if isinstance(v, str) else None


async def _get_int_config(db: AsyncSession, key: str, default: int) -> int:
    raw = await _get_system_config_value(db, key)
    if raw is None:
        return int(default)
    try:
        return int(str(raw).strip())
    except Exception:
        logger.exception("Failed to parse int config for key: %s", key)
        return int(default)


async def _set_system_config_value(
    db: AsyncSession,
    key: str,
    value: str,
    category: str = "general",
    description: str | None = None,
    updated_by: int | None = None,
) -> None:
    """设置系统配置值"""
    stmt = select(SystemConfig).where(SystemConfig.key == str(key).strip())
    res = await db.execute(stmt)
    config = res.scalar_one_or_none()

    if config:
        config.value = str(value)
        if category != "general":
            config.category = category
        if description:
            config.description = description
        if updated_by:
            config.updated_by = updated_by
    else:
        config = SystemConfig(
            key=str(key).strip(),
            value=str(value),
            category=category,
            description=description,
            updated_by=updated_by,
        )
        db.add(config)
    await db.flush()


async def _log_config_change(
    db: AsyncSession,
    user_id: int | User,
    action: str = LogAction.UPDATE,
    module: str = LogModule.SYSTEM,
    target_id: int | None = None,
    description: str | None = None,
    request: Request | None = None,
    **kwargs: Any,
) -> None:
    """记录配置变更日志"""
    uid = user_id.id if isinstance(user_id, User) else int(user_id)
    content = description or kwargs.get("content", "")

    ip = None
    ua = None
    if request:
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")

    log = AdminLog(
        user_id=uid,
        module=module,
        action=action,
        target_id=target_id,
        description=content,
        ip_address=ip,
        user_agent=ua,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()


_resolve_env_file_path = resolve_env_file_path
_update_env_file = update_env_file


async def _get_float_config(db: AsyncSession, key: str,
                            default: float) -> float:
    raw = await _get_system_config_value(db, key)
    if raw is None:
        return float(default)
    try:
        return float(str(raw).strip())
    except Exception:
        logger.exception("Failed to parse float config for key: %s", key)
        return float(default)


async def _get_vip_plan(db: AsyncSession) -> tuple[int, float]:
    """获取 VIP 计划配置（天数，价格）"""
    vip_days = await _get_int_config(db, "vip_days", 30)
    vip_price = await _get_float_config(db, "vip_price", 99.0)
    return vip_days, vip_price


async def _get_pack_options(
        db: AsyncSession, pack_type: str) -> dict[int, float]:
    """获取次数包选项配置"""
    if pack_type == "ai_chat":
        options = {
            10: await _get_float_config(db, "ai_chat_pack_10_price", 30.0),
            50: await _get_float_config(db, "ai_chat_pack_50_price", 120.0),
            100: await _get_float_config(db, "ai_chat_pack_100_price", 200.0),
        }
    elif pack_type == "document_generate":
        options = {
            5: await _get_float_config(db, "doc_pack_5_price", 25.0),
            20: await _get_float_config(db, "doc_pack_20_price", 80.0),
            50: await _get_float_config(db, "doc_pack_50_price", 150.0),
        }
    else:
        options = {}
    return options


async def _get_review_price(db: AsyncSession) -> float:
    """获取复核价格配置"""
    return await _get_float_config(db, "light_consult_review_price", 29.0)
