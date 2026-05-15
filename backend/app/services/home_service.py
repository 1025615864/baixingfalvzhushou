from __future__ import annotations

from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ..models.user import User
from ..models.lawfirm import Lawyer
from ..models.knowledge import LegalKnowledge
from ..models.analytics import UserBehaviorLog
from ..models.user_profile import UserProfile
from .cache_service import cache_service

_BANNERS = [
    {"id": "1", "title": "AI 智能法律咨询", "subtitle": "专业律师 24 小时在线为您服务", "image_url": "/assets/banners/ai-banner.png", "link": "/ai-consultation", "sort_order": 1, "is_active": True},
    {"id": "2", "title": "民法典专题解读", "subtitle": "了解与您生活息息相关的法律知识", "image_url": "/assets/banners/civil-code.png", "link": "/knowledge/civil-code", "sort_order": 2, "is_active": True},
    {"id": "3", "title": "律师匹配服务", "subtitle": "智能匹配最适合您的专业律师", "image_url": "/assets/banners/lawyer-match.png", "link": "/lawyer-matching", "sort_order": 3, "is_active": True},
    {"id": "4", "title": "积分商城上新", "subtitle": "法律文书模板、咨询服务积分兑换", "image_url": "/assets/banners/points-mall.png", "link": "/points/mall", "sort_order": 4, "is_active": True},
]

_QUICK_ACTIONS = [
    {"id": "ai", "label": "AI 咨询", "icon": "robot", "type": "feature", "link": "/ai-consultation", "badge": None, "content": "智能法律问答"},
    {"id": "lawyer", "label": "找律师", "icon": "user-tie", "type": "feature", "link": "/lawyer-matching", "badge": None, "content": "专业律师匹配"},
    {"id": "consult", "label": "法律咨询", "icon": "comment-dots", "type": "feature", "link": "/consultations", "badge": 3, "content": "在线法律咨询"},
    {"id": "document", "label": "文书模板", "icon": "file-contract", "type": "feature", "link": "/legal-document-mall", "badge": None, "content": "法律文书生成"},
    {"id": "contract", "label": "合同审查", "icon": "file-signature", "type": "feature", "link": "/contracts", "badge": None, "content": "合同审查工具"},
    {"id": "points", "label": "积分商城", "icon": "gift", "type": "feature", "link": "/points", "badge": None, "content": "积分兑换好礼"},
    {"id": "forum", "label": "法律社区", "icon": "users", "type": "community", "link": "/forum", "badge": 12, "content": "法律交流社区"},
    {"id": "news", "label": "法律资讯", "icon": "newspaper", "type": "content", "link": "/news", "badge": None, "content": "法律热点解读"},
]


