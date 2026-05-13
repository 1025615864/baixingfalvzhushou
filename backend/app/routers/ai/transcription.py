"""AI Transcription router."""
from __future__ import annotations
import json
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["AI Transcription"])

ERROR_AI_NOT_CONFIGURED = "AI_NOT_CONFIGURED"
ERROR_AI_BAD_REQUEST = "AI_BAD_REQUEST"
ERROR_AI_UNAUTHORIZED = "AI_UNAUTHORIZED"
ERROR_AI_FORBIDDEN = "AI_FORBIDDEN"
ERROR_AI_RATE_LIMITED = "AI_RATE_LIMITED"
ERROR_AI_UNAVAILABLE = "AI_UNAVAILABLE"
ERROR_AI_INTERNAL_ERROR = "AI_INTERNAL_ERROR"

SUPPORTED_AUDIO_EXTENSIONS = {
    "wav", "mp3", "m4a", "ogg", "webm", "opus", "mp4", "aac", "mpeg",
}

MAX_AUDIO_FILE_SIZE = 10 * 1024 * 1024


def _error_code_for_http(status_code: int) -> str:
    mapping = {
        400: ERROR_AI_BAD_REQUEST,
        401: ERROR_AI_UNAUTHORIZED,
        403: ERROR_AI_FORBIDDEN,
        429: ERROR_AI_RATE_LIMITED,
        503: ERROR_AI_UNAVAILABLE,
    }
    return mapping.get(status_code, ERROR_AI_INTERNAL_ERROR)


def _extract_message(detail) -> str:
    if detail is None:
        return ""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        if "message" in detail:
            return str(detail["message"])
        if "detail" in detail:
            return str(detail["detail"])
        return str(detail)
    return str(detail)


def _make_error_response(
    status_code: int,
    error_code: str,
    message: str,
    request_id: str,
    headers: Optional[dict] = None,
) -> JSONResponse:
    body = json.dumps(
        {"error_code": error_code, "message": message, "request_id": request_id},
        ensure_ascii=False,
    )
    response_headers = {
        "X-Request-Id": request_id,
        "X-Error-Code": error_code,
    }
    if headers:
        response_headers.update(headers)
    return JSONResponse(
        status_code=status_code,
        content=json.loads(body),
        headers=response_headers,
    )


def _sanitize_filename(filename: str) -> str:
    if not filename:
        return filename
    for ch in '<>|?*&%$#`\'"':
        filename = filename.replace(ch, "_")
    return filename


def _get_file_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    segment_index: Optional[int] = None,
    is_final: Optional[bool] = None,
    request: Request = None,
):
    request_id = str(uuid.uuid4())[:8]

    filename = _sanitize_filename(file.filename or "")
    content = await file.read()

    if not content:
        return _make_error_response(
            400, ERROR_AI_BAD_REQUEST, "音频文件为空", request_id,
        )

    if len(content) > MAX_AUDIO_FILE_SIZE:
        return _make_error_response(
            400, ERROR_AI_BAD_REQUEST, "音频文件大小不能超过 10MB", request_id,
        )

    ext = _get_file_extension(file.filename or "")
    if ext and ext not in SUPPORTED_AUDIO_EXTENSIONS:
        return _make_error_response(
            400, ERROR_AI_BAD_REQUEST, "音频格式不支持", request_id,
        )

    e2e_mock = False
    if request:
        e2e_mock = request.headers.get("X-E2E-Mock-AI") == "1"

    if e2e_mock:
        return JSONResponse(
            content={"text": "这是一个E2E mock 的语音转写结果", "confidence": 0.95},
            headers={"X-Request-Id": request_id},
        )

    try:
        from app.config.settings import settings as _settings
        api_key = getattr(_settings, 'openai_api_key', '')
        if not api_key:
            return _make_error_response(503, ERROR_AI_NOT_CONFIGURED, "AI服务未配置", request_id)
    except Exception:
        return _make_error_response(503, ERROR_AI_NOT_CONFIGURED, "AI服务未配置", request_id)

    return JSONResponse(
        content={"text": "", "confidence": 0.0},
        headers={"X-Request-Id": request_id},
    )
