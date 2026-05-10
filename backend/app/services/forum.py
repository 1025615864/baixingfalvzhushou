from __future__ import annotations

from datetime import datetime


class ForumService:
    def _parse_bool_value(self, value: str | None, default: bool = True) -> bool:
        raise NotImplementedError


class ForumPostService:
    pass


class ForumCommentService:
    pass


forum_service = ForumService()

__all__ = ["ForumService", "forum_service", "ForumPostService", "ForumCommentService"]
