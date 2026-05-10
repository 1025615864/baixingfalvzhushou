from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Forum Posts"])


class _ForumService:
    async def get_post(self, db, post_id):
        raise NotImplementedError

    async def get_post_any(self, db, post_id):
        raise NotImplementedError

    async def create_post(self, db, user_id, post_data):
        raise NotImplementedError

    async def get_comments_visible(self, db, post_id, page, page_size, viewer_user_id, viewer_role, include_unapproved):
        raise NotImplementedError

    async def create_comment(self, db, post_id, user_id, comment_data):
        raise NotImplementedError

    async def get_comment(self, db, comment_id):
        raise NotImplementedError

    async def get_comment_any(self, db, comment_id):
        raise NotImplementedError

    async def delete_comment(self, db, comment):
        raise NotImplementedError

    async def restore_comment(self, db, comment):
        raise NotImplementedError

    async def toggle_comment_like(self, db, comment_id, user_id):
        raise NotImplementedError

    async def apply_content_filter_config_from_db(self, db):
        raise NotImplementedError

    async def toggle_post_favorite(self, db, post_id, user_id):
        raise NotImplementedError

    async def get_user_favorites(self, db, user_id, page, page_size, category, keyword):
        raise NotImplementedError

    async def toggle_reaction(self, db, post_id, user_id, emoji):
        raise NotImplementedError

    async def get_post_reactions(self, db, post_id):
        raise NotImplementedError


forum_service = _ForumService()


def check_comment_content(content: str) -> tuple[bool, str | None]:
    raise NotImplementedError


async def _build_comment_response(db, comment, viewer_user_id):
    raise NotImplementedError


def _create_notification(db, **kwargs):
    raise NotImplementedError


@router.get("/posts")
async def list_posts():
    raise NotImplementedError


@router.post("/posts")
async def create_post():
    raise NotImplementedError


@router.get("/posts/{post_id}")
async def get_post(post_id: int):
    raise NotImplementedError


@router.put("/posts/{post_id}")
async def update_post(post_id: int):
    raise NotImplementedError


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    raise NotImplementedError


@router.post("/posts/{post_id}/comments")
async def create_comment(post_id: int):
    raise NotImplementedError


@router.get("/posts/{post_id}/comments")
async def get_comments(post_id: int):
    raise NotImplementedError


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int):
    raise NotImplementedError


@router.post("/comments/{comment_id}/restore")
async def restore_comment(comment_id: int):
    raise NotImplementedError


@router.post("/comments/{comment_id}/like")
async def like_comment(comment_id: int):
    raise NotImplementedError
