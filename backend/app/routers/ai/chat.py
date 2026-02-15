"""AI chat routes

Provides AI chat endpoints - chat and streaming chat
"""
import uuid
import asyncio
import hashlib
import json
import logging
import time
import os
import inspect as py_inspect
from collections.abc import Callable
from typing import Annotated, Any, cast
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, inspect

from ...database import get_db
from ...models.consultation import Consultation, ChatMessage
from ...models.user import User
from ...config import get_settings
from ...services.ai_metrics import ai_metrics
from ...services.critical_event_reporter import critical_event_reporter
from ...services.quota_service import quota_service
from ...schemas.ai import ChatRequest, ChatResponse, SearchQualityInfo
from ...utils.deps import get_current_user, get_current_user_optional
from ...utils.rate_limiter import rate_limit, RateLimitConfig, rate_limiter, get_client_ip
from ...utils.helpers import _get_int_env, _coerce_int

router = APIRouter(prefix="/ai", tags=["AI法律助手"])

settings = get_settings()
logger = logging.getLogger(__name__)


GUEST_AI_LIMIT = _get_int_env("GUEST_AI_LIMIT", 3)
GUEST_AI_WINDOW_SECONDS = _get_int_env("GUEST_AI_WINDOW_SECONDS", 60 * 60 * 24)
SEED_HISTORY_MAX_MESSAGES = 20

ERROR_AI_NOT_CONFIGURED = "AI_NOT_CONFIGURED"
ERROR_AI_UNAVAILABLE = "AI_UNAVAILABLE"
ERROR_AI_RATE_LIMITED = "AI_RATE_LIMITED"
ERROR_AI_FORBIDDEN = "AI_FORBIDDEN"
ERROR_AI_UNAUTHORIZED = "AI_UNAUTHORIZED"
ERROR_AI_BAD_REQUEST = "AI_BAD_REQUEST"
ERROR_AI_INTERNAL_ERROR = "AI_INTERNAL_ERROR"


def _stable_bucket(seed: str) -> int:
    s = str(seed or "").strip()
    if not s:
        return 0
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    try:
        return int(h[:8], 16) % 100
    except Exception:
        return 0


async def _get_system_config_value(db: AsyncSession, key: str) -> str | None:
    from ...models.system import SystemConfig

    k = str(key or "").strip()
    if not k:
        return None
    res = await db.execute(select(SystemConfig.value).where(SystemConfig.key == k))
    v = res.scalar_one_or_none()
    return str(v) if isinstance(v, str) else None


async def _select_prompt_version(db: AsyncSession, *, bucket_seed: str) -> str:
    default_pv = str((await _get_system_config_value(db, "AI_PROMPT_VERSION_DEFAULT")) or "v1").strip() or "v1"
    v2_pv = str((await _get_system_config_value(db, "AI_PROMPT_VERSION_V2")) or "v2").strip() or "v2"

    percent_raw = await _get_system_config_value(db, "AI_PROMPT_VERSION_V2_PERCENT")
    percent = _coerce_int(percent_raw, 0)
    percent = max(0, min(100, int(percent)))

    if percent <= 0:
        return default_pv
    if percent >= 100:
        return v2_pv or default_pv

    bucket = _stable_bucket(bucket_seed)
    return v2_pv if bucket < percent else default_pv


def _audit_event(event: str, payload: dict[str, object]) -> None:
    try:
        logger.info(
            "ai_audit event=%s payload=%s",
            str(event),
            json.dumps(
                payload,
                ensure_ascii=False))
    except Exception:
        logger.info("ai_audit event=%s", str(event))


def _error_code_for_http(status_code: int) -> str:
    sc = int(status_code)
    if sc == 400:
        return ERROR_AI_BAD_REQUEST
    if sc == 401:
        return ERROR_AI_UNAUTHORIZED
    if sc == 403:
        return ERROR_AI_FORBIDDEN
    if sc == 429:
        return ERROR_AI_RATE_LIMITED
    if sc == 503:
        return ERROR_AI_UNAVAILABLE
    return ERROR_AI_INTERNAL_ERROR


def _extract_message(detail: object) -> str:
    if detail is None:
        return ""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        detail_dict = cast(dict[str, object], detail)
        msg_obj = detail_dict.get("message")
        if isinstance(msg_obj, str):
            return msg_obj
        msg2_obj = detail_dict.get("detail")
        if isinstance(msg2_obj, str):
            return msg2_obj
    return str(detail)


