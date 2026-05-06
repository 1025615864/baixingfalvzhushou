"""统一错误响应"""
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .error_codes import CommunityException, ErrorCode


def get_trace_id(request: Request) -> Optional[str]:
    return request.headers.get("X-Trace-ID")


def community_exception_handler(request: Request, exc: CommunityException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.to_dict(),
        headers={"X-Trace-ID": exc.trace_id or get_trace_id(request) or ""},
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": ErrorCode.INVALID_PARAMETER.value,
            "message": "参数验证失败",
            "detail": errors,
            "trace_id": get_trace_id(request) or "",
        },
    )


def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code_map = {
        401: ErrorCode.INVALID_TOKEN,
        403: ErrorCode.POST_NO_PERMISSION,
        404: ErrorCode.POST_NOT_FOUND,
        429: ErrorCode.POST_RATE_LIMITED,
    }

    error_code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": error_code.value,
            "message": exc.detail or error_code.value,
            "trace_id": get_trace_id(request) or "",
        },
    )


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging
    logger = logging.getLogger(__name__)
    trace_id = get_trace_id(request) or ""

    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": ErrorCode.INTERNAL_ERROR.value,
            "message": "内部错误",
            "trace_id": trace_id,
        },
    )
