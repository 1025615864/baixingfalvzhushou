from __future__ import annotations

from fastapi import APIRouter

from .comments import forum_service

router = APIRouter(tags=["Forum Reactions"])


@router.post("/posts/{post_id}/reaction")
async def toggle_reaction(post_id: int):
    raise NotImplementedError


@router.get("/posts/{post_id}/reactions")
async def get_reactions(post_id: int):
    raise NotImplementedError


@router.post("/posts/{post_id}/like")
async def toggle_like(post_id: int):
    raise NotImplementedError
