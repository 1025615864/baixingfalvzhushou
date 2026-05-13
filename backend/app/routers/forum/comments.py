from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.utils.deps import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.forum import Post, Comment, CommentLike
from app.services.forum.core import ForumPostService, ForumCommentService, ForumService
from app.schemas.forum import PostCreate, PostUpdate, CommentCreate

router = APIRouter(tags=["Forum Posts"])

forum_service = ForumService()


def check_comment_content(content: str) -> tuple[bool, str | None]:
    if not content or not content.strip():
        return False, "评论内容不能为空"
    return True, None


async def _build_comment_response(db, comment, viewer_user_id=None) -> dict:
    return {
        "id": int(getattr(comment, "id", 0) or 0),
        "content": str(getattr(comment, "content", "")),
        "post_id": int(getattr(comment, "post_id", 0) or 0),
        "user_id": int(getattr(comment, "user_id", 0) or 0),
        "parent_id": getattr(comment, "parent_id", None),
        "like_count": getattr(comment, "like_count", 0),
        "images": [],
        "created_at": getattr(comment, "created_at", None),
        "review_status": getattr(comment, "review_status", None),
        "review_reason": getattr(comment, "review_reason", None),
        "reviewed_at": getattr(comment, "reviewed_at", None),
        "author": None,
        "is_liked": False,
        "replies": [],
    }


def _create_notification(db, *, title: str, content: str, user_id: int, type: str = "forum", **kwargs):
    pass


@router.get("/posts")
async def list_posts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    category: str | None = Query(default=None),
    keyword: str | None = Query(default=None, max_length=100),
    is_essence: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    posts, total = await ForumPostService.get_posts(db, page=page, page_size=page_size, category=category, keyword=keyword, is_essence=is_essence)
    items = []
    for p in posts:
        items.append({
            "id": p.id, "title": p.title, "content": p.content,
            "category": p.category, "user_id": p.user_id,
            "is_essence": p.is_essence, "is_hot": p.is_hot,
            "like_count": p.like_count, "comment_count": p.comment_count,
            "view_count": p.view_count, "favorite_count": p.favorite_count,
            "created_at": str(p.created_at) if p.created_at else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/hot")
async def list_hot_posts(
    limit: int = Query(default=10, ge=1, le=50),
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Post.is_deleted.is_(False), Post.is_hot.is_(True)]
    if category:
        conditions.append(Post.category == category)
    stmt = select(Post).where(*conditions).order_by(Post.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    posts = result.scalars().all()
    items = [{"id": p.id, "title": p.title, "category": p.category, "like_count": p.like_count, "comment_count": p.comment_count} for p in posts]
    return {"items": items}


@router.post("/posts")
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await forum_service.apply_content_filter_config_from_db(db)
    post = Post(
        title=post_data.title,
        content=post_data.content,
        category=post_data.category,
        cover_image=post_data.cover_image,
        user_id=current_user.id,
        review_status="approved",
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return {"id": post.id, "title": post.title, "content": post.content, "category": post.category, "user_id": post.user_id}


@router.get("/posts/{post_id}")
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Post).where(Post.id == post_id, Post.is_deleted.is_(False))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {
        "id": post.id, "title": post.title, "content": post.content,
        "category": post.category, "user_id": post.user_id,
        "is_essence": post.is_essence, "is_hot": post.is_hot,
        "like_count": post.like_count, "comment_count": post.comment_count,
        "view_count": post.view_count, "favorite_count": post.favorite_count,
        "created_at": str(post.created_at) if post.created_at else None,
    }


@router.put("/posts/{post_id}")
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Post).where(Post.id == post_id, Post.is_deleted.is_(False))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改")
    for field, value in post_data:
        if value is not None:
            setattr(post, field, value)
    await db.commit()
    await db.refresh(post)
    return {"id": post.id, "title": post.title, "content": post.content}


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Post).where(Post.id == post_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    post.is_deleted = True
    await db.commit()
    return {"success": True}


@router.get("/me/posts")
async def get_my_posts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Post.user_id == current_user.id, Post.is_deleted.is_(False)]
    count_stmt = select(func.count()).select_from(Post).where(*conditions)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = select(Post).where(*conditions).order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    posts = (await db.execute(stmt)).scalars().all()
    items = [{"id": p.id, "title": p.title, "category": p.category, "created_at": str(p.created_at) if p.created_at else None} for p in posts]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/me/posts/deleted")
async def get_my_deleted_posts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Post.user_id == current_user.id, Post.is_deleted.is_(True)]
    count_stmt = select(func.count()).select_from(Post).where(*conditions)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = select(Post).where(*conditions).order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    posts = (await db.execute(stmt)).scalars().all()
    items = [{"id": p.id, "title": p.title, "category": p.category} for p in posts]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/posts/{post_id}/recycle")
