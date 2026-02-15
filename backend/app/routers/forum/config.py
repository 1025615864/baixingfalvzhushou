"""论坛配置与词库相关路由"""
from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.system import LogAction, SystemConfig
from ...models.user import User
from ...services.forum_service import forum_service
from ...utils.deps import require_admin
from .common import _log_forum_admin_action

router = APIRouter()


class ForumReviewConfig(BaseModel):
    comment_review_enabled: bool


class ForumPostReviewConfig(BaseModel):
    post_review_enabled: bool
    post_review_mode: str  # all / rule


class ForumContentFilterRulesUpdate(BaseModel):
    ad_words_threshold: int | None = None
    check_url: bool | None = None
    check_phone: bool | None = None


class ForumContentFilterConfig(BaseModel):
    sensitive_words: list[str]
    ad_words: list[str]
    ad_words_threshold: int
    check_url: bool
    check_phone: bool


class SensitiveWordRequest(BaseModel):
    word: str


@router.get("/admin/review-config", summary="获取论坛审核配置")
async def get_forum_review_config(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    enabled = await forum_service.is_comment_review_enabled(db)
    return {"comment_review_enabled": bool(enabled)}


@router.put("/admin/review-config", summary="更新论坛审核配置")
async def update_forum_review_config(
    data: ForumReviewConfig,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    value = "true" if data.comment_review_enabled else "false"
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "forum.review.enabled")
    )
    config = result.scalar_one_or_none()

    if config:
        config.value = value
        config.updated_by = current_user.id
        if not config.description:
            config.description = "论坛评论审核开关"
    else:
        config = SystemConfig(
            key="forum.review.enabled",
            value=value,
            description="论坛评论审核开关",
            category="forum",
            updated_by=current_user.id,
        )
        db.add(config)

    await _log_forum_admin_action(
        db,
        user_id=current_user.id,
        action=LogAction.CONFIG,
        module="forum",
        description="更新论坛评论审核配置",
        extra_data={
            "comment_review_enabled": bool(
                data.comment_review_enabled)},
        request=request,
    )
    await db.commit()
    return {"message": "配置已更新", "comment_review_enabled": bool(
        data.comment_review_enabled)}


@router.get("/admin/post-review-config", summary="获取帖子审核配置")
async def get_forum_post_review_config(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    enabled = await forum_service.is_post_review_enabled(db)
    mode = await forum_service.get_post_review_mode(db)
    return {"post_review_enabled": bool(
        enabled), "post_review_mode": str(mode)}


@router.put("/admin/post-review-config", summary="更新帖子审核配置")
async def update_forum_post_review_config(
    data: ForumPostReviewConfig,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    enabled_value = "true" if data.post_review_enabled else "false"
    mode_value = (data.post_review_mode or "").strip().lower()
    if mode_value not in ("all", "rule"):
        raise HTTPException(status_code=400,
                            detail="post_review_mode 仅支持 all 或 rule")

    for key, value, desc in (
        ("forum.post_review.enabled", enabled_value, "论坛帖子审核开关"),
        ("forum.post_review.mode", mode_value, "论坛帖子审核模式（all/rule）"),
    ):
        result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
        config = result.scalar_one_or_none()
        if config:
            config.value = value
            config.updated_by = current_user.id
            if not config.description:
                config.description = desc
        else:
            config = SystemConfig(
                key=key,
                value=value,
                description=desc,
                category="forum",
                updated_by=current_user.id,
            )
            db.add(config)

    await _log_forum_admin_action(
        db,
        user_id=current_user.id,
        action=LogAction.CONFIG,
        module="forum",
        description="更新论坛帖子审核配置",
        extra_data={
            "post_review_enabled": bool(data.post_review_enabled),
            "post_review_mode": mode_value,
        },
        request=request,
    )
    await db.commit()

    return {
        "message": "配置已更新",
        "post_review_enabled": bool(data.post_review_enabled),
        "post_review_mode": mode_value,
    }


@router.get("/admin/content-filter-config",
            response_model=ForumContentFilterConfig, summary="获取内容过滤规则配置")
async def get_content_filter_config(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    config = await forum_service.apply_content_filter_config_from_db(db)
    return ForumContentFilterConfig.model_validate(config)


@router.put("/admin/content-filter-config",
            response_model=ForumContentFilterConfig, summary="更新内容过滤规则配置")
async def update_content_filter_config(
    data: ForumContentFilterRulesUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    config = await forum_service.update_content_filter_rules(
        db,
        updated_by=current_user.id,
        ad_threshold=data.ad_words_threshold,
        check_url=data.check_url,
        check_phone=data.check_phone,
    )

    await _log_forum_admin_action(
        db,
        user_id=current_user.id,
        action=LogAction.CONFIG,
        module="forum",
        description="更新论坛内容过滤规则配置",
        extra_data={
            "ad_words_threshold": data.ad_words_threshold,
            "check_url": data.check_url,
            "check_phone": data.check_phone,
        },
        request=request,
    )
    await db.commit()

    return ForumContentFilterConfig.model_validate(config)


@router.get("/admin/sensitive-words", summary="获取敏感词列表")
async def get_sensitive_words(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    config = await forum_service.apply_content_filter_config_from_db(db)
    return {
        "sensitive_words": cast(
            list[str],
            config.get("sensitive_words") or []),
        "ad_words": cast(
            list[str],
            config.get("ad_words") or []),
    }


@router.post("/admin/sensitive-words", summary="添加敏感词")
async def add_word(
    data: SensitiveWordRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    _ = await forum_service.add_sensitive_word(db, word=data.word, updated_by=current_user.id)

    await _log_forum_admin_action(
        db,
        user_id=current_user.id,
        action=LogAction.CREATE,
        module="forum",
        description="添加敏感词",
        extra_data={"word": data.word},
        request=request,
    )
    await db.commit()
    return {"message": f"已添加敏感词: {data.word}"}


@router.delete("/admin/sensitive-words/{word}", summary="删除敏感词")
async def delete_word(
    word: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    _ = await forum_service.remove_sensitive_word(db, word=word, updated_by=current_user.id)

    await _log_forum_admin_action(
        db,
        user_id=current_user.id,
        action=LogAction.DELETE,
        module="forum",
        description="删除敏感词",
        extra_data={"word": word},
        request=request,
    )
    await db.commit()
    return {"message": f"已删除敏感词: {word}"}


@router.post("/admin/ad-words", summary="添加广告词")
async def add_advertisement_word(
    data: SensitiveWordRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    _ = await forum_service.add_ad_word(db, word=data.word, updated_by=current_user.id)

    await _log_forum_admin_action(
        db,
        user_id=current_user.id,
        action=LogAction.CREATE,
        module="forum",
        description="添加广告词",
        extra_data={"word": data.word},
        request=request,
    )
    await db.commit()
    return {"message": f"已添加广告词: {data.word}"}


@router.delete("/admin/ad-words/{word}", summary="删除广告词")
async def delete_advertisement_word(
    word: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    _ = await forum_service.remove_ad_word(db, word=word, updated_by=current_user.id)

    await _log_forum_admin_action(
        db,
        user_id=current_user.id,
        action=LogAction.DELETE,
        module="forum",
        description="删除广告词",
        extra_data={"word": word},
        request=request,
    )
    await db.commit()
    return {"message": f"已删除广告词: {word}"}
