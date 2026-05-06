"""对话质量评估和Token消耗追踪服务"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.conversation_quality import ConversationQualityRecord
from app.models.token_usage import TokenUsageRecord

logger = logging.getLogger(__name__)

TOKEN_COST_PER_1K_PROMPT = float(os.getenv("TOKEN_COST_PER_1K_PROMPT", "0.001"))
TOKEN_COST_PER_1K_COMPLETION = float(os.getenv("TOKEN_COST_PER_1K_COMPLETION", "0.003"))
USD_TO_CNY_RATE = float(os.getenv("USD_TO_CNY_RATE", "7.2"))


class QualityService:
    """质量评估服务"""

    def __init__(self):
        self.prompt_cost_per_1k = TOKEN_COST_PER_1K_PROMPT
        self.completion_cost_per_1k = TOKEN_COST_PER_1K_COMPLETION
        self.usd_to_cny = USD_TO_CNY_RATE

    async def _get_session(self) -> AsyncSession:
        return AsyncSessionLocal()

    async def record_quality(
        self,
        conversation_id: str,
        query: str,
        response: str,
        quality_score: float,
        user_id: Optional[int] = None,
        feedback: Optional[int] = None,
        issues: Optional[List[str]] = None
    ) -> int:
        """记录质量评分"""
        async with await self._get_session() as session:
            record = ConversationQualityRecord(
                conversation_id=conversation_id,
                user_id=user_id,
                query=query,
                response=response,
                quality_score=quality_score,
                feedback=feedback,
                issues=issues or []
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record.id

    async def record_token_usage(
        self,
        conversation_id: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        total_tokens: Optional[int] = None
    ) -> int:
        """记录Token消耗"""
        if total_tokens is None:
            total_tokens = prompt_tokens + completion_tokens

        cost_usd = self._calculate_cost(prompt_tokens, completion_tokens)
        cost_cny = cost_usd * self.usd_to_cny

        async with await self._get_session() as session:
            record = TokenUsageRecord(
                conversation_id=conversation_id,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                cost_cny=cost_cny,
                latency_ms=latency_ms
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record.id

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """计算Token成本(USD)"""
        prompt_cost = (prompt_tokens / 1000) * self.prompt_cost_per_1k
        completion_cost = (completion_tokens / 1000) * self.completion_cost_per_1k
        return round(prompt_cost + completion_cost, 6)

    async def get_quality_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "7d"
    ) -> Dict[str, Any]:
        """生成质量报告"""
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            if period == "1d":
                start_date = end_date - timedelta(days=1)
            elif period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)

        async with await self._get_session() as session:
            query = select(
                func.count(ConversationQualityRecord.id).label("total_queries"),
                func.avg(ConversationQualityRecord.quality_score).label("avg_quality_score"),
                func.count(
                    func.nullif(ConversationQualityRecord.feedback, 1)
                ).label("negative_feedback") if False else None,
            ).where(
                and_(
                    ConversationQualityRecord.created_at >= start_date,
                    ConversationQualityRecord.created_at <= end_date
                )
            )

            result = await session.execute(query)
            row = result.first()

            total_queries = row.total_queries if row and row.total_queries else 0
            avg_quality_score = round(row.avg_quality_score, 3) if row and row.avg_quality_score else 0.0

            feedback_query = select(
                func.count(ConversationQualityRecord.id)
            ).where(
                and_(
                    ConversationQualityRecord.created_at >= start_date,
                    ConversationQualityRecord.created_at <= end_date,
                    ConversationQualityRecord.feedback == 1
                )
            )
            feedback_result = await session.execute(feedback_query)
            positive_feedback = feedback_result.scalar() or 0

            issues_query = select(
                ConversationQualityRecord.issues
            ).where(
                and_(
                    ConversationQualityRecord.created_at >= start_date,
                    ConversationQualityRecord.created_at <= end_date,
                    ConversationQualityRecord.issues.isnot(None)
                )
            )
            issues_result = await session.execute(issues_query)
            all_issues = {}
            for row in issues_result:
                if row.issues:
                    for issue in row.issues:
                        all_issues[issue] = all_issues.get(issue, 0) + 1

            return {
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_queries": total_queries,
                "avg_quality_score": avg_quality_score,
                "positive_feedback": positive_feedback,
                "negative_feedback": 0,
                "top_issues": sorted(all_issues.items(), key=lambda x: x[1], reverse=True)[:10] if all_issues else []
            }

    async def get_token_usage_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "7d"
    ) -> Dict[str, Any]:
        """获取Token消耗报告"""
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            if period == "1d":
                start_date = end_date - timedelta(days=1)
            elif period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)

        async with await self._get_session() as session:
            query = select(
                func.count(TokenUsageRecord.id).label("total_requests"),
                func.sum(TokenUsageRecord.prompt_tokens).label("total_prompt_tokens"),
                func.sum(TokenUsageRecord.completion_tokens).label("total_completion_tokens"),
                func.sum(TokenUsageRecord.total_tokens).label("total_tokens"),
                func.avg(TokenUsageRecord.latency_ms).label("avg_latency_ms")
            ).where(
                and_(
                    TokenUsageRecord.created_at >= start_date,
                    TokenUsageRecord.created_at <= end_date
                )
            )

            result = await session.execute(query)
            row = result.first()

            model_query = select(
                TokenUsageRecord.model_name,
                func.sum(TokenUsageRecord.total_tokens).label("tokens")
            ).where(
                and_(
                    TokenUsageRecord.created_at >= start_date,
                    TokenUsageRecord.created_at <= end_date
                )
            ).group_by(TokenUsageRecord.model_name)

            model_result = await session.execute(model_query)
            model_stats = [
                {"model": row.model_name, "tokens": row.tokens}
                for row in model_result
            ]

            return {
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_requests": row.total_requests if row and row.total_requests else 0,
                "total_prompt_tokens": row.total_prompt_tokens if row and row.total_prompt_tokens else 0,
                "total_completion_tokens": row.total_completion_tokens if row and row.total_completion_tokens else 0,
                "total_tokens": row.total_tokens if row and row.total_tokens else 0,
                "avg_latency_ms": round(row.avg_latency_ms, 2) if row and row.avg_latency_ms else 0.0,
                "by_model": model_stats
            }

    async def get_cost_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "7d"
    ) -> Dict[str, Any]:
        """获取成本统计"""
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            if period == "1d":
                start_date = end_date - timedelta(days=1)
            elif period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)

        async with await self._get_session() as session:
            query = select(
                func.sum(TokenUsageRecord.cost_usd).label("total_cost_usd"),
                func.sum(TokenUsageRecord.cost_cny).label("total_cost_cny"),
                func.sum(TokenUsageRecord.total_tokens).label("total_tokens")
            ).where(
                and_(
                    TokenUsageRecord.created_at >= start_date,
                    TokenUsageRecord.created_at <= end_date
                )
            )

            result = await session.execute(query)
            row = result.first()

            return {
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_cost_usd": round(row.total_cost_usd, 4) if row and row.total_cost_usd else 0.0,
                "total_cost_cny": round(row.total_cost_cny, 4) if row and row.total_cost_cny else 0.0,
                "total_tokens": row.total_tokens if row and row.total_tokens else 0,
                "pricing": {
                    "prompt_cost_per_1k": self.prompt_cost_per_1k,
                    "completion_cost_per_1k": self.completion_cost_per_1k,
                    "usd_to_cny_rate": self.usd_to_cny
                }
            }


_quality_service: Optional[QualityService] = None


def get_quality_service() -> QualityService:
    global _quality_service
    if _quality_service is None:
        _quality_service = QualityService()
    return _quality_service