"""Forum service."""
from __future__ import annotations
import time
from typing import Optional


class ForumService:
    def __init__(self):
        self._posts: dict[int, dict] = {}
        self._next_post_id = 1

    async def create_post(self, user_id: int, title: str, content: str, category: str = "general", tags: Optional[list[str]] = None) -> dict:
        post_id = self._next_post_id
        self._next_post_id += 1
        self._posts[post_id] = {
            "id": post_id, "user_id": user_id, "title": title,
            "content": content, "category": category,
            "tags": tags or [], "status": "published",
            "created_at": time.time(), "view_count": 0,
            "like_count": 0, "comment_count": 0,
        }
        return {"id": post_id, "title": title, "status": "published"}

    async def get_post(self, post_id: int) -> Optional[dict]:
        return self._posts.get(post_id)

    async def list_posts(self, category: Optional[str] = None, limit: int = 20, offset: int = 0) -> list[dict]:
        posts = list(self._posts.values())
        if category:
            posts = [p for p in posts if p["category"] == category]
        return posts[offset:offset + limit]

    async def delete_post(self, post_id: int, user_id: int) -> dict:
        post = self._posts.get(post_id)
        if not post:
            return {"success": False, "error": "帖子不存在"}
        if post["user_id"] != user_id:
            return {"success": False, "error": "无权删除"}
        del self._posts[post_id]
        return {"success": True}


class ForumPostService:
    def __init__(self):
        self._forum_service = ForumService()

    async def create_post(self, user_id: int, title: str, content: str, **kwargs) -> dict:
        return await self._forum_service.create_post(user_id, title, content, **kwargs)

    async def get_post(self, post_id: int) -> Optional[dict]:
        return await self._forum_service.get_post(post_id)

    async def update_post(self, post_id: int, user_id: int, **kwargs) -> dict:
        post = self._forum_service._posts.get(post_id)
        if not post:
            return {"success": False, "error": "帖子不存在"}
        if post["user_id"] != user_id:
            return {"success": False, "error": "无权修改"}
        for k, v in kwargs.items():
            if k in post:
                post[k] = v
        return {"success": True}

    async def like_post(self, post_id: int, user_id: int) -> dict:
        post = self._forum_service._posts.get(post_id)
        if not post:
            return {"success": False, "error": "帖子不存在"}
        post["like_count"] = post.get("like_count", 0) + 1
        return {"success": True, "like_count": post["like_count"]}


class ForumCommentService:
    def __init__(self):
        self._comments: dict[int, dict] = {}
        self._next_comment_id = 1

    async def create_comment(self, post_id: int, user_id: int, content: str, parent_id: Optional[int] = None) -> dict:
        comment_id = self._next_comment_id
        self._next_comment_id += 1
        self._comments[comment_id] = {
            "id": comment_id, "post_id": post_id, "user_id": user_id,
            "content": content, "parent_id": parent_id,
            "created_at": time.time(),
        }
        return {"id": comment_id, "post_id": post_id, "status": "published"}

    async def get_comments(self, post_id: int) -> list[dict]:
        return [c for c in self._comments.values() if c["post_id"] == post_id]

    async def delete_comment(self, comment_id: int, user_id: int) -> dict:
        comment = self._comments.get(comment_id)
        if not comment:
            return {"success": False, "error": "评论不存在"}
        if comment["user_id"] != user_id:
            return {"success": False, "error": "无权删除"}
        del self._comments[comment_id]
        return {"success": True}


forum_service = ForumService()
