"""AI transcription routes

Provides speech-to-text endpoints - audio transcription using OpenAI Whisper or Sherpa-ONNX
"""
import asyncio
import io
import json
import logging
import os
import time
import uuid
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect

from ...config import get_settings
from ...database import get_db
from ...models.user import User
from ...schemas.ai import TranscribeResponse
from ...services.ai_metrics import ai_metrics
from ...services.critical_event_reporter import critical_event_reporter
from ...utils.deps import get_current_user_optional
from ...utils.helpers import _get_int_env
from ...utils.rate_limiter import rate_limit, RateLimitConfig, get_client_ip

router = APIRouter(prefix="/ai/transcribe", tags=["AI语音转写"])

settings = get_settings()
logger = logging.getLogger(__name__)

ERROR_AI_NOT_CONFIGURED = "AI_NOT_CONFIGURED"
ERROR_AI_UNAVAILABLE = "AI_UNAVAILABLE"
ERROR_AI_RATE_LIMITED = "AI_RATE_LIMITED"
ERROR_AI_FORBIDDEN = "AI_FORBIDDEN"
ERROR_AI_UNAUTHORIZED = "AI_UNAUTHORIZED"
ERROR_AI_BAD_REQUEST = "AI_BAD_REQUEST"
ERROR_AI_INTERNAL_ERROR = "AI_INTERNAL_ERROR"


GUEST_AI_LIMIT = _get_int_env("GUEST_AI_LIMIT", 3)
GUEST_AI_WINDOW_SECONDS = _get_int_env("GUEST_AI_WINDOW_SECONDS", 60 * 60 * 24)


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


def _audit_event(event: str, payload: dict[str, object]) -> None:
    try:
        logger.info(
            "ai_audit event=%s payload=%s",
            str(event),
            json.dumps(
                payload,
                ensure_ascii=False))
    except Exception:
        logger.exception("ai_audit event logging failed: %s", str(event))


async def _enforce_guest_ai_quota(request: Request) -> None:
    from ...utils.rate_limiter import rate_limiter
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


