"""评论服务 - 业务逻辑层"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from fastapi import HTTPException

from ..models.comment import Comment
from ..models.post import Post
from ..middleware.auth import AuthUser


def utc_now():
    return datetime.now(timezone.utc)


class CommentService:
    def __init__(self, db: AsyncSession, user_client=None, event_bus=None):
        self.db = db
        self.user_client = user_client
        self.event_bus = event_bus

    async def create_comment(
        self,
        post_id: int,
        user_id: int,
        content: str,
        parent_id: Optional[int] = None,
        reply_to_user_id: Optional[int] = None
    ) -> Comment:
        from .ops.user_ops_service import UserOpsService
        ops_service = UserOpsService(self.db)
        if await ops_service.is_user_penalized(user_id, ["mute", "ban"]):
            raise HTTPException(status_code=403, detail="您因违规已被禁言或封禁，无法评论")

        post_result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        post = post_result.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        user_info = None
        if self.user_client:
            user_info = await self.user_client.get_user_info(user_id)

        author_name = user_info.get("nickname") if user_info else f"用户{user_id}"
        author_avatar = user_info.get("avatar") if user_info else None
        is_lawyer = user_info.get("is_lawyer", False) if user_info else False

        reply_to_user_name = None
        if reply_to_user_id and self.user_client:
            reply_user_info = await self.user_client.get_user_info(reply_to_user_id)
            reply_to_user_name = reply_user_info.get("nickname") if reply_user_info else None

        floor_number = None
        if parent_id is None:
            max_floor_result = await self.db.execute(
                select(func.max(Comment.floor_number)).where(
                    and_(
                        Comment.post_id == post_id,
                        Comment.parent_id.is_(None)
                    )
                )
            )
            max_floor = max_floor_result.scalar() or 0
            floor_number = max_floor + 1

        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            author_name=author_name,
            author_avatar=author_avatar,
            is_lawyer=is_lawyer,
            content=content,
            parent_id=parent_id,
            reply_to_user_id=reply_to_user_id,
            reply_to_user_name=reply_to_user_name,
            floor_number=floor_number,
            status="published"
        )

        self.db.add(comment)

        post.comment_count += 1
        await self.db.commit()
        await self.db.refresh(comment)

        if self.event_bus:
            await self.event_bus.publish_comment_created(comment)

        return comment

    async def get_comments(
        self,
        post_id: int,
        page: int = 1,
        page_size: int = 20,
        nested: bool = True
    ) -> tuple[List[dict], int]:
        query = select(Comment).where(
            and_(
                Comment.post_id == post_id,
                Comment.status != "deleted"
            )
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        if nested:
            query = query.order_by(Comment.floor_number, Comment.created_at)
        else:
            query = query.where(Comment.parent_id.is_(None))
            query = query.order_by(Comment.floor_number, Comment.created_at)

        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        comments = result.scalars().all()

        if nested:
            comment_dicts = []
            for c in comments:
                comment_dicts.append({
                    "id": c.id,
                    "post_id": c.post_id,
                    "user_id": c.user_id,
                    "author_name": c.author_name,
                    "author_avatar": c.author_avatar,
                    "is_lawyer": c.is_lawyer,
                    "content": c.content,
                    "parent_id": c.parent_id,
                    "reply_to_user_id": c.reply_to_user_id,
                    "reply_to_user_name": c.reply_to_user_name,
                    "floor_number": c.floor_number,
                    "like_count": c.like_count,
                    "created_at": c.created_at,
                    "replies": []
                })

            id_to_comment = {c["id"]: c for c in comment_dicts}
            for c in comment_dicts:
                if c["parent_id"] and c["parent_id"] in id_to_comment:
                    id_to_comment[c["parent_id"]]["replies"].append(c)

            root_comments = [c for c in comment_dicts if c["parent_id"] is None]
            return root_comments, total

        return list(comments), total

    async def delete_comment(self, comment_id: int, current_user: AuthUser) -> bool:
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        can_delete = (
            comment.user_id == current_user.id or
            current_user.role == "admin"
        )

        if not can_delete:
            post_result = await self.db.execute(
                select(Post).where(Post.id == comment.post_id)
            )
            post = post_result.scalar_one_or_none()
            if post and post.user_id == current_user.id:
                can_delete = True

        if not can_delete:
            raise HTTPException(status_code=403, detail="无权删除此评论")

        comment.status = "deleted"
        comment.is_deleted = True
        comment.deleted_at = utc_now()

        post_result = await self.db.execute(
            select(Post).where(Post.id == comment.post_id)
        )
        post = post_result.scalar_one_or_none()
        if post:
            post.comment_count = max(0, post.comment_count - 1)

        await self.db.commit()

        if self.event_bus:
            await self.event_bus.publish_comment_deleted(comment)

        return True

    async def like_comment(self, comment_id: int, user_id: int) -> dict:
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        comment.like_count += 1
        await self.db.commit()

        return {"like_count": comment.like_count}
