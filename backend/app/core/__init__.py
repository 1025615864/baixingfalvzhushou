"""核心模块

提供基础架构支持，包括异常处理、响应格式、分页等。
"""

from .exceptions import (
    BaseException,
    BusinessException,
    NotFoundException,
    ForbiddenException,
    UnauthorizedException,
    ValidationException,
    ConflictException,
    RateLimitException,
    PaymentException,
    DatabaseException,
    ExternalServiceException,
    http_exception_from_business_exception,
)

from .error_handler import setup_exception_handling, GlobalExceptionHandler

from .response import (
    APIResponse,
    SuccessResponse,
    ListResponse,
    ResponseFactory,
)

from .pagination import (
    PaginationParams,
    paginated_response,
    get_pagination_from_query,
)

from .versioning import (
    APIVersion,
    APIVersionMiddleware,
    VersionedRouter,
    VersionNegotiator,
    get_current_api_version,
    is_api_deprecated,
    create_versioned_response,
    versioned_router,
    setup_versioning,
)

__all__ = [
    # 异常类
    "BaseException",
    "BusinessException",
    "NotFoundException",
    "ForbiddenException",
    "UnauthorizedException",
    "ValidationException",
    "ConflictException",
    "RateLimitException",
    "PaymentException",
    "DatabaseException",
    "ExternalServiceException",
    "http_exception_from_business_exception",
    # 错误处理器
    "setup_exception_handling",
    "GlobalExceptionHandler",
    # 响应格式
    "APIResponse",
    "SuccessResponse",
    "ListResponse",
    "ResponseFactory",
    # 分页
    "PaginationParams",
    "paginated_response",
    "get_pagination_from_query",
    # 版本控制
    "APIVersion",
    "APIVersionMiddleware",
    "VersionedRouter",
    "VersionNegotiator",
    "get_current_api_version",
    "is_api_deprecated",
    "create_versioned_response",
    "versioned_router",
    "setup_versioning",
]
