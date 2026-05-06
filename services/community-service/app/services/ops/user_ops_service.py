"""用户运营服务"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.models.ops_models import UserPenalty, UserAppeal
from app.models.post import Post
from app.models.comment import Comment


class UserOpsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def penalize_user(
        self,
        user_id: int,
        penalty_type: str,
        reason: str = None,
        duration_hours: int = None,
        related_post_id: int = None,
        related_comment_id: int = None,
        operator_id: int = 0
    ) -> UserPenalty:
        expires_at = None
        if duration_hours:
            expires_at = datetime.now() + timedelta(hours=duration_hours)

        penalty = UserPenalty(
            user_id=user_id,
            type=penalty_type,
            reason=reason,
            related_post_id=related_post_id,
            related_comment_id=related_comment_id,
            operator_id=operator_id,
            duration_hours=duration_hours,
            expires_at=expires_at,
            is_active=True
        )
        self.db.add(penalty)
        await self.db.commit()
        await self.db.refresh(penalty)
        return penalty

    async def revoke_penalty(
        self,
        user_id: int,
        revoked_by: int,
        reason: str = None
    ) -> bool:
        result = await self.db.execute(
            update(UserPenalty)
            .where(
                UserPenalty.user_id == user_id,
                UserPenalty.is_active == True
            )
            .values(
                is_active=False,
                revoked_at=datetime.now(),
                revoked_by=revoked_by,
                revoked_reason=reason
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_active_penalty(self, user_id: int) -> Optional[UserPenalty]:
        result = await self.db.execute(
            select(UserPenalty).where(
                UserPenalty.user_id == user_id,
                UserPenalty.is_active == True,
                (UserPenalty.expires_at == None) | (UserPenalty.expires_at > datetime.now())
            )
        )
        return result.scalar_one_or_none()

    async def get_user_penalties(
        self,
        user_id: int,
        include_inactive: bool = False
    ) -> List[UserPenalty]:
        query = select(UserPenalty).where(UserPenalty.user_id == user_id)
        if not include_inactive:
            query = query.where(UserPenalty.is_active == True)
        query = query.order_by(UserPenalty.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        from sqlalchemy import func

        posts_result = await self.db.execute(
            select(func.count()).select_from(Post)
            .where(Post.user_id == user_id, Post.is_deleted == False)
        )
        post_count = posts_result.scalar() or 0

        comments_result = await self.db.execute(
            select(func.count()).select_from(Comment)
            .where(Comment.user_id == user_id, Comment.is_deleted == False)
        )
        comment_count = comments_result.scalar() or 0

        violations_result = await self.db.execute(
            select(func.count()).select_from(UserPenalty)
            .where(UserPenalty.user_id == user_id)
        )
        violation_count = violations_result.scalar() or 0

        active_penalty = await self.get_active_penalty(user_id)

        return {
            "user_id": user_id,
            "post_count": post_count,
            "comment_count": comment_count,
            "violation_count": violation_count,
            "active_penalty": {
                "type": active_penalty.type,
                "reason": active_penalty.reason,
                "expires_at": active_penalty.expires_at.isoformat() if active_penalty and active_penalty.expires_at else None
            } if active_penalty else None
        }

    async def get_user_appeals(
        self,
        status: str = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        query = select(UserAppeal)
        if status:
            query = query.where(UserAppeal.status == status)

        from sqlalchemy import func
        count_result = await self.db.execute(
            select(func.count()).select_from(UserAppeal)
            .where(UserAppeal.status == status) if status else select(func.count()).select_from(UserAppeal)
        )
        total = count_result.scalar() or 0

        query = query.order_by(UserAppeal.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        appeals = []
        for row in result.scalars().all():
            appeals.append({
                "id": row.id,
                "user_id": row.user_id,
                "penalty_id": row.penalty_id,
                "reason": row.reason,
                "evidence": row.evidence,
                "status": row.status,
                "handler_id": row.handler_id,
                "handle_reason": row.handle_reason,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "handled_at": row.handled_at.isoformat() if row.handled_at else None
            })

        return appeals, total

    async def handle_appeal(
        self,
        appeal_id: int,
        action: str,
        handle_reason: str = None,
        handler_id: int = 0
    ) -> bool:
        appeal_result = await self.db.execute(
            select(UserAppeal).where(UserAppeal.id == appeal_id)
        )
        appeal = appeal_result.scalar_one_or_none()
        if not appeal:
            return False

        appeal.status = "accepted" if action == "accept" else "rejected"
        appeal.handler_id = handler_id
        appeal.handle_reason = handle_reason
        appeal.handled_at = datetime.now()

        if action == "accept":
            penalty_result = await self.db.execute(
                select(UserPenalty).where(UserPenalty.id == appeal.penalty_id)
            )
            penalty = penalty_result.scalar_one_or_none()
            if penalty:
                penalty.is_active = False
                penalty.revoked_at = datetime.now()
                penalty.revoked_by = handler_id
                penalty.revoked_reason = f"申诉通过: {handle_reason}"

        await self.db.commit()
        return True

    async def is_user_penalized(self, user_id: int, penalty_types: List[str] = None) -> bool:
        active_penalty = await self.get_active_penalty(user_id)
        if not active_penalty:
            return False
        if penalty_types and active_penalty.type not in penalty_types:
            return False
        return True
