from fastapi import APIRouter

from . import assistant, comments, config, favorites, invitations, moderation, posts, reactions, reviews

router = APIRouter(prefix="/forum", tags=["社区论坛"])

router.include_router(posts.router)
router.include_router(comments.router)
router.include_router(favorites.router)
router.include_router(reactions.router)
router.include_router(config.router)
router.include_router(moderation.router)
router.include_router(invitations.router)
router.include_router(reviews.router)
router.include_router(assistant.router)

__all__ = ["router"]