class HomeService:
    def __init__(self, db: AsyncSession, user: User | None = None) -> None:
        self.db = db
        self.user = user

    async def get_home_data(self, user_id: int | None = None) -> dict[str, Any]:
        banners = await self.get_banners()
        quick_actions = await self.get_quick_actions()
        recommendations = await self._build_recommendations(limit=6)
        stats = await self.get_stats()
        recent_activity = await self._get_recent_activity(user_id)
        return {
            "banners": banners,
            "quick_actions": quick_actions,
            "recommendations": recommendations,
            "stats": stats,
            "recent_activity": recent_activity,
        }

    async def get_recommendations(
        self,
        user_id: int | None = None,
        page: int = 1,
        page_size: int = 10,
        recommendation_type: str | None = None,
    ) -> dict[str, Any]:
        items: list[dict[str, Any]] = []

        if recommendation_type is None or recommendation_type == "lawyer":
            lawyer_rows = await self._query_top_lawyers(limit=page_size * 2)
            for row in lawyer_rows:
                items.append(self._lawyer_to_recommendation(row))

        if recommendation_type is None or recommendation_type == "article":
            knowledge_rows = await self._query_top_knowledge(limit=page_size * 2)
            for row in knowledge_rows:
                items.append(self._knowledge_to_recommendation(row))

        if recommendation_type and recommendation_type not in ("lawyer", "article"):
            filtered = []
        elif recommendation_type:
            filtered = items
        else:
            filtered = items

        total = len(filtered)
        start = (page - 1) * page_size
        page_items = filtered[start:start + page_size]

        return {
            "recommendations": page_items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_quick_actions(self) -> list[dict[str, Any]]:
        cached = await cache_service.get_json("home:quick_actions")
        if cached is not None:
            return cached
        await cache_service.set_json("home:quick_actions", _QUICK_ACTIONS, expire=3600)
        return _QUICK_ACTIONS

    async def get_stats(self) -> dict[str, Any]:
        cached = await cache_service.get_json("home:stats")
        if cached is not None:
            return cached

        total_users = await self.db.scalar(select(func.count()).select_from(User))
        total_lawyers = await self.db.scalar(select(func.count()).select_from(Lawyer))
        total_knowledge = await self.db.scalar(select(func.count()).select_from(LegalKnowledge))

        data = {
            "total_users": total_users or 0,
            "total_lawyers": total_lawyers or 0,
            "total_consultations": 0,
            "total_documents": 0,
            "today_active_users": 0,
            "monthly_resolved_cases": 0,
            "total_knowledge": total_knowledge or 0,
        }
        await cache_service.set_json("home:stats", data, expire=300)
        return data

    async def get_banners(self) -> list[dict[str, Any]]:
        cached = await cache_service.get_json("home:banners")
        if cached is not None:
            return cached
        await cache_service.set_json("home:banners", _BANNERS, expire=3600)
        return _BANNERS

    async def track_click(self, user_id: int | None, data: dict[str, Any]) -> None:
        try:
            import json
            log = UserBehaviorLog(
                user_id=user_id,
                action="click",
                resource_type=data.get("resource_type"),
                resource_id=data.get("resource_id"),
                metadata_json=json.dumps(data, ensure_ascii=False) if data else None,
                ip_address=data.get("ip_address"),
                user_agent=data.get("user_agent"),
                referrer=data.get("referrer"),
                session_id=data.get("session_id"),
            )
            self.db.add(log)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def set_interests(self, user_id: int | None, interests: list[str]) -> dict[str, Any]:
        if user_id is None:
            return {"success": False, "interests": interests}

        try:
            result = await self.db.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()

            if profile is None:
                profile = UserProfile(user_id=user_id, interest_tags=interests)
                self.db.add(profile)
            else:
                profile.interest_tags = interests

            await self.db.commit()
            return {"success": True, "interests": interests}
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def _build_recommendations(self, limit: int = 6) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        half = limit // 2

        lawyer_rows = await self._query_top_lawyers(limit=half)
        for row in lawyer_rows:
            items.append(self._lawyer_to_recommendation(row))

        knowledge_rows = await self._query_top_knowledge(limit=limit - len(items))
        for row in knowledge_rows:
            items.append(self._knowledge_to_recommendation(row))

        return items[:limit]

    async def _query_top_lawyers(self, limit: int = 3) -> list[Lawyer]:
        stmt = (
            select(Lawyer)
            .where(Lawyer.is_active == True, Lawyer.is_verified == True)
            .order_by(Lawyer.rating.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _query_top_knowledge(self, limit: int = 3) -> list[LegalKnowledge]:
        stmt = (
            select(LegalKnowledge)
            .where(LegalKnowledge.is_active == True)
            .order_by(LegalKnowledge.weight.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_recent_activity(self, user_id: int | None) -> list[dict[str, Any]]:
        if user_id is None:
            return []

        stmt = (
            select(UserBehaviorLog)
            .where(UserBehaviorLog.user_id == user_id)
            .order_by(UserBehaviorLog.created_at.desc())
            .limit(10)
        )
        result = await self.db.execute(stmt)
        logs = list(result.scalars().all())

        activities: list[dict[str, Any]] = []
        for log in logs:
            activities.append({
                "id": str(log.id),
                "type": log.resource_type or log.action,
                "title": f"{log.action} - {log.resource_type or ''}",
                "description": log.metadata_json or "",
                "timestamp": log.created_at.isoformat() if log.created_at else "",
                "link": f"/{log.resource_type}/{log.resource_id}" if log.resource_type else "",
            })
        return activities

    @staticmethod
    def _lawyer_to_recommendation(lawyer: Lawyer) -> dict[str, Any]:
        tags = lawyer.specialties.split(",") if lawyer.specialties else []
        return {
            "id": str(lawyer.id),
            "type": "lawyer",
            "title": f"{lawyer.name} - {lawyer.title or '律师'}",
            "content": lawyer.introduction or "",
            "tags": tags,
            "image_url": lawyer.avatar or "",
            "score": int(lawyer.rating * 20) if lawyer.rating else 0,
            "link": f"/lawyers/{lawyer.id}",
        }

    @staticmethod
    def _knowledge_to_recommendation(knowledge: LegalKnowledge) -> dict[str, Any]:
        tags = knowledge.keywords.split(",") if knowledge.keywords else []
        return {
            "id": str(knowledge.id),
            "type": "article",
            "title": knowledge.title,
            "content": knowledge.summary or knowledge.content[:100] if knowledge.content else "",
            "tags": tags,
            "image_url": "",
            "score": int(knowledge.weight * 20) if knowledge.weight else 0,
            "link": f"/knowledge/{knowledge.id}",
        }