def _make_error_response(
    *,
    status_code: int,
    error_code: str,
    message: str,
    request_id: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    out_headers: dict[str, str] = {
        "X-Request-Id": str(request_id),
        "X-Error-Code": str(error_code),
    }
    if headers:
        for k, v in headers.items():
            out_headers[str(k)] = str(v)

    return JSONResponse(
        status_code=int(status_code),
        content={
            "error_code": str(error_code),
            "message": str(message),
            "detail": str(message),
            "request_id": str(request_id),
        },
        headers=out_headers,
    )


def _audit_text(value: str | None, *, limit: int = 500) -> str:
    s = str(value or "")
    s = s.replace("\r", " ").replace("\n", " ")
    s = s[: max(0, limit)]
    s = s.strip()
    s = s.replace("\t", " ")
    s = s.replace("  ", " ")
    return s


async def _enforce_guest_ai_quota(request: Request) -> None:
    key = f"ai:guest:{get_client_ip(request)}"
    allowed, remaining, wait_time = await rate_limiter.check(key, GUEST_AI_LIMIT, GUEST_AI_WINDOW_SECONDS)
    if allowed:
        return
    raise HTTPException(
        status_code=429,
        detail=f"游客模式 24 小时内仅可试用 {int(GUEST_AI_LIMIT)} 次，请登录后继续",
        headers={
            "X-RateLimit-Limit": str(GUEST_AI_LIMIT),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str(int(time.time() + wait_time)),
            "Retry-After": str(int(wait_time)),
        },
    )


def _try_get_ai_assistant() -> Any | None:
    """
    获取AI助手实例

    先尝试从ai模块的导出中获取（支持测试mock），
    如果没有则使用本地实现。
    """
    # First try to use the mock from ai module (if test has set it)
    import sys
    try:
        ai_module = sys.modules.get('app.routers.ai')
        if ai_module is not None:
            mock_func = getattr(ai_module, '_try_get_ai_assistant', None)
            if mock_func is not None and callable(mock_func):
                # Check if it's different from this function (meaning it was
                # mocked)
                if mock_func is not _try_get_ai_assistant:
                    return mock_func()
    except Exception:
        logger.exception("Failed to get mock AI assistant")

    # Fall back to original implementation
    try:
        from ...services.ai_assistant import get_ai_assistant
        return get_ai_assistant()
    except Exception:
        return None


def _supports_kwarg(func: Callable[..., Any] | None, name: str) -> bool:
    if func is None:
        return False
    try:
        sig = py_inspect.signature(func)
        params = sig.parameters
        for p in params.values():
            if p.kind == py_inspect.Parameter.VAR_KEYWORD:
                return True
        return name in params
    except Exception:
        logger.exception("Failed to check kwarg support")
        return False


def _build_user_profile(current_user: User | None) -> str:
    if current_user is None:
        return ""
    nickname = str(getattr(current_user, "nickname", "") or "").strip()
    username = str(getattr(current_user, "username", "") or "").strip()
    role = str(getattr(current_user, "role", "") or "").strip()

    parts: list[str] = []
    if nickname:
        parts.append(f"昵称：{nickname}")
    if username:
        parts.append(f"用户名：{username}")
    if role:
        parts.append(f"身份：{role}")
    return "\n".join(parts)


async def _load_seed_history(
    db: AsyncSession,
    session_id: str,
    *,
    current_user: User | None,
) -> tuple[Consultation | None, list[dict[str, str]]]:
    """Load DB-backed conversation history for a given session."""
    result = await db.execute(
        select(Consultation).where(Consultation.session_id == session_id)
    )
    consultation = result.scalar_one_or_none()

    if consultation is None:
        return None, []

    consultation_user_id = cast(
        int | None, getattr(
            consultation, "user_id", None))
    if consultation_user_id is not None:
        if current_user is None or consultation_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限访问该咨询会话")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.consultation_id == consultation.id)
        .order_by(ChatMessage.created_at)
    )
    messages = messages_result.scalars().all()

    history = [
        {"role": cast(str, cast(object, m.role)),
         "content": cast(str, cast(object, m.content))}
        for m in messages
    ]
    if len(history) > SEED_HISTORY_MAX_MESSAGES:
        history = history[-SEED_HISTORY_MAX_MESSAGES:]
    return consultation, history


