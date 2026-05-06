"""话题运营服务"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.topic import Topic
from app.models.post import Post
from app.models.ops_models import RecommendationSlot


class TopicOpsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def pin_post(
        self,
        post_id: int,
        duration_hours: int = 72,
        operator_id: int = 0
    ) -> bool:
        expires_at = datetime.now() + timedelta(hours=duration_hours)
        await self.db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(
                is_pinned=True,
                pinned_until=expires_at
            )
        )
        await self.db.commit()
        return True

    async def unpin_post(self, post_id: int) -> bool:
        await self.db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(is_pinned=False, pinned_until=None)
        )
        await self.db.commit()
        return True

    async def feature_post(self, post_id: int, operator_id: int = 0) -> bool:
        await self.db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(is_featured=True)
        )
        await self.db.commit()
        return True

    async def unfeature_post(self, post_id: int) -> bool:
        await self.db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(is_featured=False)
        )
        await self.db.commit()
        return True

    async def recommend_post(
        self,
        post_id: int,
        operator_id: int = 0
    ) -> bool:
        await self.db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(is_recommended=True)
        )
        await self.db.commit()
        return True

    async def unrecommend_post(self, post_id: int) -> bool:
        await self.db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(is_recommended=False)
        )
        await self.db.commit()
        return True

    async def update_topic_announcement(
        self,
        topic_id: int,
        content: str,
        operator_id: int = 0
    ) -> bool:
        await self.db.execute(
            update(Topic)
            .where(Topic.id == topic_id)
            .values(announcement=content)
        )
        await self.db.commit()
        return True

    async def get_recommendation_slots(
        self,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        query = select(RecommendationSlot)
        if not include_expired:
            query = query.where(
                RecommendationSlot.is_active == True,
                (RecommendationSlot.expires_at == None) | (RecommendationSlot.expires_at > datetime.now())
            )
        query = query.order_by(RecommendationSlot.position)

        result = await self.db.execute(query)
        slots = []
        for row in result.scalars().all():
            post_result = await self.db.execute(
                select(Post).where(Post.id == row.post_id)
            )
            post = post_result.scalar_one_or_none()

            slots.append({
                "id": row.id,
                "position": row.position,
                "post_id": row.post_id,
                "post_title": post.title if post else None,
                "label": row.label,
                "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                "is_active": row.is_active
            })

        return slots

    async def update_recommendation_slots(
        self,
        slots: List[Dict[str, Any]],
        operator_id: int = 0
    ) -> bool:
        await self.db.execute(
            update(RecommendationSlot)
            .where(RecommendationSlot.is_active == True)
            .values(is_active=False)
        )

        for slot_data in slots:
            expires_at = None
            if slot_data.get("duration_hours"):
                expires_at = datetime.now() + timedelta(hours=slot_data["duration_hours"])

            slot = RecommendationSlot(
                position=slot_data["position"],
                post_id=slot_data["post_id"],
                label=slot_data.get("label"),
                operator_id=operator_id,
                expires_at=expires_at,
                is_active=True
            )
            self.db.add(slot)

        await self.db.commit()
        return True

    async def cleanup_expired_recommendations(self) -> int:
        result = await self.db.execute(
            update(RecommendationSlot)
            .where(
                RecommendationSlot.is_active == True,
                RecommendationSlot.expires_at != None,
                RecommendationSlot.expires_at < datetime.now()
            )
            .values(is_active=False)
        )
        await self.db.commit()
        return result.rowcount
