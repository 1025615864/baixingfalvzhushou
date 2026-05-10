from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .comments import forum_service

router = APIRouter(tags=["Forum Favorites"])


async def _build_post_responses(db, posts, user_id):
    raise NotImplementedError


@router.post("/posts/{post_id}/favorite")
async def toggle_favorite(post_id: int):
    raise NotImplementedError


@router.get("/favorites")
async def list_favorites():
    raise NotImplementedError