@router.post("/chat", response_model=ChatResponse)
@rate_limit(*RateLimitConfig.AI_CHAT, by_ip=True, by_user=False)
async def chat_with_ai(
    payload: ChatRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(
        get_current_user_optional)] = None,
):
    """
    与AI法律助手对话

    - **message**: 用户消息内容
    - **session_id**: 会话ID（可选，为空则创建新会话）
    - 如果已登录，咨询记录将绑定到用户账号
    """
    started_at = float(time.time())
    request_id = str(getattr(request.state, "request_id", "")
                     or "").strip() or uuid.uuid4().hex
    _ = response.headers.setdefault("X-Request-Id", request_id)
    ai_metrics.record_request("chat")
    client_ip = get_client_ip(request)
    user_id_str = str(current_user.id) if current_user else "guest"

    try:
        if not settings.openai_api_key:
            error_code = ERROR_AI_NOT_CONFIGURED
            message = "AI服务未配置：请设置 OPENAI_API_KEY 后重试"
            ai_metrics.record_error(
                endpoint="chat",
                request_id=request_id,
                error_code=error_code,
                status_code=503,
                message=message,
            )
            critical_event_reporter.fire_and_forget(
                event="ai_not_configured",
                severity="warning",
                request_id=request_id,
                title="AI服务未配置",
                message=message,
                data={
                    "endpoint": "chat",
                    "user_id": user_id_str,
                    "ip": client_ip,
                },
                dedup_key="ai_not_configured",
            )
            _audit_event(
                "chat_error",
                {
                    "request_id": request_id,
                    "endpoint": "chat",
                    "user_id": user_id_str,
                    "ip": client_ip,
                    "session_id": str(payload.session_id or ""),
                    "status_code": 503,
                    "error_code": error_code,
                    "duration_ms": int((time.time() - started_at) * 1000),
                },
            )
            return _make_error_response(
                status_code=503,
                error_code=error_code,
                message=message,
                request_id=request_id,
            )

        if current_user is None:
            await _enforce_guest_ai_quota(request)
        else:
            await quota_service.enforce_ai_chat_quota(db, current_user)

        logger.info(
            "ai_chat_request request_id=%s user_id=%s session_id=%s message=%s",
            request_id,
            user_id_str,
            str(payload.session_id) if payload.session_id else "",
            _audit_text(payload.message),
        )
        _audit_event(
            "chat_request",
            {
                "request_id": request_id,
                "endpoint": "chat",
                "user_id": user_id_str,
                "ip": client_ip,
                "session_id": str(payload.session_id or ""),
            },
        )

        seed_history: list[dict[str, str]] | None = None
        consultation: Consultation | None = None
        if payload.session_id:
            consultation, seed_history = await _load_seed_history(db, payload.session_id, current_user=current_user)

        bucket_seed = f"u:{current_user.id}" if current_user is not None else f"g:{client_ip or request_id}"
        prompt_version = await _select_prompt_version(db, bucket_seed=bucket_seed)

        assistant = _try_get_ai_assistant()
        if assistant is None:
            error_code = ERROR_AI_UNAVAILABLE
            message = "AI服务不可用：缺少可选依赖或配置异常"
            ai_metrics.record_error(
                endpoint="chat",
                request_id=request_id,
                error_code=error_code,
                status_code=503,
                message=message,
            )
            critical_event_reporter.fire_and_forget(
                event="ai_unavailable",
                severity="warning",
                request_id=request_id,
                title="AI服务不可用",
                message=message,
                data={
                    "endpoint": "chat",
                    "user_id": user_id_str,
                    "ip": client_ip,
                },
                dedup_key="ai_unavailable",
            )
            return _make_error_response(
                status_code=503,
                error_code=error_code,
                message=message,
                request_id=request_id,
            )

        user_profile = _build_user_profile(current_user)
        chat_kwargs: dict[str, Any] = {
            "message": payload.message,
            "session_id": payload.session_id,
            "initial_history": seed_history,
        }
        if user_profile and _supports_kwarg(
                getattr(assistant, "chat", None), "user_profile"):
            chat_kwargs["user_profile"] = user_profile
        if _supports_kwarg(getattr(assistant, "chat", None), "prompt_version"):
            chat_kwargs["prompt_version"] = prompt_version

        chat_result: object = await cast(Any, assistant).chat(**chat_kwargs)

        meta: dict[str, Any] = {}
        if not isinstance(chat_result, tuple):
            raise RuntimeError("invalid assistant.chat result")

        if len(chat_result) == 3:
            session_id_obj, answer_obj, references_obj = chat_result
        elif len(chat_result) == 4:
            session_id_obj, answer_obj, references_obj, meta_obj = chat_result
            if isinstance(meta_obj, dict):
                meta = cast(dict[str, Any], meta_obj)
        else:
            raise RuntimeError("invalid assistant.chat result")

        session_id = cast(
            str, session_id_obj) if isinstance(
            session_id_obj, str) else str(session_id_obj)
        answer = cast(
            str, answer_obj) if isinstance(
            answer_obj, str) else str(answer_obj)
        references: list[Any] = cast(
            list[Any], references_obj) if isinstance(
            references_obj, list) else []

        if consultation is None:
            result = await db.execute(
                select(Consultation).where(
                    Consultation.session_id == session_id)
            )
            consultation = result.scalar_one_or_none()

            if consultation is not None:
                consultation_user_id = cast(
                    int | None, getattr(
                        consultation, "user_id", None))
                if consultation_user_id is not None:
                    if current_user is None or consultation_user_id != current_user.id:
                        raise HTTPException(
                            status_code=403, detail="无权限访问该咨询会话")

        if not consultation:
            consultation = Consultation(
                session_id=session_id,
                title=payload.message[:50] +
                "..." if len(payload.message) > 50 else payload.message,
                user_id=current_user.id if current_user else None,
            )
            db.add(consultation)
            await db.flush()
        else:
            consultation_user_id = cast(
                int | None, getattr(
                    consultation, "user_id", None))
            if current_user is not None and consultation_user_id is None:
                setattr(consultation, "user_id", current_user.id)

        user_message = ChatMessage(
            consultation_id=consultation.id,
            role="user",
            content=payload.message,
        )
        db.add(user_message)

        references_list = [ref.model_dump() for ref in references]
        meta_to_save: dict[str, object] = {}
        if isinstance(meta, dict):
            meta_to_save.update(meta)
        meta_to_save.setdefault("prompt_version", str(prompt_version or "v1"))
        meta_to_save.setdefault(
            "duration_ms", int(
                (time.time() - started_at) * 1000))
        meta_to_save.setdefault("request_id", str(request_id))

        refs_json = json.dumps(
            {"references": references_list, "meta": meta_to_save},
            ensure_ascii=False,
        )
        ai_message = ChatMessage(
            consultation_id=consultation.id,
            role="assistant",
            content=answer,
            references=refs_json,
        )
        db.add(ai_message)

        await db.flush()
        assistant_message_id = cast(
            int | None, getattr(
                ai_message, "id", None))

        await db.commit()

        if current_user is not None:
            try:
                await quota_service.record_ai_chat_usage(db, current_user)
            except Exception:
                logger.exception(
                    "quota_consume_failed request_id=%s", request_id)

        logger.info(
            "ai_chat_response request_id=%s user_id=%s session_id=%s assistant_message_id=%s",
            request_id,
            user_id_str,
            str(session_id),
            str(assistant_message_id) if assistant_message_id is not None else "",
        )

        _audit_event(
            "chat_done",
            {
                "request_id": request_id,
                "endpoint": "chat",
                "user_id": user_id_str,
                "ip": client_ip,
                "session_id": str(session_id),
                "assistant_message_id": int(assistant_message_id) if assistant_message_id is not None else None,
                "strategy_used": meta.get("strategy_used"),
                "risk_level": meta.get("risk_level"),
                "duration_ms": int(
                    (time.time() - started_at) * 1000),
            },
        )

        search_quality_raw = meta.get("search_quality")
        search_quality = (
            SearchQualityInfo.model_validate(search_quality_raw)
            if isinstance(search_quality_raw, dict)
            else None
        )

        # 提取话题和工具用于质量监控
        intent = cast(str | None, meta.get("intent"))
        strategy_used = cast(str | None, meta.get("strategy_used"))

        # 话题分类
        topics: list[str] = []
        if intent:
            topics = [intent]
        elif payload.message:
            msg_lower = payload.message.lower()
            if any(kw in msg_lower for kw in [
                   "劳动", "工资", "合同", "解雇", "赔偿", "补偿"]):
                topics = ["劳动法"]
            elif any(kw in msg_lower for kw in ["离婚", "财产", "抚养", "结婚", "继承", "遗嘱"]):
                topics = ["婚姻家庭"]
            elif any(kw in msg_lower for kw in ["赔偿", "事故", "伤害", "医疗", "侵权"]):
                topics = ["侵权赔偿"]
            elif any(kw in msg_lower for kw in ["房产", "租房", "买卖", "物业", "租赁"]):
                topics = ["房产纠纷"]
            elif any(kw in msg_lower for kw in ["刑事", "犯罪", "拘留", "逮捕", "判刑"]):
                topics = ["刑事辩护"]
            elif any(kw in msg_lower for kw in ["行政", "复议", "诉讼", "处罚"]):
                topics = ["行政诉讼"]
            else:
                topics = ["其他"]

        # 工具使用
        tools_used: list[str] = []
        if strategy_used:
            tools_used = [strategy_used]

        # 记录AI质量监控日志
        response_time_ms = int((time.time() - started_at) * 1000)
        log_success = False
        log_error_msg = None
        try:
            from ...middleware.ai_quality_middleware import get_ai_logger
            ai_logger = get_ai_logger()
            if ai_logger is not None:
                ai_logger.log_conversation(
                    request_id=request_id,
                    session_id=session_id,
                    user_id=current_user.id if current_user else None,
                    message_length=len(payload.message),
                    response_length=len(answer),
                    response_time_ms=response_time_ms,
                    quality_score=None,
                    topics=topics,
                    tools_used=tools_used,
                    token_usage=None,
                )
                log_success = True
        except Exception as e:
            log_error_msg = str(e)
            logger.warning(f"AI质量日志记录失败: {e}")

        if not log_success:
            logger.warning(
                f"AI质量日志记录跳过 - request_id: {request_id}, session_id: {session_id}, "
                f"error: {log_error_msg or 'unknown'}"
            )

        return ChatResponse(
            session_id=session_id,
            answer=answer,
            references=references,
            assistant_message_id=assistant_message_id,
            strategy_used=cast(
                str | None, meta.get("strategy_used")) if isinstance(
                meta.get("strategy_used"), str) else None,
            strategy_reason=cast(
                str | None, meta.get("strategy_reason")) if isinstance(
                meta.get("strategy_reason"), str) else None,
            confidence=cast(
                str | None,
                meta.get("confidence")) if isinstance(
                meta.get("confidence"),
                str) else None,
            risk_level=cast(
                str | None,
                meta.get("risk_level")) if isinstance(
                meta.get("risk_level"),
                str) else None,
            search_quality=search_quality,
            disclaimer=cast(
                str | None,
                meta.get("disclaimer")) if isinstance(
                meta.get("disclaimer"),
                str) else None,
            model_used=cast(
                str | None,
                meta.get("model_used")) if isinstance(
                meta.get("model_used"),
                str) else None,
            fallback_used=cast(
                bool | None,
                meta.get("fallback_used")) if isinstance(
                meta.get("fallback_used"),
                bool) else None,
            model_attempts=cast(list[str] | None, meta.get("model_attempts"))
            if isinstance(meta.get("model_attempts"), list)
            else None,
            intent=cast(
                str | None,
                meta.get("intent")) if isinstance(
                meta.get("intent"),
                str) else None,
            needs_clarification=cast(
                bool | None, meta.get("needs_clarification")) if isinstance(
                meta.get("needs_clarification"), bool) else None,
            clarifying_questions=cast(
                list[str] | None, meta.get("clarifying_questions"))
            if isinstance(meta.get("clarifying_questions"), list)
            else None,
            created_at=datetime.now(),
        )
    except HTTPException as e:
        sc = int(e.status_code)
        error_code = _error_code_for_http(sc)
        message = _extract_message(getattr(e, "detail", ""))
        ai_metrics.record_error(
            endpoint="chat",
            request_id=request_id,
            error_code=error_code,
            status_code=sc,
            message=message,
        )

        # 记录AI质量监控错误日志
        response_time_ms = int((time.time() - started_at) * 1000)
        try:
            from ...middleware.ai_quality_middleware import get_ai_logger
            ai_logger = get_ai_logger()
            if ai_logger is not None:
                ai_logger.log_conversation(
                    request_id=request_id,
                    session_id=str(payload.session_id or ""),
                    user_id=current_user.id if current_user else None,
                    message_length=len(
                        payload.message) if payload.message else 0,
                    response_length=0,
                    response_time_ms=response_time_ms,
                    error_type=error_code,
                    topics=[],  # 无法从异常中提取topics
                )
        except Exception as log_err:
            logger.warning(f"AI质量错误日志记录失败: {log_err}")
            critical_event_reporter.fire_and_forget(
                event="ai_http_exception",
                severity="error",
                request_id=request_id,
                title="AI接口异常",
                message=message,
                data={
                    "endpoint": "chat",
                    "user_id": user_id_str,
                    "ip": client_ip,
                },
                dedup_key="ai_http_exception|chat",
            )
        _audit_event(
            "chat_error",
            {
                "request_id": request_id,
                "endpoint": "chat",
                "user_id": user_id_str,
                "ip": client_ip,
                "session_id": str(payload.session_id or ""),
                "status_code": sc,
                "error_code": error_code,
                "duration_ms": int((time.time() - started_at) * 1000),
            },
        )
        extra_headers = cast(dict[str, str] | None,
                             getattr(e, "headers", None))
        return _make_error_response(
            status_code=sc,
            error_code=error_code,
            message=message,
            request_id=request_id,
            headers=extra_headers,
        )
    except Exception as e:
        logger.exception("ai_chat_unhandled request_id=%s", request_id)
        error_code = ERROR_AI_INTERNAL_ERROR
        message = "AI服务异常，请稍后重试"
        ai_metrics.record_error(
            endpoint="chat",
            request_id=request_id,
            error_code=error_code,
            status_code=500,
            message=str(e),
        )

        # 记录AI质量监控错误日志
        response_time_ms = int((time.time() - started_at) * 1000)
        try:
            from ...middleware.ai_quality_middleware import get_ai_logger
            ai_logger = get_ai_logger()
            if ai_logger is not None:
                ai_logger.log_conversation(
                    request_id=request_id,
                    session_id=str(payload.session_id or ""),
                    user_id=current_user.id if current_user else None,
                    message_length=len(
                        payload.message) if payload.message else 0,
                    response_length=0,
                    response_time_ms=response_time_ms,
                    error_type=error_code,
                    topics=[],
                )
        except Exception as log_err:
            logger.warning(f"AI质量未处理异常日志记录失败: {log_err}")
        critical_event_reporter.fire_and_forget(
            event="ai_unhandled_exception",
            severity="error",
            request_id=request_id,
            title="AI未处理异常",
            message=str(e),
            data={
                "endpoint": "chat",
                "user_id": user_id_str,
                "ip": client_ip,
            },
            dedup_key="ai_unhandled_exception|chat",
        )
        _audit_event(
            "chat_error",
            {
                "request_id": request_id,
                "endpoint": "chat",
                "user_id": user_id_str,
                "ip": client_ip,
                "session_id": str(payload.session_id or ""),
                "status_code": 500,
                "error_code": error_code,
                "duration_ms": int((time.time() - started_at) * 1000),
            },
        )
        return _make_error_response(
            status_code=500,
            error_code=error_code,
            message=message,
            request_id=request_id,
        )


