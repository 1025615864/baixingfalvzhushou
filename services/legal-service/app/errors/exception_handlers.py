"""统一错误响应"""
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .error_codes import LegalException, LegalErrorCode
from ..schemas.response import ApiResponse, ResponseCode


def get_trace_id(request: Request) -> Optional[str]:
    return request.headers.get("X-Trace-ID")


def legal_exception_handler(request: Request, exc: LegalException) -> JSONResponse:
    code = int(LegalErrorCode.INVALID_PARAMETER.value) if not exc.code else exc.code
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ApiResponse.error(code, exc.message).model_dump(),
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
        content=ApiResponse.error(
            ResponseCode.VALIDATION_ERROR,
            "参数验证失败",
            {"errors": errors}
        ).model_dump(),
    )


def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code_map = {
        401: ResponseCode.UNAUTHORIZED,
        403: ResponseCode.FORBIDDEN,
        404: ResponseCode.NOT_FOUND,
        429: ResponseCode.RATE_LIMIT_EXCEEDED,
    }

    error_code = code_map.get(exc.status_code, ResponseCode.INTERNAL_ERROR)

    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.error(error_code, exc.detail or "请求错误").model_dump(),
    )


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging
    logger = logging.getLogger(__name__)
    trace_id = get_trace_id(request) or ""

    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse.error(
            ResponseCode.INTERNAL_ERROR,
            "内部错误"
        ).model_dump(),
    )
