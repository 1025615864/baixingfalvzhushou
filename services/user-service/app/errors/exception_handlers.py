"""统一异常处理器"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .error_codes import ErrorCode, UserServiceException, ERROR_MESSAGES

logger = logging.getLogger(__name__)


async def user_service_exception_handler(request: Request, exc: UserServiceException) -> JSONResponse:
    """处理UserServiceException"""
    logger.warning(
        f"UserServiceException: code={exc.code}, message={exc.message}, "
        f"path={request.url.path}"
    )
    return JSONResponse(
        status_code=_map_code_to_status(exc.code),
        content=exc.to_dict(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求验证错误"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": ErrorCode.COMMON_INVALID_PARAMETER.value,
            "message": "参数验证失败",
            "detail": {"errors": errors},
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """处理HTTP异常"""
    code = _map_http_status_to_code(exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": code,
            "message": exc.detail,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理通用异常"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": ErrorCode.COMMON_INTERNAL_ERROR.value,
            "message": "内部服务器错误",
        },
    )


def _map_code_to_status(code: str) -> int:
    """将错误码映射到HTTP状态码"""
    if code.startswith("U01"):
        return status.HTTP_401_UNAUTHORIZED
    if code.startswith("U02"):
        if "NOT_FOUND" in code or "DELETED" in code:
            return status.HTTP_404_NOT_FOUND
        if "NO_PERMISSION" in code or "BANNED" in code:
            return status.HTTP_403_FORBIDDEN
        if "ALREADY_EXISTS" in code:
            return status.HTTP_409_CONFLICT
        return status.HTTP_400_BAD_REQUEST
    if code.startswith("U03"):
        if "PERMISSION" in code or "DENIED" in code:
            return status.HTTP_403_FORBIDDEN
        return status.HTTP_400_BAD_REQUEST
    if code.startswith("U04"):
        return status.HTTP_401_UNAUTHORIZED
    if code.startswith("U05"):
        if "SERVICE_UNAVAILABLE" in code:
            return status.HTTP_503_SERVICE_UNAVAILABLE
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def _map_http_status_to_code(status_code: int) -> str:
    """将HTTP状态码映射到错误码"""
    if status_code == 400:
        return ErrorCode.COMMON_INVALID_PARAMETER.value
    if status_code == 401:
        return ErrorCode.AUTH_TOKEN_INVALID.value
    if status_code == 403:
        return ErrorCode.USER_NO_PERMISSION.value
    if status_code == 404:
        return ErrorCode.USER_NOT_FOUND.value
    if status_code == 429:
        return "U05005"
    if status_code == 500:
        return ErrorCode.COMMON_INTERNAL_ERROR.value
    if status_code == 503:
        return ErrorCode.COMMON_SERVICE_UNAVAILABLE.value
    return ErrorCode.COMMON_INTERNAL_ERROR.value


def register_exception_handlers(app):
    """注册所有异常处理器"""
    from fastapi import FastAPI
    app.add_exception_handler(UserServiceException, user_service_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