async def get_deleted_post_detail(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Post).where(Post.id == post_id, Post.is_deleted.is_(True))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {"id": post.id, "title": post.title, "content": post.content}


@router.post("/posts/{post_id}/restore")
async def restore_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Post).where(Post.id == post_id, Post.is_deleted.is_(True))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    post.is_deleted = False
    await db.commit()
    return {"success": True}


@router.delete("/posts/{post_id}/permanent")
async def permanently_delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Post).where(Post.id == post_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    await db.delete(post)
    await db.commit()
    return {"success": True}


@router.put("/posts/{post_id}/essence")
async def set_essence(
    post_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Post).where(Post.id == post_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    post.is_essence = data.get("is_essence", True)
    await db.commit()
    return {"success": True}


@router.put("/posts/{post_id}/pin")
async def set_pin(
    post_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Post).where(Post.id == post_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    post.is_pinned = data.get("is_pinned", True)
    await db.commit()
    return {"success": True}


@router.put("/posts/{post_id}/lock")
async def set_lock(
    post_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Post).where(Post.id == post_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    post.is_locked = data.get("is_locked", True)
    await db.commit()
    return {"success": True}


@router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    comment_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = comment_data.get("content", "")
    parent_id = comment_data.get("parent_id")

    ok, err = check_comment_content(content)
    if not ok:
        return JSONResponse(status_code=400, content={"error": {"message": err}})

    await forum_service.apply_content_filter_config_from_db(db)

    post = await forum_service.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    if parent_id:
        parent = await forum_service.get_comment(db, parent_id)
        if not parent:
            return JSONResponse(status_code=400, content={"error": {"message": "父评论不存在"}})
        if getattr(parent, "post_id", None) != post_id:
            return JSONResponse(status_code=400, content={"error": {"message": "父评论不属于该帖子"}})

    comment = await forum_service.create_comment(db, post_id=post_id, user_id=current_user.id, content=content, parent_id=parent_id)

    _create_notification(db, title="你的评论已提交审核", content=content, user_id=current_user.id, type="forum_comment")

    resp = await _build_comment_response(db, comment, viewer_user_id=current_user.id)
    return resp


@router.get("/posts/{post_id}/comments")
async def get_comments(
    post_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if current_user:
        post = await forum_service.get_post_any(db, post_id)
    else:
        post = await forum_service.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    viewer_user_id = current_user.id if current_user else None
    viewer_role = getattr(current_user, "role", None) if current_user else None
    include_unapproved = False

    comments, total = await forum_service.get_comments_visible(db, post_id, page, page_size, viewer_user_id, viewer_role, include_unapproved)
    return {"items": comments, "total": total, "page": page, "page_size": page_size}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.utils.permissions import is_owner_or_admin

    comment = await forum_service.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    if not is_owner_or_admin(current_user, comment.user_id):
        raise HTTPException(status_code=403, detail="无权删除")
    await forum_service.delete_comment(db, comment)
    return {"success": True}


@router.post("/comments/{comment_id}/restore")
async def restore_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.utils.permissions import is_owner_or_admin

    comment = await forum_service.get_comment_any(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    if not is_owner_or_admin(current_user, comment.user_id):
        raise HTTPException(status_code=403, detail="无权恢复")
    result = await forum_service.restore_comment(db, comment)
    return {"message": "已恢复", "success": result}


@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = await forum_service.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    liked, count = await forum_service.toggle_comment_like(db, comment_id, current_user.id)
    if liked:
        return {"message": "点赞成功", "liked": liked, "like_count": count}
    else:
        return {"message": "取消点赞", "liked": liked, "like_count": count}


@router.post("/posts/{post_id}/report")
async def report_post(post_id: int, data: dict = None):
    return {"success": True}


@router.post("/posts/{post_id}/share")
async def share_post(post_id: int, data: dict = None):
    return {"success": True}
