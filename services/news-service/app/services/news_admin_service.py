"""新闻管理服务 - 管理员审核/编辑分配/统计/批量操作"""
import logging
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, and_, or_, update, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    News, NewsCategory, NewsTag, NewsTagAssociation,
    NewsAuditLog, NewsEditorAssignment, NewsOperationStats,
    NewsComment, UserNewsInteraction,
)

logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    "draft": ["review", "archived"],
    "review": ["approved", "rejected", "draft"],
    "approved": ["published", "review"],
    "published": ["archived"],
    "rejected": ["draft", "review"],
    "archived": ["draft"],
}


class NewsAdminService:
    """新闻管理服务"""

    async def get_audit_queue(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        conditions = []
        if status:
            conditions.append(News.status == status)
        else:
            conditions.append(News.status.in_(["review", "approved"]))

        if category_id:
            conditions.append(News.category_id == category_id)

        base_query = select(News).where(*conditions).order_by(News.created_at.asc())
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        query = base_query.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(query)
        news_list = result.scalars().all()

        items = []
        for n in news_list:
            assignment = await self._get_active_assignment(session, n.id)
            items.append({
                "id": n.id,
                "title": n.title,
                "status": n.status,
                "category_id": n.category_id,
                "author": n.author,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "updated_at": n.updated_at.isoformat() if n.updated_at else None,
                "assigned_editor": assignment.editor_name if assignment else None,
                "assigned_editor_id": assignment.editor_id if assignment else None,
            })

        return items, total

    async def submit_for_review(
        self,
        session: AsyncSession,
        news_id: int,
        operator_id: int,
        operator_name: Optional[str] = None,
    ) -> News:
        news = await session.get(News, news_id)
        if not news:
            raise ValueError("新闻不存在")

        if news.status not in VALID_TRANSITIONS.get("draft", []):
            if news.status != "draft":
                raise ValueError(f"当前状态 {news.status} 不可提交审核，仅草稿可提交")

        from_status = news.status
        news.status = "review"
        news.updated_at = datetime.now(timezone.utc)
        await session.flush()

        await self._create_audit_log(
            session, news_id, operator_id, operator_name,
            "submit_review", from_status, "review",
            "提交审核",
        )
        return news

    async def assign_editor(
        self,
        session: AsyncSession,
        news_id: int,
        editor_id: int,
        editor_name: Optional[str] = None,
        assigned_by: int = 0,
        assigned_by_name: Optional[str] = None,
    ) -> NewsEditorAssignment:
        news = await session.get(News, news_id)
        if not news:
            raise ValueError("新闻不存在")

        existing = await self._get_active_assignment(session, news_id)
        if existing:
            existing.status = "reassigned"
            existing.updated_at = datetime.now(timezone.utc)
            await session.flush()

        assignment = NewsEditorAssignment(
            news_id=news_id,
            editor_id=editor_id,
            editor_name=editor_name,
            assigned_by=assigned_by,
            assigned_by_name=assigned_by_name,
            status="pending",
        )
        session.add(assignment)
        await session.flush()

        await self._create_audit_log(
            session, news_id, assigned_by, assigned_by_name,
            "assign_editor", news.status, news.status,
            f"分配编辑：{editor_name or editor_id}",
            {"editor_id": editor_id, "editor_name": editor_name},
        )
        return assignment

    async def review_news(
        self,
        session: AsyncSession,
        news_id: int,
        reviewer_id: int,
        reviewer_name: Optional[str] = None,
        action: str = "approve",
        comment: Optional[str] = None,
    ) -> News:
        news = await session.get(News, news_id)
        if not news:
            raise ValueError("新闻不存在")

        if news.status != "review":
            raise ValueError(f"当前状态 {news.status} 不可审核，仅待审核状态可审核")

        from_status = news.status
        if action == "approve":
            news.status = "approved"
            audit_action = "approve"
            audit_comment = comment or "审核通过"
        elif action == "reject":
            news.status = "rejected"
            audit_action = "reject"
            audit_comment = comment or "审核拒绝"
        else:
            raise ValueError(f"无效的审核操作: {action}")

        news.updated_at = datetime.now(timezone.utc)
        await session.flush()

        assignment = await self._get_active_assignment(session, news_id)
        if assignment:
            assignment.status = "completed" if action == "approve" else "rejected"
            assignment.review_comment = comment
            assignment.reviewed_at = datetime.now(timezone.utc)
            assignment.updated_at = datetime.now(timezone.utc)
            await session.flush()

        await self._create_audit_log(
            session, news_id, reviewer_id, reviewer_name,
            audit_action, from_status, news.status,
            audit_comment,
        )
        return news

    async def publish_approved_news(
        self,
        session: AsyncSession,
        news_id: int,
        operator_id: int,
        operator_name: Optional[str] = None,
    ) -> News:
        news = await session.get(News, news_id)
        if not news:
            raise ValueError("新闻不存在")

        if news.status != "approved":
            raise ValueError(f"当前状态 {news.status} 不可发布，仅已通过状态可发布")

        from_status = news.status
        news.status = "published"
        news.published_at = datetime.now(timezone.utc)
        news.updated_at = datetime.now(timezone.utc)
        await session.flush()

        await self._create_audit_log(
            session, news_id, operator_id, operator_name,
            "publish", from_status, "published",
            "发布新闻",
        )
        return news

    async def batch_update_status(
        self,
        session: AsyncSession,
        news_ids: List[int],
        target_status: str,
        operator_id: int,
        operator_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        success_ids = []
        failed_items = []

        for news_id in news_ids:
            try:
                news = await session.get(News, news_id)
                if not news:
                    failed_items.append({"id": news_id, "reason": "不存在"})
                    continue

                if target_status not in VALID_TRANSITIONS.get(news.status, []):
                    failed_items.append({"id": news_id, "reason": f"不可从 {news.status} 变更为 {target_status}"})
                    continue

                from_status = news.status
                news.status = target_status
                news.updated_at = datetime.now(timezone.utc)

                if target_status == "published" and news.published_at is None:
                    news.published_at = datetime.now(timezone.utc)

                await self._create_audit_log(
                    session, news_id, operator_id, operator_name,
                    f"batch_{target_status}", from_status, target_status,
                    f"批量操作：变更为 {target_status}",
                )
                success_ids.append(news_id)
            except Exception as e:
                failed_items.append({"id": news_id, "reason": str(e)})

        await session.flush()
        return {"success_count": len(success_ids), "failed_count": len(failed_items), "failed_items": failed_items}

    async def get_dashboard_stats(self, session: AsyncSession) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        status_counts = {}
        for status in ["draft", "review", "approved", "published", "rejected", "archived"]:
            count_q = select(func.count()).select_from(News).where(News.status == status)
            result = await session.execute(count_q)
            status_counts[status] = result.scalar() or 0

        today_published_q = select(func.count()).select_from(News).where(
            News.status == "published",
            News.published_at >= today_start,
        )
        result = await session.execute(today_published_q)
        today_published = result.scalar() or 0

        week_published_q = select(func.count()).select_from(News).where(
            News.status == "published",
            News.published_at >= week_ago,
        )
        result = await session.execute(week_published_q)
        week_published = result.scalar() or 0

        pending_review_q = select(func.count()).select_from(News).where(
            News.status == "review",
        )
        result = await session.execute(pending_review_q)
        pending_review = result.scalar() or 0

        total_views_q = select(func.coalesce(func.sum(News.view_count), 0)).where(
            News.published_at >= month_ago,
        )
        result = await session.execute(total_views_q)
        month_views = result.scalar() or 0

        total_likes_q = select(func.coalesce(func.sum(News.like_count), 0)).where(
            News.published_at >= month_ago,
        )
        result = await session.execute(total_likes_q)
        month_likes = result.scalar() or 0

        avg_review_time_q = select(
            func.avg(
                func.extract("epoch", NewsEditorAssignment.reviewed_at - NewsEditorAssignment.created_at) / 3600
            )
        ).where(
            NewsEditorAssignment.status.in_(["completed", "rejected"]),
            NewsEditorAssignment.reviewed_at >= month_ago,
        )
        result = await session.execute(avg_review_time_q)
        avg_review_hours = round(float(result.scalar() or 0), 2)

        top_news_q = select(News).where(
            News.status == "published",
            News.published_at >= month_ago,
        ).order_by(News.view_count.desc()).limit(10)
        result = await session.execute(top_news_q)
        top_news = [
            {"id": n.id, "title": n.title, "view_count": n.view_count, "like_count": n.like_count}
            for n in result.scalars().all()
        ]

        return {
            "status_counts": status_counts,
            "today_published": today_published,
            "week_published": week_published,
            "pending_review": pending_review,
            "month_views": month_views,
            "month_likes": month_likes,
            "avg_review_hours": avg_review_hours,
            "top_news": top_news,
        }

    async def get_audit_logs(
        self,
        session: AsyncSession,
        news_id: Optional[int] = None,
        operator_id: Optional[int] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        conditions = []
        if news_id:
            conditions.append(NewsAuditLog.news_id == news_id)
        if operator_id:
            conditions.append(NewsAuditLog.operator_id == operator_id)
        if action:
            conditions.append(NewsAuditLog.action == action)

        base_query = select(NewsAuditLog).where(*conditions).order_by(NewsAuditLog.created_at.desc())
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        query = base_query.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(query)
        logs = result.scalars().all()

        items = [
            {
                "id": log.id,
                "news_id": log.news_id,
                "operator_id": log.operator_id,
                "operator_name": log.operator_name,
                "action": log.action,
                "from_status": log.from_status,
                "to_status": log.to_status,
                "comment": log.comment,
                "extra_data": log.extra_data,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
        return items, total

    async def get_editor_workload(
        self,
        session: AsyncSession,
    ) -> List[Dict[str, Any]]:
        result = await session.execute(
            select(
                NewsEditorAssignment.editor_id,
                NewsEditorAssignment.editor_name,
                NewsEditorAssignment.status,
                func.count().label("count"),
            )
            .group_by(
                NewsEditorAssignment.editor_id,
                NewsEditorAssignment.editor_name,
                NewsEditorAssignment.status,
            )
        )
        rows = result.all()

        editor_map: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            eid = row.editor_id
            if eid not in editor_map:
                editor_map[eid] = {
                    "editor_id": eid,
                    "editor_name": row.editor_name,
                    "pending": 0,
                    "completed": 0,
                    "rejected": 0,
                    "reassigned": 0,
                }
            editor_map[eid][row.status] = row.count

        return list(editor_map.values())

    async def _get_active_assignment(self, session: AsyncSession, news_id: int) -> Optional[NewsEditorAssignment]:
        result = await session.execute(
            select(NewsEditorAssignment).where(
                NewsEditorAssignment.news_id == news_id,
                NewsEditorAssignment.status == "pending",
            )
        )
        return result.scalar_one_or_none()

    async def _create_audit_log(
        self,
        session: AsyncSession,
        news_id: int,
        operator_id: int,
        operator_name: Optional[str],
        action: str,
        from_status: Optional[str],
        to_status: Optional[str],
        comment: Optional[str] = None,
        extra_data: Optional[Dict] = None,
    ) -> NewsAuditLog:
        log = NewsAuditLog(
            news_id=news_id,
            operator_id=operator_id,
            operator_name=operator_name,
            action=action,
            from_status=from_status,
            to_status=to_status,
            comment=comment,
            extra_data=extra_data,
        )
        session.add(log)
        await session.flush()
        return log


news_admin_service = NewsAdminService()