@router.post("/chat/stream")
@rate_limit(*RateLimitConfig.AI_CHAT, by_ip=True, by_user=False)
async def chat_with_ai_stream(
    payload: ChatRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(
        get_current_user_optional)] = None,
):
    """
    流式对话（SSE）

    返回Server-Sent Events流，包含：
    - session: 会话ID
    - references: 法律引用
    - content: 回答内容片段
    - done: 完成信号
    """
    started_at = float(time.time())
    request_id = str(getattr(request.state, "request_id", "")
                     or "").strip() or uuid.uuid4().hex
    ai_metrics.record_request("chat_stream")
    client_ip = get_client_ip(request)

    current_user_id: int | None = None
    if current_user is not None:
        try:
            identity = inspect(current_user).identity
            if identity:
                current_user_id = cast(int | None, identity[0])
        except Exception:
            current_user_id = None

    user_id_str = str(
        current_user_id) if current_user_id is not None else "guest"

    e2e_mock_enabled = bool(settings.debug) and str(
        request.headers.get("X-E2E-Mock-AI") or "").strip() == "1"
    if e2e_mock_enabled:
        forced_persist_error = str(request.headers.get(
            "X-E2E-Force-Persist-Error") or "").strip()
        e2e_stream_scenario = str(request.headers.get(
            "X-E2E-Stream-Scenario") or "").strip().lower()

        async def event_generator():
            session_id = str(payload.session_id or "").strip() or f"e2e_{uuid.uuid4().hex}"
            yield f"event: session\ndata: {json.dumps({'session_id': session_id}, ensure_ascii=False)}\n\n"

            thinking_steps = [
                {
                    "type": "intent",
                    "title": "识别用户意图",
                    "content": "理解用户的问题类型与诉求重点。",
                },
                {
                    "type": "retrieval",
                    "title": "检索相关法条",
                    "content": "匹配可能适用的法律条文与关键词。",
                },
                {
                    "type": "analysis",
                    "title": "归纳要点并分析",
                    "content": "梳理事实要点，给出可执行的建议路径。",
                },
                {
                    "type": "generation",
                    "title": "生成回复",
                    "content": "输出结构化答复与注意事项。",
                },
            ]
            yield f"event: thinking\ndata: {json.dumps({'steps': thinking_steps, 'is_thinking': True}, ensure_ascii=False)}\n\n"

            refs = [
                {
                    "law_name": "民法典",
                    "article": "第1条",
                    "content": "为了保护民事主体的合法权益，调整民事关系，维护社会和经济秩序，适应中国特色社会主义发展要求，弘扬社会主义核心价值观，根据宪法，制定本法。",
                    "relevance": 0.92,
                }]
            yield f"event: references\ndata: {json.dumps({'references': refs}, ensure_ascii=False)}\n\n"

            # 生成行动卡建议
            actions = [
                {
                    "id": "generate_document",
                    "type": "action",
                    "label": "生成文书",
                    "description": "根据对话内容生成法律文书",
                    "icon": "file-text",
                    "priority": "high",
                    "payload": {"template_type": "legal_opinion"}
                },
                {
                    "id": "search_lawyer",
                    "type": "action",
                    "label": "搜索律师",
                    "description": "查找适合的律师资源",
                    "icon": "search",
                    "priority": "medium",
                    "payload": {"specialty": "劳动纠纷"}
                }
            ]
            yield f"event: actions\ndata: {json.dumps({'actions': actions}, ensure_ascii=False)}\n\n"

            if e2e_stream_scenario == "scroll":
                scroll_intro = "根据《民法典》第1条，以下为滚动测试内容：\n"
                yield f"event: content\ndata: {json.dumps({'text': scroll_intro}, ensure_ascii=False)}\n\n"

                lines = [f"{i}-内容\n" for i in range(1, 201)]
                batch_size = 12
                for batch_start in range(0, len(lines), batch_size):
                    batch_text = "".join(
                        lines[batch_start: batch_start + batch_size])
                    yield f"event: content\ndata: {json.dumps({'text': batch_text}, ensure_ascii=False)}\n\n"

                    if batch_start == batch_size * 4:
                        await asyncio.sleep(0.9)
                    else:
                        await asyncio.sleep(0.02)
            else:
                yield f"event: content\ndata: {json.dumps({'text': '根据《民法典》第1条，给您一个示例回复。'}, ensure_ascii=False)}\n\n"

            final_done: dict[str, object] = {
                "session_id": session_id,
                "assistant_message_id": 1,
                "request_id": request_id,
            }

            if forced_persist_error:
                final_done["persist_error"] = forced_persist_error

            persist_error_code: str | None = None
            if forced_persist_error == "stream_failed":
                persist_error_code = "AI_STREAM_FAILED"
            elif forced_persist_error == "persist_failed":
                persist_error_code = "AI_PERSIST_FAILED"
            elif forced_persist_error == "persist_forbidden":
                persist_error_code = "AI_PERSIST_FORBIDDEN"
            if persist_error_code is not None:
                final_done["error_code"] = persist_error_code

            yield f"event: done\ndata: {json.dumps(final_done, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Encoding": "identity",
                "X-Request-Id": request_id,
            },
        )

    try:
        if not settings.openai_api_key:
            error_code = ERROR_AI_NOT_CONFIGURED
            message = "AI服务未配置：请设置 OPENAI_API_KEY 后重试"
            ai_metrics.record_error(
                endpoint="chat_stream",
                request_id=request_id,
                error_code=error_code,
                status_code=503,
                message=message,
            )
            critical_event_reporter.fire_and_forget(
                event="ai_not_configured",
                severity="warning",
                request_id=request_id,
                title="AI服务未配置",
                message=message,
                data={
                    "endpoint": "chat_stream",
                    "user_id": user_id_str,
                    "ip": client_ip,
                },
                dedup_key="ai_not_configured",
            )
            _audit_event(
                "chat_stream_error",
                {
                    "request_id": request_id,
                    "endpoint": "chat_stream",
                    "user_id": user_id_str,
                    "ip": client_ip,
                    "session_id": str(payload.session_id or ""),
                    "status_code": 503,
                    "error_code": error_code,
                    "duration_ms": int((time.time() - started_at) * 1000),
                },
            )
            return _make_error_response(
                status_code=503,
                error_code=error_code,
                message=message,
                request_id=request_id,
            )

        if current_user is None:
            await _enforce_guest_ai_quota(request)
        else:
            await quota_service.enforce_ai_chat_quota(db, current_user)

        logger.info(
            "ai_chat_stream_request request_id=%s user_id=%s session_id=%s message=%s",
            request_id,
            user_id_str,
            str(payload.session_id) if payload.session_id else "",
            _audit_text(payload.message),
        )
        _audit_event(
            "chat_stream_request",
            {
                "request_id": request_id,
                "endpoint": "chat_stream",
                "user_id": user_id_str,
                "ip": client_ip,
                "session_id": str(payload.session_id or ""),
            },
        )

        bucket_seed = f"u:{current_user_id}" if current_user_id is not None else f"g:{client_ip or request_id}"
        prompt_version = await _select_prompt_version(db, bucket_seed=bucket_seed)

        seed_history: list[dict[str, str]] | None = None
        if payload.session_id:
            _, seed_history = await _load_seed_history(db, payload.session_id, current_user=current_user)

        assistant = _try_get_ai_assistant()
        if assistant is None:
            error_code = ERROR_AI_UNAVAILABLE
            message = "AI服务不可用：缺少可选依赖或配置异常"
            ai_metrics.record_error(
                endpoint="chat_stream",
                request_id=request_id,
                error_code=error_code,
                status_code=503,
                message=message,
            )
            critical_event_reporter.fire_and_forget(
                event="ai_unavailable",
                severity="warning",
                request_id=request_id,
                title="AI服务不可用",
                message=message,
                data={
                    "endpoint": "chat_stream",
                    "user_id": user_id_str,
                    "ip": client_ip,
                },
                dedup_key="ai_unavailable",
            )
            return _make_error_response(
                status_code=503,
                error_code=error_code,
                message=message,
                request_id=request_id,
            )

        if current_user is not None:
            try:
                await quota_service.record_ai_chat_usage(db, current_user)
            except Exception:
                logger.exception(
                    "quota_consume_failed request_id=%s", request_id)

        async def event_generator():
            session_id: str | None = None
            references_payload: list[dict[str, object]] | None = None
            answer_parts: list[str] = []
            done_payload: dict[str, object] | None = None

            assistant_message_id: int | None = None
            persist_error: str | None = None

            try:
                user_profile = _build_user_profile(current_user)
                stream_kwargs: dict[str, object] = {
                    "message": payload.message,
                    "session_id": payload.session_id,
                    "initial_history": seed_history,
                }
                if user_profile and _supports_kwarg(
                        getattr(
                            assistant,
                            "chat_stream",
                            None),
                        "user_profile"):
                    stream_kwargs["user_profile"] = user_profile
                if _supports_kwarg(
                        getattr(
                            assistant,
                            "chat_stream",
                            None),
                        "prompt_version"):
                    stream_kwargs["prompt_version"] = prompt_version

                async for event_type, data in assistant.chat_stream(**cast(dict, stream_kwargs)):
                    if event_type == "session":
                        session_id = cast(str | None, data.get("session_id"))
                    elif event_type == "references":
                        references_payload = cast(
                            list[dict[str, object]] | None, data.get("references"))
                    elif event_type == "content":
                        chunk = cast(str | None, data.get("text"))
                        if chunk:
                            answer_parts.append(chunk)

                    if event_type == "done":
                        done_payload = data
                        continue

                    yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            except asyncio.CancelledError:
                raise
            except Exception:
                persist_error = "stream_failed"

            if session_id is None:
                session_id = payload.session_id

            if session_id is None:
                if persist_error is None:
                    persist_error = "stream_failed"
            else:
                try:
                    result = await db.execute(
                        select(Consultation).where(
                            Consultation.session_id == session_id)
                    )
                    consultation = result.scalar_one_or_none()

                    if consultation is not None:
                        consultation_user_id = cast(
                            int | None, getattr(
                                consultation, "user_id", None))
                        if consultation_user_id is not None:
                            if current_user_id is None or consultation_user_id != current_user_id:
                                if persist_error is None:
                                    persist_error = "persist_forbidden"
                                raise PermissionError("persist forbidden")

                    if not consultation:
                        consultation = Consultation(
                            session_id=session_id,
                            title=payload.message[:50] + "..." if len(
                                payload.message) > 50 else payload.message,
                            user_id=current_user_id,
                        )
                        db.add(consultation)
                        await db.flush()
                    else:
                        consultation_user_id = cast(
                            int | None, getattr(
                                consultation, "user_id", None))
                        if current_user_id is not None and consultation_user_id is None:
                            setattr(consultation, "user_id", current_user_id)

                    user_message = ChatMessage(
                        consultation_id=consultation.id,
                        role="user",
                        content=payload.message,
                    )
                    db.add(user_message)

                    meta_to_save: dict[str, object] = {}
                    if isinstance(done_payload, dict):
                        for k in (
                            "strategy_used",
                            "strategy_reason",
                            "confidence",
                            "risk_level",
                            "prompt_version",
                            "intent",
                            "needs_clarification",
                            "model_used",
                            "fallback_used",
                            "model_attempts",
                            "prompt_tokens",
                            "completion_tokens",
                            "total_tokens",
                            "estimated_cost_usd",
                        ):
                            if k in done_payload:
                                meta_to_save[k] = cast(
                                    object, done_payload.get(k))
                    meta_to_save.setdefault(
                        "prompt_version", str(
                            prompt_version or "v1"))
                    meta_to_save.setdefault(
                        "duration_ms", int(
                            (time.time() - started_at) * 1000))
                    meta_to_save.setdefault("request_id", str(request_id))

                    refs_json = json.dumps(
                        {"references": references_payload or [],
                            "meta": meta_to_save},
                        ensure_ascii=False,
                    )
                    ai_message = ChatMessage(
                        consultation_id=consultation.id,
                        role="assistant",
                        content="".join(answer_parts),
                        references=refs_json,
                    )
                    db.add(ai_message)

                    await db.flush()
                    assistant_message_id = cast(
                        int | None, getattr(ai_message, "id", None))

                    await db.commit()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    await db.rollback()
                    if persist_error is None:
                        persist_error = "persist_failed"

            final_done: dict[str, object] = {}
            if done_payload:
                final_done.update(done_payload)
            final_done["session_id"] = session_id
            if assistant_message_id is not None:
                final_done["assistant_message_id"] = assistant_message_id
            if persist_error is not None:
                final_done["persist_error"] = persist_error

            final_done["request_id"] = request_id

            persist_error_code: str | None = None
            if persist_error == "stream_failed":
                persist_error_code = "AI_STREAM_FAILED"
            elif persist_error == "persist_failed":
                persist_error_code = "AI_PERSIST_FAILED"
            elif persist_error == "persist_forbidden":
                persist_error_code = "AI_PERSIST_FORBIDDEN"
            if persist_error_code is not None:
                final_done["error_code"] = persist_error_code
                ai_metrics.record_error(
                    endpoint="chat_stream",
                    request_id=request_id,
                    error_code=persist_error_code,
                    status_code=200,
                    message=persist_error,
                )

            logger.info(
                "ai_chat_stream_done request_id=%s user_id=%s session_id=%s assistant_message_id=%s persist_error=%s",
                request_id,
                user_id_str,
                str(session_id) if session_id is not None else "",
                str(assistant_message_id) if assistant_message_id is not None else "",
                str(persist_error) if persist_error is not None else "",
            )

            _audit_event(
                "chat_stream_done",
                {
                    "request_id": request_id,
                    "endpoint": "chat_stream",
                    "user_id": user_id_str,
                    "ip": client_ip,
                    "session_id": str(session_id) if session_id is not None else "",
                    "assistant_message_id": int(assistant_message_id) if assistant_message_id is not None else None,
                    "persist_error": str(persist_error) if persist_error is not None else None,
                    "persist_error_code": persist_error_code,
                    "duration_ms": int(
                        (time.time() - started_at) * 1000),
                },
            )

            yield f"event: done\ndata: {json.dumps(final_done, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Encoding": "identity",
                "X-Request-Id": request_id,
            },
        )
    except HTTPException as e:
        sc = int(getattr(e, "status_code", 500) or 500)
        error_code = _error_code_for_http(sc)
        message = _extract_message(getattr(e, "detail", ""))
        ai_metrics.record_error(
            endpoint="chat_stream",
            request_id=request_id,
            error_code=error_code,
            status_code=sc,
            message=message,
        )
        if sc >= 500:
            critical_event_reporter.fire_and_forget(
                event="ai_http_exception",
                severity="error",
                request_id=request_id,
                title="AI接口异常",
                message=message,
                data={
                    "endpoint": "chat_stream",
                    "status_code": sc,
                    "error_code": error_code,
                    "user_id": user_id_str,
                    "ip": client_ip,
                },
                dedup_key=f"ai_http_exception|chat_stream|{sc}|{error_code}",
            )
        _audit_event(
            "chat_stream_error",
            {
                "request_id": request_id,
                "endpoint": "chat_stream",
                "user_id": user_id_str,
                "ip": client_ip,
                "session_id": str(payload.session_id or ""),
                "status_code": sc,
                "error_code": error_code,
                "duration_ms": int((time.time() - started_at) * 1000),
            },
        )
        extra_headers = cast(dict[str, str] | None,
                             getattr(e, "headers", None))
        return _make_error_response(
            status_code=sc,
            error_code=error_code,
            message=message,
            request_id=request_id,
            headers=extra_headers,
        )
    except Exception as e:
        logger.exception("ai_chat_stream_unhandled request_id=%s", request_id)
        error_code = ERROR_AI_INTERNAL_ERROR
        message = "AI服务异常，请稍后重试"
        ai_metrics.record_error(
            endpoint="chat_stream",
            request_id=request_id,
            error_code=error_code,
            status_code=500,
            message=str(e),
        )
        critical_event_reporter.fire_and_forget(
            event="ai_unhandled_exception",
            severity="error",
            request_id=request_id,
            title="AI未处理异常",
            message=str(e),
            data={
                "endpoint": "chat_stream",
                "user_id": user_id_str,
                "ip": client_ip,
            },
            dedup_key="ai_unhandled_exception|chat_stream",
        )
        _audit_event(
            "chat_stream_error",
            {
                "request_id": request_id,
                "endpoint": "chat_stream",
                "user_id": user_id_str,
                "ip": client_ip,
                "session_id": str(payload.session_id or ""),
                "status_code": 500,
                "error_code": error_code,
                "duration_ms": int((time.time() - started_at) * 1000),
            },
        )
        return _make_error_response(
            status_code=500,
            error_code=error_code,
            message=message,
            request_id=request_id,
        )
