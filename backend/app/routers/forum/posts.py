"""论坛帖子相关路由"""
from __future__ import annotations

import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...database import get_db
from ...models.user import User
from ...schemas.forum import (
    LikeResponse,
    PostCreate,
    PostIdListRequest,
    PostListResponse,
    PostResponse,
    PostUpdate,
)
from ...services.cache_service import cache_service
from ...services.forum_service import forum_service
from ...utils.content_filter import check_post_content
from ...utils.xss_sanitizer import check_post_content_with_sanitization
from ...utils.deps import get_current_user, get_current_user_optional
from .common import _build_post_response, _create_notification

router = APIRouter()

settings = get_settings()
logger = logging.getLogger(__name__)


@router.post("/posts", response_model=PostResponse, summary="发布帖子")
async def create_post(
    post_data: PostCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """发布新帖子（需登录）"""
    _ = await forum_service.apply_content_filter_config_from_db(db)

    # 1. 基础内容检查 & 敏感词过滤
    passed, error_msg = check_post_content(post_data.title, post_data.content)
    if not passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg)

    # 2. XSS 清理
    passed, error_msg, cleaned_title, cleaned_content = check_post_content_with_sanitization(
        post_data.title, post_data.content
    )
    if not passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg)

    # 使用清理后的内容
    post_data.title = cleaned_title
    post_data.content = cleaned_content

    post = await forum_service.create_post(db, current_user.id, post_data)
    if getattr(post, "review_status", None) == "pending":
        content_lines: list[str] = [f"标题：{post.title}"]
        if getattr(post, "review_reason", None):
            content_lines.append(f"原因：{post.review_reason}")
        await _create_notification(
            db,
            user_id=int(post.user_id),
            title="你的帖子已提交审核",
            content="\n".join(content_lines) if content_lines else None,
            link=f"/forum/post/{int(post.id)}",
            related_post_id=int(post.id),
        )
        await db.commit()
    return await _build_post_response(db, post, current_user.id)


@router.get("/posts", response_model=PostListResponse, summary="获取帖子列表")
async def get_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: Annotated[str | None, Query(max_length=100)] = None,
    is_essence: Annotated[bool | None, Query(description="是否仅精华帖")] = None,
):
    """获取帖子列表，支持分类筛选和关键词搜索"""
    user_id = current_user.id if current_user else None

    # SQL注入防护：限制keyword长度
    if keyword and len(keyword) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关键词长度不能超过100个字符"
        )

    cache_enabled = os.getenv("FORUM_POSTS_CACHE_ENABLED", "").strip().lower() in {
        "1", "true", "yes", "y", "on", }

    cache_key = None
    if cache_enabled and user_id is None:
        essence_key = "1" if is_essence is True else "0" if is_essence is False else "-"
        cache_key = (
            f"forum:posts:list:v1:{page}:{page_size}:{category or '-'}:{keyword or '-'}:{essence_key}"
        )
        cached = await cache_service.get_json(cache_key)
        if isinstance(
                cached, dict) and "items" in cached and "total" in cached:
            try:
                return PostListResponse.model_validate(cached)
            except Exception:
                logger.exception("Failed to validate cached posts data")

    posts, total = await forum_service.get_posts(db, page, page_size, category, keyword, is_essence=is_essence)

    post_ids = [int(post.id) for post in posts]
    favorite_counts = await forum_service.get_posts_favorite_counts(db, post_ids)
    reactions_map = await forum_service.get_posts_reactions(db, post_ids)

    # 批量获取用户点赞和收藏状态，避免N+1查询
    liked_status_map = {}
    favorited_status_map = {}
    if user_id:
        liked_status_map = await forum_service.get_posts_liked_status(db, post_ids, user_id)
        favorited_status_map = await forum_service.get_posts_favorited_status(db, post_ids, user_id)

    items = [
        await _build_post_response(
            db,
            post,
            user_id,
            favorite_count=favorite_counts.get(int(post.id), 0),
            reactions_data=reactions_map.get(int(post.id), []),
            is_liked=liked_status_map.get(int(post.id)),
            is_favorited=favorited_status_map.get(int(post.id)),
        )
        for post in posts
    ]

    response = PostListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size)

    if cache_enabled and user_id is None and cache_key:
        ttl_value = os.getenv(
            "FORUM_POSTS_LIST_CACHE_TTL_SECONDS",
            "60").strip()
        try:
            ttl_seconds = int(ttl_value)
        except (TypeError, ValueError):
            ttl_seconds = 60
        if ttl_seconds > 0:
            await cache_service.set_json(
                cache_key,
                response.model_dump(mode="json"),
                expire=ttl_seconds,
            )

    return response


