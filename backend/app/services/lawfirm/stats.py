"""Lawyer statistics services - 律师统计数据服务"""
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, case, text

from app.models.lawfirm import Lawyer, LawyerReview, LawyerConsultation
from app.models.settlement import LawyerWallet, WithdrawalRequest, LawyerIncomeRecord


class LawyerStatsService:
    """律师统计数据服务"""

    @staticmethod
    async def get_dashboard(
        db: AsyncSession,
        lawyer_id: int
    ) -> dict:
        """获取律师工作台数据"""
        # 获取咨询统计
        consultation_result = await db.execute(
            select(
                func.count(LawyerConsultation.id).label("total"),
                func.sum(
                    case(
                        (LawyerConsultation.status == "completed", 1),
                        else_=0
                    )
                ).label("completed"),
                func.sum(
                    case(
                        (LawyerConsultation.status == "in_progress", 1),
                        else_=0
                    )
                ).label("in_progress")
            ).where(LawyerConsultation.lawyer_id == lawyer_id)
        )
        cons_row = consultation_result.one()

        # 获取收入统计
        income_result = await db.execute(
            select(
                func.sum(LawyerIncomeRecord.lawyer_income).label(
                    "total_income"),
                func.count(LawyerIncomeRecord.id).label("transaction_count")
            ).where(
                LawyerIncomeRecord.lawyer_id == lawyer_id,
                LawyerIncomeRecord.status == "settled"
            )
        )
        income_row = income_result.one()

        # 获取评价统计
        review_result = await db.execute(
            select(
                func.avg(LawyerReview.rating).label("avg_rating"),
                func.count(LawyerReview.id).label("review_count")
            ).where(LawyerReview.lawyer_id == lawyer_id)
        )
        review_row = review_result.one()

        return {
            "consultations": {
                "total": cons_row.total or 0,
                "completed": cons_row.completed or 0,
                "in_progress": cons_row.in_progress or 0},
            "income": {
                "total": float(
                    income_row.total_income or 0),
                "transaction_count": income_row.transaction_count or 0},
            "reviews": {
                "average_rating": round(
                    float(
                        review_row.avg_rating or 0),
                    1) if review_row.avg_rating else None,
                "count": review_row.review_count or 0}}

    @staticmethod
    async def get_income_trend(
        db: AsyncSession,
        lawyer_id: int,
        days: int = 30
    ) -> list[dict]:
        """获取收入趋势"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = await db.execute(
            text("""
                SELECT
                    DATE(created_at) as date,
                    SUM(amount) as daily_income
                FROM lawyer_income_records
                WHERE lawyer_id = :lawyer_id
                    AND created_at >= :start_date
                    AND type = 'consultation_income'
                GROUP BY DATE(created_at)
                ORDER BY date ASC
            """),
            {"lawyer_id": lawyer_id, "start_date": start_date}
        )

        rows = result.all()
        return [
            {"date": row.date.isoformat() if hasattr(row.date, 'isoformat') else str(
                row.date), "income": float(row.daily_income or 0)}
            for row in rows
        ]

    @staticmethod
    async def get_consultation_stats(
        db: AsyncSession,
        lawyer_id: int,
        days: int = 30
    ) -> dict:
        """获取咨询统计数据"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # 按状态统计
        status_result = await db.execute(
            select(
                LawyerConsultation.status,
                func.count(LawyerConsultation.id).label("count")
            ).where(
                LawyerConsultation.lawyer_id == lawyer_id,
                LawyerConsultation.created_at >= start_date
            ).group_by(LawyerConsultation.status)
        )

        status_stats = {row.status: row.count for row in status_result.all()}

        # 平均完成时间
        completed_result = await db.execute(
            select(
                func.avg(
                    func.timestampdiff(
                        text("MINUTE"),
                        LawyerConsultation.created_at,
                        LawyerConsultation.completed_at
                    )
                ).label("avg_duration")
            ).where(
                LawyerConsultation.lawyer_id == lawyer_id,
                LawyerConsultation.status == "completed",
                LawyerConsultation.completed_at.isnot(None)
            )
        )
        avg_duration = completed_result.one().avg_duration

        return {
            "by_status": status_stats,
            "average_duration_minutes": round(
                float(
                    avg_duration or 0),
                1) if avg_duration else None}

    @staticmethod
    async def get_lawyer_performance(
        db: AsyncSession,
        lawyer_id: int,
        days: int = 30
    ) -> dict[str, Any]:
        """
        获取律师绩效分析

        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            days: 查询天数

        Returns:
            律师绩效数据
        """
        from app.models.lawfirm import Lawyer, LawyerReview, LawyerConsultation
        from app.models.settlement import LawyerIncomeRecord
        from sqlalchemy import select, func, desc, and_
        from datetime import timedelta

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # 咨询统计
        total_result = await db.execute(
            select(func.count(LawyerConsultation.id)).where(
                and_(
                    LawyerConsultation.lawyer_id == lawyer_id,
                    LawyerConsultation.created_at >= start_date,
                )
            )
        )
        total = int(total_result.scalar() or 0)

        completed_result = await db.execute(
            select(func.count(LawyerConsultation.id)).where(
                and_(
                    LawyerConsultation.lawyer_id == lawyer_id,
                    LawyerConsultation.created_at >= start_date,
                    LawyerConsultation.status == "completed"
                )
            )
        )
        completed = int(completed_result.scalar() or 0)

        cancelled_result = await db.execute(
            select(func.count(LawyerConsultation.id)).where(
                and_(
                    LawyerConsultation.lawyer_id == lawyer_id,
                    LawyerConsultation.created_at >= start_date,
                    LawyerConsultation.status == "cancelled"
                )
            )
        )
        cancelled = int(cancelled_result.scalar() or 0)

        # 收入统计
        income_result = await db.execute(
            select(func.sum(LawyerIncomeRecord.lawyer_income)).where(
                and_(
                    LawyerIncomeRecord.lawyer_id == lawyer_id,
                    LawyerIncomeRecord.created_at >= start_date,
                )
            )
        )
        total_income = float(income_result.scalar() or 0)

        # 评价统计
        review_count_result = await db.execute(
            select(func.count(LawyerReview.id)).where(
                and_(
                    LawyerReview.lawyer_id == lawyer_id,
                    LawyerReview.created_at >= start_date,
                )
            )
        )
        review_count = int(review_count_result.scalar() or 0)

        avg_rating_result = await db.execute(
            select(func.avg(LawyerReview.rating)).where(
                and_(
                    LawyerReview.lawyer_id == lawyer_id,
                    LawyerReview.created_at >= start_date,
                )
            )
        )
        avg_rating = float(avg_rating_result.scalar() or 0)

        # 响应时间统计
        response_time_result = await db.execute(
            select(
                func.avg(
                    func.extract('epoch', LawyerConsultation.updated_at) -
                    func.extract('epoch', LawyerConsultation.created_at)
                )
            ).where(
                and_(
                    LawyerConsultation.lawyer_id == lawyer_id,
                    LawyerConsultation.created_at >= start_date,
                    LawyerConsultation.status == "confirmed"
                )
            )
        )
        avg_response_seconds = response_time_result.scalar()
        avg_response_minutes = round(
            avg_response_seconds / 60,
            1) if avg_response_seconds else 0.0

        # 每日咨询量
        daily_result = await db.execute(
            select(
                func.date(LawyerConsultation.created_at).label('date'),
                func.count(LawyerConsultation.id).label('count')
            ).where(
                and_(
                    LawyerConsultation.lawyer_id == lawyer_id,
                    LawyerConsultation.created_at >= start_date,
                )
            ).group_by(func.date(LawyerConsultation.created_at))
            .order_by(func.date(LawyerConsultation.created_at))
        )
        daily_data = []
        for row in daily_result.all():
            count_value = row.count if row.count is not None else 0
            daily_data.append({'date': str(row.date), 'count': count_value})

        return {
            'lawyer_id': lawyer_id,
            'period_days': days,
            'consultation': {
                'total': total,
                'completed': completed,
                'cancelled': cancelled,
                'completion_rate': round(
                    completed / total * 100,
                    1) if total > 0 else 0.0,
            },
            'income': {
                'total': round(
                    total_income,
                    2),
                'avg_per_consultation': round(
                    total_income / completed,
                    2) if completed > 0 else 0.0,
            },
            'review': {
                'count': review_count,
                'avg_rating': round(
                    avg_rating,
                    1),
            },
            'response': {
                'avg_response_minutes': avg_response_minutes,
            },
            'daily_consultations': daily_data,
        }

    @staticmethod
    async def get_lawyers_ranking(
        db: AsyncSession,
        metric: str = "income",
        days: int = 30,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        获取律师排行榜

        Args:
            db: 数据库会话
            metric: 排序指标（income/completion/rating）
            days: 查询天数
            limit: 返回数量

        Returns:
            律师排行榜数据
        """
        from app.models.lawfirm import Lawyer, LawyerReview, LawyerConsultation
        from app.models.settlement import LawyerIncomeRecord
        from sqlalchemy import select, func, desc, and_, case
        from datetime import timedelta

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        if metric == "income":
            # 按收入排序
            result = await db.execute(
                select(
                    Lawyer.id,
                    Lawyer.name,
                    Lawyer.rating,
                    func.sum(
                        LawyerIncomeRecord.lawyer_income).label('total_income')
                )
                .join(LawyerIncomeRecord, Lawyer.id == LawyerIncomeRecord.lawyer_id)
                .where(
                    and_(
                        Lawyer.is_active,
                        LawyerIncomeRecord.created_at >= start_date,
                    )
                )
                .group_by(Lawyer.id, Lawyer.name, Lawyer.rating)
                .order_by(desc('total_income'))
                .limit(limit)
            )
            rows = result.all()
            return [
                {
                    'lawyer_id': int(row.id),
                    'lawyer_name': row.name,
                    'rating': float(row.rating),
                    'value': float(row.total_income or 0),
                }
                for row in rows
            ]

        elif metric == "completion":
            # 按完成率排序
            result = await db.execute(
                select(
                    Lawyer.id,
                    Lawyer.name,
                    Lawyer.rating,
                    func.count(LawyerConsultation.id).label('total'),
                    func.sum(
                        case(
                            (LawyerConsultation.status == "completed",
                             1),
                            else_=0)).label('completed')
                )
                .join(LawyerConsultation, Lawyer.id == LawyerConsultation.lawyer_id)
                .where(
                    and_(
                        Lawyer.is_active,
                        LawyerConsultation.created_at >= start_date,
                    )
                )
                .group_by(Lawyer.id, Lawyer.name, Lawyer.rating)
                .having(func.count(LawyerConsultation.id) > 0)
                .order_by(desc('completed' / func.count(LawyerConsultation.id)))
                .limit(limit)
            )
            rows = result.all()
            return [
                {
                    'lawyer_id': int(
                        row.id),
                    'lawyer_name': row.name,
                    'rating': float(
                        row.rating),
                    'value': round(
                        float(
                            row.completed) /
                        float(
                            row.total) *
                        100,
                        1) if row.total > 0 else 0.0,
                } for row in rows]

        elif metric == "rating":
            # 按评分排序
            result = await db.execute(
                select(
                    Lawyer.id,
                    Lawyer.name,
                    Lawyer.rating,
                    func.count(LawyerReview.id).label('review_count')
                )
                .join(LawyerReview, Lawyer.id == LawyerReview.lawyer_id)
                .where(
                    and_(
                        Lawyer.is_active,
                        LawyerReview.created_at >= start_date,
                    )
                )
                .group_by(Lawyer.id, Lawyer.name, Lawyer.rating)
                .having(func.count(LawyerReview.id) >= 3)
                .order_by(desc(Lawyer.rating))
                .limit(limit)
            )
            rows = result.all()
            return [
                {
                    'lawyer_id': int(row.id),
                    'lawyer_name': row.name,
                    'rating': float(row.rating),
                    'value': float(row.rating),
                }
                for row in rows
            ]

        return []
