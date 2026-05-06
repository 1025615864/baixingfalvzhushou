"""统一 API 响应格式"""
from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: T = None, message: str = "success"):
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str, data: Any = None):
        return cls(code=code, message=message, data=data)


class ResponseCode:
    SUCCESS = 0
    VALIDATION_ERROR = 40000
    NOT_FOUND = 40400
    INTERNAL_ERROR = 50000
    CONSULTATION_NOT_FOUND = 40401
    LAWYER_NOT_FOUND = 40402
    APPOINTMENT_NOT_FOUND = 40403
    UNAUTHORIZED = 40100
    FORBIDDEN = 40300
    RATE_LIMIT_EXCEEDED = 42900


class PaginatedData(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int = 0

    @classmethod
    def create(cls, items: List[Any], total: int, page: int, page_size: int):
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