@router.post("", response_model=TranscribeResponse)
@rate_limit(*RateLimitConfig.AI_CHAT, by_ip=True, by_user=False)
async def transcribe(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File(...)],
    segment_index: Annotated[int | None, Form()] = None,
    is_final: Annotated[bool | None, Form()] = None,
    current_user: Annotated[User | None, Depends(
        get_current_user_optional)] = None,
    db: Annotated[AsyncSession | None, Depends(get_db)] = None,
):
    started_at = float(time.time())
    request_id = str(getattr(request.state, "request_id", "")
                     or "").strip() or uuid.uuid4().hex
    ai_metrics.record_request("transcribe")
    client_ip = get_client_ip(request)

    current_user_id: int | None = None
    if current_user is not None:
        try:
            identity = inspect(current_user).identity
            if identity:
                current_user_id = cast(int | None, identity[0])
        except Exception:
            logger.exception("Failed to get current_user_id from identity")
            current_user_id = None

    user_id_str = str(
        current_user_id) if current_user_id is not None else "guest"

    e2e_mock_enabled = bool(settings.debug) and str(
        request.headers.get("X-E2E-Mock-AI") or "").strip() == "1"
    if e2e_mock_enabled:
        try:
            _ = await file.read()
        except Exception:
            logger.exception("E2E mock file read failed")
        _ = response.headers.setdefault("X-Request-Id", request_id)
        return TranscribeResponse(
            text="这是一个E2E mock 的语音转写结果",
            segment_index=segment_index,
            is_final=is_final,
        )

    try:
        from ...services.sherpa_asr_service import sherpa_is_ready, sherpa_transcribe
        from ...services.voice_config_service import get_effective_voice_settings

        effective_settings = settings
        voice_cfg_overrides: dict[str, str] = {}
        voice_forced = False
        if db is not None:
            try:
                effective_settings, voice_cfg_overrides, voice_forced = await get_effective_voice_settings(db, settings)
            except Exception:
                logger.exception("Failed to get effective voice settings")
                effective_settings = settings
                voice_cfg_overrides = {}
                voice_forced = False

        if voice_forced:
            response.headers.setdefault("X-Voice-Config-Forced", "1")

        provider_raw = str(
            getattr(
                effective_settings,
                "voice_transcribe_provider",
                "auto") or "").strip().lower()
        provider = provider_raw if provider_raw in {
            "auto", "openai", "sherpa"} else "auto"

        transcribe_api_key = str(
            getattr(
                settings,
                "openai_transcribe_api_key",
                "") or "").strip()
        transcribe_base_url = str(
            getattr(
                settings,
                "openai_transcribe_base_url",
                "") or "").strip()
        default_api_key = str(settings.openai_api_key or "").strip()
        default_base_url = str(settings.openai_base_url or "").strip()

        api_key_to_use = transcribe_api_key or default_api_key
        base_url_to_use = transcribe_base_url or default_base_url

        sherpa_ready = False
        try:
            sherpa_ready = bool(sherpa_is_ready(effective_settings))
        except Exception:
            logger.exception("Sherpa ASR readiness check failed")
            sherpa_ready = False

        official_openai_base = "https://api.openai.com/v1"
        base_norm = (str(base_url_to_use or official_openai_base).strip()
                     or official_openai_base).rstrip("/")
        openai_ready = bool(api_key_to_use) and (
            bool(transcribe_base_url)
            or base_norm == official_openai_base
            or bool(transcribe_api_key)
        )

        sherpa_enabled_flag = bool(
            getattr(
                effective_settings,
                "sherpa_asr_enabled",
                False))
        sherpa_mode_raw = str(
            getattr(
                effective_settings,
                "sherpa_asr_mode",
                "off") or "").strip().lower()
        sherpa_mode = sherpa_mode_raw if sherpa_mode_raw in {
            "off", "local", "remote"} else "off"

        diag_headers: dict[str, str] = {
            "X-AI-Voice-Provider-Configured": str(provider),
            "X-AI-Voice-OpenAI-Ready": "1" if openai_ready else "0",
            "X-AI-Voice-Sherpa-Enabled": "1" if sherpa_enabled_flag else "0",
            "X-AI-Voice-Sherpa-Mode": str(sherpa_mode),
            "X-AI-Voice-Sherpa-Ready": "1" if sherpa_ready else "0",
        }
        if voice_forced:
            diag_headers["X-Voice-Config-Forced"] = "1"

        if provider == "openai" and not openai_ready:
            error_code = ERROR_AI_NOT_CONFIGURED
            message = "AI服务未配置：请设置 OPENAI_TRANSCRIBE_API_KEY 或 OPENAI_API_KEY 后重试"
            ai_metrics.record_error(
                endpoint="transcribe",
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
                    "endpoint": "transcribe",
                    "user_id": user_id_str,
                    "ip": client_ip,
                },
                dedup_key="ai_not_configured",
            )
            _audit_event(
                "transcribe_error",
                {
                    "request_id": request_id,
                    "endpoint": "transcribe",
                    "user_id": user_id_str,
                    "ip": client_ip,
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
                headers=diag_headers,
            )

        if provider == "sherpa" and not sherpa_ready:
            error_code = ERROR_AI_NOT_CONFIGURED
            message = (
                "AI服务未配置：Sherpa 未就绪。"
                " 请确认：1) SHERPA_ASR_ENABLED=1；2) SHERPA_ASR_MODE=local/remote（当前为 %s）；"
                " 3) remote 模式需配置 SHERPA_ASR_REMOTE_URL，local 模式需配置 tokens+model 路径。"
            ) % (sherpa_mode,)
            ai_metrics.record_error(
                endpoint="transcribe",
                request_id=request_id,
                error_code=error_code,
                status_code=503,
                message=message,
            )
            return _make_error_response(
                status_code=503,
                error_code=error_code,
                message=message,
                request_id=request_id,
                headers=diag_headers,
            )

        if provider == "auto" and not openai_ready and not sherpa_ready:
            error_code = ERROR_AI_NOT_CONFIGURED
            message = "AI服务未配置：请设置 OPENAI_TRANSCRIBE_API_KEY/OPENAI_API_KEY 或启用 Sherpa-ONNX 后重试"
            ai_metrics.record_error(
                endpoint="transcribe",
                request_id=request_id,
                error_code=error_code,
                status_code=503,
                message=message,
            )
            return _make_error_response(
                status_code=503,
                error_code=error_code,
                message=message,
                request_id=request_id,
                headers=diag_headers,
            )

        if current_user is None:
            await _enforce_guest_ai_quota(request)

        content = await file.read()
        if not content:
            return _make_error_response(
                status_code=400,
                error_code=ERROR_AI_BAD_REQUEST,
                message="音频文件为空",
                request_id=request_id,
            )

        if len(content) > 10 * 1024 * 1024:
            return _make_error_response(
                status_code=400,
                error_code=ERROR_AI_BAD_REQUEST,
                message="音频文件大小不能超过 10MB",
                request_id=request_id,
            )

        filename = str(file.filename or "audio").strip() or "audio"
        safe_filename = "".join(
            ch if (
                "0" <= ch <= "9") or (
                "A" <= ch <= "Z") or (
                "a" <= ch <= "z") or ch in (
                "-",
                "_",
                ".") else "_"
            for ch in filename
        ).strip("._")
        if not safe_filename:
            safe_filename = "audio"
        filename = safe_filename

        ext = (filename.rsplit(".", 1)
               [-1] if "." in filename else "").lower().strip()
        allowed_ext = {
            "wav",
            "mp3",
            "m4a",
            "ogg",
            "webm",
            "opus",
            "mp4",
            "aac",
            "mpeg"}
        if ext and ext not in allowed_ext:
            return _make_error_response(
                status_code=400,
                error_code=ERROR_AI_BAD_REQUEST,
                message="音频格式不支持",
                request_id=request_id,
            )

        openai_error: Exception | None = None
        if provider in {"auto", "openai"} and openai_ready:
            try:
                def _transcribe_sync() -> tuple[str, str | None, bool]:
                    from openai import OpenAI

                    official_base = "https://api.openai.com/v1"
                    primary_base = str(
                        base_url_to_use or "").strip() or official_base
                    bases: list[str]
                    if bool(transcribe_api_key) and (
                            not str(transcribe_base_url or "").strip()):
                        bases = [official_base]
                        if primary_base.rstrip("/") != official_base:
                            bases.append(primary_base)
                    else:
                        bases = [primary_base]
                        allow_official_fallback = bool(
                            transcribe_api_key) and primary_base.rstrip("/") != official_base
                        if allow_official_fallback:
                            bases.append(official_base)

                    last_err: Exception | None = None

                    used_base: str | None = None
                    used_fallback: bool = False

                    for base_url in bases:
                        try:
                            used_base = base_url
                            used_fallback = base_url.rstrip(
                                "/") == official_base and primary_base.rstrip("/") != official_base
                            client = OpenAI(
                                api_key=api_key_to_use, base_url=base_url)
                            buf = io.BytesIO(content)
                            try:
                                setattr(buf, "name", filename)
                            except Exception:
                                pass
                            res = client.audio.transcriptions.create(
                                model="whisper-1", file=buf)
                            return str(getattr(res, "text", "")
                                       or ""), used_base, used_fallback
                        except Exception as e:
                            last_err = e

                    if last_err is not None:
                        raise last_err
                    return "", used_base, used_fallback

                text, used_base, used_fallback = await asyncio.to_thread(_transcribe_sync)
                response.headers.setdefault(
                    "X-AI-Transcribe-Provider", "openai")
                if used_base:
                    response.headers.setdefault(
                        "X-AI-Transcribe-Base-Url", str(used_base))
                    response.headers.setdefault(
                        "X-AI-Transcribe-Fallback", "1" if used_fallback else "0")
                if not str(text).strip():
                    response.headers["X-Request-Id"] = request_id
                    return TranscribeResponse(
                        text="", segment_index=segment_index, is_final=is_final)

                _audit_event(
                    "transcribe_ok",
                    {
                        "request_id": request_id,
                        "endpoint": "transcribe",
                        "user_id": user_id_str,
                        "ip": client_ip,
                        "duration_ms": int((time.time() - started_at) * 1000),
                        "text_len": len(str(text)),
                    },
                )

                response.headers["X-Request-Id"] = request_id
                return TranscribeResponse(
                    text=str(text),
                    segment_index=segment_index,
                    is_final=is_final,
                )
            except Exception as e:
                openai_error = e
                if provider == "openai":
                    raise

        if provider in {"auto", "sherpa"} and sherpa_ready:
            try:
                text, sherpa_kind, sherpa_url = await sherpa_transcribe(
                    content=content,
                    filename=filename,
                    settings=effective_settings,
                    segment_index=segment_index,
                    is_final=is_final,
                )
                response.headers.setdefault(
                    "X-AI-Transcribe-Provider", sherpa_kind)
                if sherpa_url:
                    response.headers.setdefault(
                        "X-AI-Transcribe-Remote-Url", str(sherpa_url))
                if not str(text).strip():
                    response.headers["X-Request-Id"] = request_id
                    return TranscribeResponse(
                        text="", segment_index=segment_index, is_final=is_final)

                _audit_event(
                    "transcribe_ok",
                    {
                        "request_id": request_id,
                        "endpoint": "transcribe",
                        "user_id": user_id_str,
                        "ip": client_ip,
                        "duration_ms": int((time.time() - started_at) * 1000),
                        "text_len": len(str(text)),
                    },
                )

                response.headers["X-Request-Id"] = request_id
                return TranscribeResponse(
                    text=str(text),
                    segment_index=segment_index,
                    is_final=is_final,
                )
            except Exception:
                if openai_error is not None:
                    raise openai_error
                raise

        if openai_error is not None:
            if provider == "auto" and not sherpa_ready:
                msg = (
                    "语音转写失败：OpenAI Whisper 调用失败，且 Sherpa 未就绪，无法回退。"
                    " 请到管理后台【系统设置 -> AI 咨询 -> 语音管理】开启强制模式，"
                    "并将 SHERPA_ASR_MODE 设置为 local/remote（不要是 off），"
                    "再配置 remote_url 或本地模型路径；或者改用 provider=openai 并确保转写网关支持 Whisper。")
                return _make_error_response(
                    status_code=503,
                    error_code=ERROR_AI_UNAVAILABLE,
                    message=msg,
                    request_id=request_id,
                    headers=diag_headers,
                )
            raise openai_error

        error_code = ERROR_AI_UNAVAILABLE
        message = "AI服务不可用：请稍后再试"
        return _make_error_response(
            status_code=503,
            error_code=error_code,
            message=message,
            request_id=request_id,
        )
    except HTTPException as e:
        sc = int(getattr(e, "status_code", 500) or 500)
        error_code = _error_code_for_http(sc)
        message = _extract_message(getattr(e, "detail", ""))
        raw_headers = getattr(e, "headers", None)
        out_headers: dict[str, str] | None = None
        if isinstance(raw_headers, dict) and raw_headers:
            out_headers = {str(k): str(v) for k, v in raw_headers.items()}
        ai_metrics.record_error(
            endpoint="transcribe",
            request_id=request_id,
            error_code=error_code,
            status_code=sc,
            message=message or "transcribe_http_error",
        )
        return _make_error_response(
            status_code=sc,
            error_code=error_code,
            message=message or "语音转写失败",
            request_id=request_id,
            headers=out_headers,
        )
    except Exception as e:
        sc = int(
            getattr(
                getattr(
                    e,
                    "status_code",
                    None),
                "__int__",
                lambda: 0)() or 0)
        if not sc:
            try:
                sc = int(
                    getattr(
                        getattr(
                            e,
                            "response",
                            None),
                        "status_code",
                        0) or 0)
            except Exception:
                sc = 0
        if sc <= 0:
            sc = 500
        error_code = _error_code_for_http(sc)
        ai_metrics.record_error(
            endpoint="transcribe",
            request_id=request_id,
            error_code=error_code,
            status_code=sc,
            message="transcribe_failed",
        )
        logger.exception("ai_transcribe_failed request_id=%s", request_id)
        critical_event_reporter.fire_and_forget(
            event="ai_transcribe_failed",
            severity="error",
            request_id=request_id,
            title="语音转写失败",
            message="transcribe_failed",
            data={
                "endpoint": "transcribe",
            },
            dedup_key="ai_transcribe_failed",
        )
        msg = "语音转写失败：请确认 OPENAI_TRANSCRIBE_BASE_URL 指向支持 Whisper 的服务，且 OPENAI_TRANSCRIBE_API_KEY 有效"
        if sc == 401:
            msg = "AI鉴权失败：TRANSCRIBE_API_KEY 无效或与 TRANSCRIBE_BASE_URL 不匹配"
        elif sc == 403:
            msg = "AI服务拒绝访问：权限不足或账号未开通语音转写能力"
        elif sc == 429:
            msg = "AI服务限流：请求过于频繁，请稍后再试"
        elif sc == 503:
            msg = "AI服务不可用：请稍后再试"
        return _make_error_response(
            status_code=sc,
            error_code=error_code,
            message=msg,
            request_id=request_id,
        )