@router.get("/hot", response_model=PostListResponse, summary="获取热门帖子")
async def get_hot_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    category: str | None = None,
):
    """获取热门帖子"""
    posts = await forum_service.get_hot_posts(db, limit=limit, category=category)
    user_id = current_user.id if current_user else None
    items = [await _build_post_response(db, post, user_id) for post in posts]
    return PostListResponse(items=items, total=len(
        items), page=1, page_size=limit)


@router.get("/me/posts", response_model=PostListResponse, summary="获取我发布的帖子")
async def get_my_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
):
    """获取当前用户发布的帖子列表"""
    posts, total = await forum_service.get_user_posts(db, current_user.id, page, page_size, category, keyword)
    items = [await _build_post_response(db, post, current_user.id) for post in posts]
    return PostListResponse(items=items, total=total,
                            page=page, page_size=page_size)


@router.get("/posts/{post_id}/recycle",
            response_model=PostResponse, summary="查看回收站帖子详情")
async def get_deleted_post_detail(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from ...utils.permissions import is_owner_or_admin

    post = await forum_service.get_post_any(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")
    if not post.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该帖子未被删除")
    if not is_owner_or_admin(current_user, post.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限查看")

    return await _build_post_response(db, post, current_user.id)


@router.get("/me/posts/deleted", response_model=PostListResponse,
            summary="获取我删除的帖子（回收站）")
async def get_my_deleted_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
):
    """获取我删除的帖子（回收站）"""
    posts, total = await forum_service.get_user_deleted_posts(db, current_user.id, page, page_size, category, keyword)
    items = [await _build_post_response(db, post, current_user.id) for post in posts]
    return PostListResponse(items=items, total=total,
                            page=page, page_size=page_size)


@router.get("/posts/{post_id}", response_model=PostResponse, summary="获取帖子详情")
async def get_post(
    post_id: int,
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取帖子详情，自动增加浏览量"""
    try:
        post = await forum_service.get_post(db, post_id)
        if not post:
            if current_user is not None:
                post_any = await forum_service.get_post_any(db, post_id)
                if post_any and not post_any.is_deleted:
                    from ...utils.permissions import is_owner_or_admin

                    if is_owner_or_admin(current_user, post_any.user_id):
                        post = post_any
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看")

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="帖子不存在")

        await forum_service.increment_view(db, post)

        post_review_status = getattr(post, "review_status", None)
        if post_review_status in (None, "approved"):
            post = await forum_service.get_post(db, post_id)
        else:
            post = await forum_service.get_post_any(db, post_id)
            if post and post.is_deleted:
                post = None

            if post and current_user is not None:
                from ...utils.permissions import is_owner_or_admin

                if not is_owner_or_admin(current_user, post.user_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看")

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="帖子不存在")

        user_id = current_user.id if current_user else None
        return await _build_post_response(db, post, user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("获取帖子详情失败 post_id=%s", post_id)
        detail = str(e) if settings.debug else "服务器错误"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail)


@router.put("/posts/{post_id}", response_model=PostResponse, summary="更新帖子")
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """更新帖子（仅作者或管理员可操作）"""
    from ...utils.permissions import is_owner_or_admin

    post = await forum_service.get_post_any(db, post_id)
    if not post or post.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")

    if not is_owner_or_admin(current_user, post.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有作者或管理员可以编辑帖子",
        )

    updated_post = await forum_service.update_post(db, post, post_data)
    return await _build_post_response(db, updated_post, current_user.id)


@router.delete("/posts/{post_id}", summary="删除帖子")
async def delete_post(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """删除帖子（仅作者、版主或管理员可操作）"""
    from ...utils.permissions import is_owner_or_admin

    post = await forum_service.get_post_any(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")

    if post.is_deleted:
        return {"message": "帖子已删除"}

    if not is_owner_or_admin(current_user, post.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有作者、版主或管理员可以删除帖子",
        )

    await forum_service.delete_post(db, post)
    return {"message": "删除成功"}


@router.post("/posts/{post_id}/restore", summary="恢复帖子")
async def restore_post(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from ...utils.permissions import is_owner_or_admin

    post = await forum_service.get_post_any(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")

    if not is_owner_or_admin(current_user, post.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有作者、版主或管理员可以恢复帖子")

    if not post.is_deleted:
        return {"message": "帖子未被删除"}

    _ = await forum_service.restore_post(db, post)
    return {"message": "恢复成功"}


@router.delete("/posts/{post_id}/purge", summary="永久删除帖子")
async def purge_post(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from ...utils.permissions import is_owner_or_admin

    post = await forum_service.get_post_any(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")

    if not is_owner_or_admin(current_user, post.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有作者、版主或管理员可以永久删除帖子")

    if not post.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先删除帖子后再永久删除")

    await forum_service.purge_post(db, post)
    return {"message": "已永久删除"}


@router.post("/posts/batch/restore", summary="批量恢复帖子")
async def batch_restore_posts(
    payload: PostIdListRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from ...utils.permissions import is_owner_or_admin

    success_ids: list[int] = []
    failed: list[dict[str, object]] = []

    try:
        for post_id in payload.ids:
            post = await forum_service.get_post_any(db, int(post_id))
            if not post:
                failed.append({"id": int(post_id), "reason": "帖子不存在"})
                continue
            if not is_owner_or_admin(current_user, post.user_id):
                failed.append({"id": int(post_id), "reason": "无权限"})
                continue
            if not post.is_deleted:
                failed.append({"id": int(post_id), "reason": "帖子未被删除"})
                continue
            await forum_service.restore_post(db, post)
            success_ids.append(int(post_id))
        await db.commit()
    except Exception:
        await db.rollback()
        for post_id in success_ids:
            failed.append({"id": int(post_id), "reason": "操作失败"})
        success_ids = []

    return {"success_ids": success_ids, "failed": failed}


@router.post("/posts/batch/purge", summary="批量永久删除帖子")
async def batch_purge_posts(
    payload: PostIdListRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from ...utils.permissions import is_owner_or_admin

    success_ids: list[int] = []
    failed: list[dict[str, object]] = []

    try:
        for post_id in payload.ids:
            post = await forum_service.get_post_any(db, int(post_id))
            if not post:
                failed.append({"id": int(post_id), "reason": "帖子不存在"})
                continue
            if not is_owner_or_admin(current_user, post.user_id):
                failed.append({"id": int(post_id), "reason": "无权限"})
                continue
            if not post.is_deleted:
                failed.append({"id": int(post_id), "reason": "请先删除帖子"})
                continue
            await forum_service.purge_post(db, post)
            success_ids.append(int(post_id))
        await db.commit()
    except Exception:
        await db.rollback()
        for post_id in success_ids:
            failed.append({"id": int(post_id), "reason": "操作失败"})
        success_ids = []

    return {"success_ids": success_ids, "failed": failed}


@router.post("/posts/batch/delete", summary="批量删除帖子")
async def batch_delete_posts(
    payload: PostIdListRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from ...utils.permissions import is_owner_or_admin

    success_ids: list[int] = []
    failed: list[dict[str, object]] = []

    try:
        for post_id in payload.ids:
            post = await forum_service.get_post_any(db, int(post_id))
            if not post:
                failed.append({"id": int(post_id), "reason": "帖子不存在"})
                continue
            if not is_owner_or_admin(current_user, post.user_id):
                failed.append({"id": int(post_id), "reason": "无权限"})
                continue
            if post.is_deleted:
                failed.append({"id": int(post_id), "reason": "帖子已删除"})
                continue
            await forum_service.delete_post(db, post)
            success_ids.append(int(post_id))
        await db.commit()
    except Exception:
        await db.rollback()
        for post_id in success_ids:
            failed.append({"id": int(post_id), "reason": "操作失败"})
        success_ids = []

    return {"success_ids": success_ids, "failed": failed}


# ==================== 帖子审核和置顶功能（管理员用） ====================

from pydantic import BaseModel
from ...utils.deps import require_admin


class PostReviewRequest(BaseModel):
    """帖子审核请求"""
    post_id: int
    status: str  # approved, rejected
    reason: str | None = None


class BatchReviewRequest(BaseModel):
    """批量审核请求"""
    post_ids: list[int]
    status: str
    reason: str | None = None


class PostStickyRequest(BaseModel):
    """帖子置顶请求"""
    is_sticky: bool
    sticky_priority: int = 0


class PostEssenceRequest(BaseModel):
    """帖子精华请求"""
    is_essence: bool


@router.put("/posts/{post_id}/review", summary="审核帖子")
async def review_post(
    post_id: int,
    data: PostReviewRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """审核帖子（需要管理员权限）"""
    _ = current_user
    
    post = await forum_service.get_post_any(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")
    
    # 更新审核状态
    post.review_status = data.status
    if data.reason:
        post.review_reason = data.reason
    
    await db.commit()
    await db.refresh(post)
    
    # 发送通知给帖子作者
    if data.status == "rejected":
        await _create_notification(
            db,
            user_id=int(post.user_id),
            title="帖子审核未通过",
            content=f"你的帖子《{post.title}》审核未通过" + (f"，原因：{data.reason}" if data.reason else ""),
            link=f"/forum/post/{post_id}",
            related_post_id=post_id,
        )
        await db.commit()
    elif data.status == "approved":
        await _create_notification(
            db,
            user_id=int(post.user_id),
            title="帖子审核通过",
            content=f"你的帖子《{post.title}》已通过审核",
            link=f"/forum/post/{post_id}",
            related_post_id=post_id,
        )
        await db.commit()
    
    return {"message": "审核完成", "post_id": post_id, "status": data.status}


@router.post("/posts/batch/review", summary="批量审核帖子")
async def batch_review_posts(
    data: BatchReviewRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """批量审核帖子（需要管理员权限）"""
    _ = current_user
    
    success_count = 0
    failed_ids = []
    
    for post_id in data.post_ids:
        try:
            post = await forum_service.get_post_any(db, post_id)
            if post:
                post.review_status = data.status
                if data.reason:
                    post.review_reason = data.reason
                success_count += 1
            else:
                failed_ids.append(post_id)
        except Exception:
            failed_ids.append(post_id)
    
    await db.commit()
    
    return {
        "message": "批量审核完成",
        "success_count": success_count,
        "failed_count": len(failed_ids),
        "failed_ids": failed_ids
    }


@router.put("/posts/{post_id}/sticky", summary="设置帖子置顶")
async def set_post_sticky(
    post_id: int,
    data: PostStickyRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """设置帖子置顶状态（需要管理员权限）"""
    _ = current_user
    
    post = await forum_service.get_post_any(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")
    
    # 设置置顶状态
    post.is_sticky = data.is_sticky
    post.sticky_priority = data.sticky_priority if data.is_sticky else 0
    
    await db.commit()
    await db.refresh(post)
    
    return {
        "message": "置顶设置成功",
        "post_id": post_id,
        "is_sticky": data.is_sticky,
        "sticky_priority": post.sticky_priority
    }


@router.put("/posts/{post_id}/essence", summary="设置帖子精华")
async def set_post_essence(
    post_id: int,
    data: PostEssenceRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """设置帖子精华状态（需要管理员权限）"""
    _ = current_user
    
    post = await forum_service.get_post_any(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")
    
    # 设置精华状态
    post.is_essence = data.is_essence
    
    await db.commit()
    await db.refresh(post)
    
    # 发送通知给帖子作者
    if data.is_essence:
        await _create_notification(
            db,
            user_id=int(post.user_id),
            title="帖子被设为精华",
            content=f"恭喜！你的帖子《{post.title}》被设为精华帖",
            link=f"/forum/post/{post_id}",
            related_post_id=post_id,
        )
        await db.commit()
    
    return {
        "message": "精华设置成功",
        "post_id": post_id,
        "is_essence": data.is_essence
    }


@router.post("/posts/{post_id}/like",
             response_model=LikeResponse, summary="点赞/取消点赞帖子")
async def toggle_post_like(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """切换帖子点赞状态"""
    post = await forum_service.get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")

    try:
        liked, like_count = await forum_service.toggle_post_like(db, post_id, current_user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")
    message = "点赞成功" if liked else "取消点赞"

    return LikeResponse(liked=liked, like_count=like_count, message=message)
