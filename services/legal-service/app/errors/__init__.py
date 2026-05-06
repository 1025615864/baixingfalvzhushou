"""errors package"""
from .error_codes import LegalException, LegalErrorCode, ERROR_MESSAGES
from .exception_handlers import (
    legal_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)

__all__ = [
    "LegalException",
    "LegalErrorCode",
    "ERROR_MESSAGES",
    "legal_exception_handler",
    "validation_exception_handler",
    "http_exception_handler",
    "generic_exception_handler",
]