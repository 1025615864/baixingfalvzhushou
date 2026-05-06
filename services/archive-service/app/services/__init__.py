"""档案库服务模块"""
from .archive_vector_store import (
    search_archive,
    add_archive,
    delete_archive,
    get_collection_count
)

__all__ = ["search_archive", "add_archive", "delete_archive", "get_collection_count"]