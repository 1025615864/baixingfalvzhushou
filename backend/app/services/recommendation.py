from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.user_profile import UserProfile, UserInterestHistory, UserTagInteraction, UserOnboarding
from ..models.lawfirm import Lawyer, LawFirm, LawyerConsultation, LawyerReview
from ..models.knowledge import LegalKnowledge, KnowledgeCategory
from ..models.analytics import UserBehaviorLog
from .cache_service import cache_service


class RecommendationService:

    def __init__(self, db: AsyncSession, user: Optional[Any] = None):
        self.db = db
        self.user = user

    async def get_lawyer_recommendations(
        self,
        limit: int = 10,
        category: Optional[str] = None,
        city: Optional[str] = None,
    ) -> list[dict]:
        user_id = self.user.id if self.user else None
        tag_weights = await self._get_user_tag_weights(user_id) if user_id else {}

        query = (
            select(Lawyer)
            .options(selectinload(Lawyer.firm))
            .where(Lawyer.is_active == True)
        )

        if category:
            query = query.where(Lawyer.specialties.ilike(f"%{category}%"))

        if city:
            query = query.join(LawFirm, Lawyer.firm_id == LawFirm.id, isouter=True).where(
                LawFirm.city == city
            )

        result = await self.db.execute(query)
        lawyers = list(result.scalars().all())

        items = []
        for lawyer in lawyers:
            lawyer_tags = []
            if lawyer.specialties:
                lawyer_tags = [t.strip() for t in lawyer.specialties.split(",") if t.strip()]

            if user_id and tag_weights:
                score = self._compute_match_score(lawyer_tags, tag_weights)
            else:
                score = float(lawyer.rating or 0) + float(lawyer.review_count or 0) * 0.1

            firm_info = None
            if lawyer.firm:
                firm_info = {
                    "id": lawyer.firm.id,
                    "name": lawyer.firm.name,
                    "city": lawyer.firm.city,
                    "province": lawyer.firm.province,
                }

            items.append({
                "id": lawyer.id,
                "name": lawyer.name,
                "avatar": lawyer.avatar,
                "title": lawyer.title,
                "specialties": lawyer.specialties,
                "experience_years": lawyer.experience_years,
                "rating": lawyer.rating,
                "review_count": lawyer.review_count,
                "consultation_fee": lawyer.consultation_fee,
                "is_verified": lawyer.is_verified,
                "firm": firm_info,
                "match_score": round(score, 4),
            })

        items.sort(key=lambda x: x["match_score"], reverse=True)
        return items[:limit]

    async def get_lawyers_by_consultation(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[dict]:
        result = await self.db.execute(
            select(LawyerConsultation.category)
            .where(LawyerConsultation.user_id == user_id)
            .where(LawyerConsultation.category.isnot(None))
            .distinct()
        )
        categories = [row[0] for row in result.all()]

        if not categories:
            return []

        tag_weights = await self._get_user_tag_weights(user_id)

        conditions = []
        for cat in categories:
            conditions.append(Lawyer.specialties.ilike(f"%{cat}%"))

        from sqlalchemy import or_
        query = (
            select(Lawyer)
            .options(selectinload(Lawyer.firm))
            .where(Lawyer.is_active == True)
            .where(or_(*conditions))
        )

        result = await self.db.execute(query)
        lawyers = list(result.scalars().all())

        items = []
        for lawyer in lawyers:
            lawyer_tags = []
            if lawyer.specialties:
                lawyer_tags = [t.strip() for t in lawyer.specialties.split(",") if t.strip()]

            score = self._compute_match_score(lawyer_tags, tag_weights) if tag_weights else 0.0

            firm_info = None
            if lawyer.firm:
                firm_info = {
                    "id": lawyer.firm.id,
                    "name": lawyer.firm.name,
                    "city": lawyer.firm.city,
                }

            items.append({
                "id": lawyer.id,
                "name": lawyer.name,
                "avatar": lawyer.avatar,
                "title": lawyer.title,
                "specialties": lawyer.specialties,
                "experience_years": lawyer.experience_years,
                "rating": lawyer.rating,
                "review_count": lawyer.review_count,
                "is_verified": lawyer.is_verified,
                "firm": firm_info,
                "match_score": round(score, 4),
                "matched_categories": [c for c in categories if c and lawyer.specialties and c.lower() in lawyer.specialties.lower()],
            })

        items.sort(key=lambda x: x["match_score"], reverse=True)
        return items[:limit]

    async def get_lawyers_by_location(
        self,
        city: str,
        limit: int = 10,
    ) -> list[dict]:
        query = (
            select(Lawyer)
            .options(selectinload(Lawyer.firm))
            .join(LawFirm, Lawyer.firm_id == LawFirm.id, isouter=True)
            .where(Lawyer.is_active == True)
            .where(LawFirm.city == city)
            .order_by(Lawyer.rating.desc(), Lawyer.review_count.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        lawyers = list(result.scalars().all())

        items = []
        for lawyer in lawyers:
            firm_info = None
            if lawyer.firm:
                firm_info = {
                    "id": lawyer.firm.id,
                    "name": lawyer.firm.name,
                    "city": lawyer.firm.city,
                    "province": lawyer.firm.province,
                }

            items.append({
                "id": lawyer.id,
                "name": lawyer.name,
                "avatar": lawyer.avatar,
                "title": lawyer.title,
                "specialties": lawyer.specialties,
                "experience_years": lawyer.experience_years,
                "rating": lawyer.rating,
                "review_count": lawyer.review_count,
                "is_verified": lawyer.is_verified,
                "firm": firm_info,
                "match_score": round(float(lawyer.rating or 0) + float(lawyer.review_count or 0) * 0.1, 4),
            })

        return items

    async def get_post_recommendations(
        self,
        limit: int = 10,
        category: Optional[str] = None,
    ) -> list[dict]:
        return []

    async def get_news_recommendations(
        self,
        limit: int = 10,
        category: Optional[str] = None,
    ) -> list[dict]:
        return []

    async def get_knowledge_recommendations(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[dict]:
        tag_weights = await self._get_user_tag_weights(user_id)

        if not tag_weights:
            result = await self.db.execute(
                select(LegalKnowledge)
                .where(LegalKnowledge.is_active == True)
                .order_by(LegalKnowledge.weight.desc())
                .limit(limit)
            )
            knowledge_items = list(result.scalars().all())
            return [
                {
                    "id": k.id,
                    "title": k.title,
                    "category": k.category,
                    "knowledge_type": k.knowledge_type,
                    "summary": k.summary,
                    "keywords": k.keywords,
                    "match_score": round(float(k.weight or 1.0), 4),
                }
                for k in knowledge_items
            ]

        user_tags = list(tag_weights.keys())

        conditions = []
        for tag in user_tags:
            conditions.append(LegalKnowledge.category.ilike(f"%{tag}%"))
            conditions.append(LegalKnowledge.keywords.ilike(f"%{tag}%"))

        from sqlalchemy import or_
        query = (
            select(LegalKnowledge)
            .where(LegalKnowledge.is_active == True)
            .where(or_(*conditions))
        )

        result = await self.db.execute(query)
        knowledge_items = list(result.scalars().all())

        items = []
        for k in knowledge_items:
            k_tags = []
            if k.category:
                k_tags.append(k.category)
            if k.keywords:
                k_tags.extend([t.strip() for t in k.keywords.split(",") if t.strip()])

            score = self._compute_match_score(k_tags, tag_weights)
            items.append({
                "id": k.id,
                "title": k.title,
                "category": k.category,
                "knowledge_type": k.knowledge_type,
                "summary": k.summary,
                "keywords": k.keywords,
                "match_score": round(score, 4),
            })

        items.sort(key=lambda x: x["match_score"], reverse=True)
        return items[:limit]

    async def get_personalized_recommendations(
        self,
        user_id: int,
        lawyer_limit: int = 5,
        post_limit: int = 5,
        news_limit: int = 5,
    ) -> dict:
        lawyers = await self.get_lawyer_recommendations(limit=lawyer_limit)
        posts = await self.get_post_recommendations(limit=post_limit)
        news = await self.get_news_recommendations(limit=news_limit)

        return {
            "lawyers": lawyers,
            "posts": posts,
            "news": news,
            "similar_users_content": [],
        }

    async def get_enhanced_recommendations(
        self,
        recommendation_type: str = "hybrid",
        limit: int = 10,
    ) -> dict:
        user_id = self.user.id if self.user else None

        cache_key = f"rec:enhanced:{user_id}:{recommendation_type}:{limit}"
        cached = await cache_service.get_json(cache_key)
        if cached is not None:
            return cached

        items = []

        if recommendation_type in ("hybrid", "lawyer"):
            lawyers = await self.get_lawyer_recommendations(limit=limit)
            for l in lawyers:
                reason = ""
                if l.get("specialties"):
                    reason = f"擅长{l['specialties']}，与您的兴趣匹配"
                items.append({
                    "id": str(l["id"]),
                    "type": "lawyer",
                    "title": l["name"],
                    "score": l["match_score"],
                    "reason": reason,
                    "metadata": l,
                })

        if recommendation_type in ("hybrid", "knowledge") and user_id:
            knowledge = await self.get_knowledge_recommendations(user_id=user_id, limit=limit)
            for k in knowledge:
                reason = ""
                if k.get("category"):
                    reason = f"属于{k['category']}领域，与您的关注方向一致"
                items.append({
                    "id": str(k["id"]),
                    "type": "knowledge",
                    "title": k["title"],
                    "score": k["match_score"],
                    "reason": reason,
                    "metadata": k,
                })

        if recommendation_type in ("hybrid", "post"):
            posts = await self.get_post_recommendations(limit=limit)
            for p in posts:
                items.append({
                    "id": str(p["id"]),
                    "type": "post",
                    "title": p.get("title", ""),
                    "score": p.get("match_score", 0.0),
                    "reason": "",
                    "metadata": p,
                })

        if recommendation_type in ("hybrid", "news"):
            news = await self.get_news_recommendations(limit=limit)
            for n in news:
                items.append({
                    "id": str(n["id"]),
                    "type": "news",
                    "title": n.get("title", ""),
                    "score": n.get("match_score", 0.0),
                    "reason": "",
                    "metadata": n,
                })

        items.sort(key=lambda x: x["score"], reverse=True)
        items = items[:limit]

        result = {"items": items, "total": len(items), "source": f"{recommendation_type}_v1"}
        await cache_service.set_json(cache_key, result, expire=600)
        return result

    async def get_enhanced_home(
        self,
        user_id: int,
        lawyer_limit: int = 5,
        post_limit: int = 5,
        news_limit: int = 5,
        knowledge_limit: int = 5,
    ) -> dict:
        cache_key = f"rec:home:{user_id}:{lawyer_limit}:{post_limit}:{news_limit}:{knowledge_limit}"
        cached = await cache_service.get_json(cache_key)
        if cached is not None:
            return cached

        lawyers = await self.get_lawyer_recommendations(limit=lawyer_limit)
        posts = await self.get_post_recommendations(limit=post_limit)
        news = await self.get_news_recommendations(limit=news_limit)
        knowledge = await self.get_knowledge_recommendations(user_id=user_id, limit=knowledge_limit) if user_id else []

        result = {
            "lawyers": lawyers,
            "posts": posts,
            "news": news,
            "knowledge": knowledge,
            "hot_content": [],
        }

        await cache_service.set_json(cache_key, result, expire=600)
        return result

    async def get_home_recommendations(
        self,
        recommendation_limit: int = 10,
    ) -> dict:
        user_id = self.user.id if self.user else None

        lawyers = await self.get_lawyer_recommendations(limit=recommendation_limit)
        posts = await self.get_post_recommendations(limit=recommendation_limit)
        news = await self.get_news_recommendations(limit=recommendation_limit)
        knowledge = await self.get_knowledge_recommendations(user_id=user_id, limit=recommendation_limit) if user_id else []

        return {
            "lawyers": lawyers,
            "posts": posts,
            "news": news,
            "knowledge": knowledge,
        }

    async def record_interaction(
        self,
        user_id: int,
        content_id: str,
        content_type: str,
        tags: list[str] | None = None,
        interaction_type: str = "viewed",
        weight: float = 1.0,
    ) -> dict:
        now = datetime.now(timezone.utc)

        history = UserInterestHistory(
            user_id=user_id,
            behavior_type=content_type,
            content_tags=tags or [],
            interaction_type=interaction_type,
            weight=weight,
            content_id=content_id,
            content_type=content_type,
            created_at=now,
        )
        self.db.add(history)

        if tags:
            for tag in tags:
                result = await self.db.execute(
                    select(UserTagInteraction).where(
                        UserTagInteraction.user_id == user_id,
                        UserTagInteraction.tag == tag,
                    )
                )
                tag_interaction = result.scalar_one_or_none()

                if tag_interaction:
                    tag_interaction.interaction_count += 1
                    tag_interaction.total_weight += weight
                    tag_interaction.last_interaction_at = now
                    tag_interaction.updated_at = now
                else:
                    self.db.add(UserTagInteraction(
                        user_id=user_id,
                        tag=tag,
                        interaction_count=1,
                        total_weight=weight,
                        last_interaction_at=now,
                        created_at=now,
                        updated_at=now,
                    ))

        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if profile:
            current_weights = profile.interest_weights or {}
            if tags:
                for tag in tags:
                    current_weights[tag] = current_weights.get(tag, 0) + weight
            profile.interest_weights = current_weights
            profile.updated_at = now

            current_tags = set(profile.interest_tags or [])
            if tags:
                current_tags.update(tags)
            profile.interest_tags = list(current_tags)

        await self.db.flush()
        await self._invalidate_user_cache(user_id)

        return {"success": True}

    async def submit_feedback(
        self,
        user_id: int,
        recommendation_id: str,
        rating: int,
        reason: Optional[str] = None,
    ) -> dict:
        now = datetime.now(timezone.utc)

        log = UserBehaviorLog(
            user_id=user_id,
            action="recommendation_feedback",
            resource_type="recommendation",
            resource_id=int(recommendation_id) if recommendation_id.isdigit() else None,
            metadata_json=str({"rating": rating, "reason": reason}),
            created_at=now,
        )
        self.db.add(log)
        await self.db.flush()

        return {"success": True}

    async def get_survey(self) -> list[dict]:
        return [
            {
                "id": "role",
                "question": "您的身份是？",
                "type": "single_choice",
                "options": [
                    {"value": "individual", "label": "个人用户"},
                    {"value": "business", "label": "企业用户"},
                    {"value": "lawyer", "label": "律师"},
                ],
            },
            {
                "id": "legal_needs",
                "question": "您最关注哪些法律领域？",
                "type": "multi_choice",
                "options": [
                    {"value": "labor", "label": "劳动纠纷"},
                    {"value": "marriage", "label": "婚姻家庭"},
                    {"value": "contract", "label": "合同纠纷"},
                    {"value": "property", "label": "房产纠纷"},
                    {"value": "criminal", "label": "刑事案件"},
                    {"value": "traffic", "label": "交通事故"},
                    {"value": "intellectual", "label": "知识产权"},
                    {"value": "corporate", "label": "公司法务"},
                ],
            },
            {
                "id": "experience",
                "question": "您的法律经验水平？",
                "type": "single_choice",
                "options": [
                    {"value": "novice", "label": "完全不了解"},
                    {"value": "basic", "label": "了解一些基本概念"},
                    {"value": "experienced", "label": "有较多经验"},
                ],
            },
            {
                "id": "usage_frequency",
                "question": "您预计多久使用一次本平台？",
                "type": "single_choice",
                "options": [
                    {"value": "often", "label": "经常（每周）"},
                    {"value": "sometimes", "label": "偶尔（每月）"},
                    {"value": "rarely", "label": "很少（偶尔）"},
                ],
            },
            {
                "id": "budget",
                "question": "您的法律服务预算范围？",
                "type": "single_choice",
                "options": [
                    {"value": "free", "label": "仅免费咨询"},
                    {"value": "low", "label": "500元以内"},
                    {"value": "medium", "label": "500-2000元"},
                    {"value": "high", "label": "2000元以上"},
                ],
            },
            {
                "id": "location",
                "question": "您所在的城市？",
                "type": "text",
                "placeholder": "请输入城市名称",
            },
        ]

    async def complete_onboarding(
        self,
        user_id: int,
        answers: dict,
    ) -> dict:
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)

        interest_tags = []
        interest_weights = {}
        preferred_content_types = []

        if "legal_needs" in answers:
            needs = answers["legal_needs"]
            if isinstance(needs, list):
                interest_tags.extend(needs)
                for tag in needs:
                    interest_weights[tag] = 2.0

        if "role" in answers:
            role = answers["role"]
            if isinstance(role, str):
                interest_tags.append(role)
                interest_weights[role] = 1.5
                if role == "individual":
                    preferred_content_types.extend(["consultation", "knowledge"])
                elif role == "business":
                    preferred_content_types.extend(["contract", "corporate", "lawyer"])
                elif role == "lawyer":
                    preferred_content_types.extend(["knowledge", "case"])

        profile.interest_tags = interest_tags
        profile.interest_weights = interest_weights
        profile.preferred_content_types = preferred_content_types
        profile.experience_level = answers.get("experience", "novice")
        profile.usage_frequency = answers.get("usage_frequency", "unknown")
        profile.budget_range = answers.get("budget", None)
        profile.location = answers.get("location", None)
        profile.onboarding_completed = True
        profile.onboarding_completed_at = now
        profile.updated_at = now

        for tag in interest_tags:
            tag_result = await self.db.execute(
                select(UserTagInteraction).where(
                    UserTagInteraction.user_id == user_id,
                    UserTagInteraction.tag == tag,
                )
            )
            tag_interaction = tag_result.scalar_one_or_none()
            if tag_interaction:
                tag_interaction.interaction_count += 1
                tag_interaction.total_weight += interest_weights.get(tag, 1.0)
                tag_interaction.last_interaction_at = now
                tag_interaction.updated_at = now
            else:
                self.db.add(UserTagInteraction(
                    user_id=user_id,
                    tag=tag,
                    interaction_count=1,
                    total_weight=interest_weights.get(tag, 1.0),
                    last_interaction_at=now,
                    created_at=now,
                    updated_at=now,
                ))

        await self.db.flush()

        return {
            "success": True,
            "profile": {
                "interest_tags": profile.interest_tags,
                "interest_weights": profile.interest_weights,
                "preferred_content_types": profile.preferred_content_types,
                "usage_frequency": profile.usage_frequency,
                "onboarding_completed": profile.onboarding_completed,
                "experience_level": profile.experience_level,
                "location": profile.location,
                "budget_range": profile.budget_range,
            },
        }

    async def should_show_onboarding(
        self,
        user_id: int,
    ) -> bool:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return True

        return not profile.onboarding_completed

    async def get_weights(
        self,
        user_id: int,
    ) -> dict:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return {"weights": {}}

        return {"weights": profile.interest_weights or {}}

    def _compute_match_score(
        self,
        item_tags: list[str],
        user_tag_weights: dict[str, float],
    ) -> float:
        score = 0.0
        for tag in item_tags:
            if tag in user_tag_weights:
                score += user_tag_weights[tag]
        return score

    async def _get_user_tag_weights(
        self,
        user_id: Optional[int],
    ) -> dict[str, float]:
        if not user_id:
            return {}

        result = await self.db.execute(
            select(UserTagInteraction).where(
                UserTagInteraction.user_id == user_id,
            )
        )
        interactions = list(result.scalars().all())

        return {i.tag: i.total_weight for i in interactions}

    async def _invalidate_user_cache(
        self,
        user_id: int,
    ) -> None:
        await cache_service.clear_pattern(f"rec:*:{user_id}:*")
