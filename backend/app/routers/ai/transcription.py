"""AI Transcription router."""
from __future__ import annotations
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter(tags=["AI Transcription"])

ERROR_AI_NOT_CONFIGURED = "AI_NOT_CONFIGURED"
ERROR_AI_BAD_REQUEST = "AI_BAD_REQUEST"
ERROR_AI_UNAUTHORIZED = "AI_UNAUTHORIZED"
ERROR_AI_FORBIDDEN = "AI_FORBIDDEN"
ERROR_AI_RATE_LIMITED = "AI_RATE_LIMITED"
ERROR_AI_UNAVAILABLE = "AI_UNAVAILABLE"
ERROR_AI_INTERNAL_ERROR = "AI_INTERNAL_ERROR"


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


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    raise NotImplementedError
