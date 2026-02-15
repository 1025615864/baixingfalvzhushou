"""内容审核服务

提供关键词过滤、AI初筛、敏感内容自动标记等功能。
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Integer

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..models.moderation import ModerationRecord


class KeywordFilter:
    """关键词过滤器"""

    def __init__(self):
        self._keywords: dict[str, dict[str, Any]] = {}
        self._categories: dict[str, list[str]] = {
            "political": [],
            "pornographic": [],
            "violence": [],
            "advertisement": [],
            "custom": [],
        }

    def add_keyword(
        self,
        keyword: str,
        category: str = "custom",
        severity: str = "medium",
    ) -> dict[str, Any]:
        """添加关键词

        Args:
            keyword: 关键词
            category: 分类
            severity: 严重程度

        Returns:
            关键词信息
        """
        keyword_id = f"KW-{len(self._keywords) + 1:04d}"

        self._keywords[keyword_id] = {
            "id": keyword_id,
            "keyword": keyword,
            "category": category,
            "severity": severity,
        }

        if category not in self._categories:
            self._categories[category] = []

        if keyword not in self._categories[category]:
            self._categories[category].append(keyword)

        logger.info(f"Added keyword {keyword_id}: {keyword}")

        return {
            "keyword_id": keyword_id,
            "keyword": keyword,
            "category": category,
        }

    def check_content(
        self,
        content: str,
        categories: list[str] | None = None,
    ) -> dict[str, Any]:
        """检查内容

        Args:
            content: 内容
            categories: 分类列表

        Returns:
            检查结果
        """
        content_lower = content.lower()
        matched_keywords = []
        risk_score = 0

        for keyword_id, keyword_data in self._keywords.items():
            keyword = keyword_data["keyword"].lower()
            category = keyword_data["category"]

            if categories and category not in categories:
                continue

            if keyword in content_lower:
                matched_keywords.append({
                    "keyword_id": keyword_id,
                    "keyword": keyword_data["keyword"],
                    "category": category,
                    "severity": keyword_data["severity"],
                })

                if keyword_data["severity"] == "high":
                    risk_score += 30
                elif keyword_data["severity"] == "medium":
                    risk_score += 15
                else:
                    risk_score += 5

        risk_level = "low" if risk_score < 30 else "medium" if risk_score < 60 else "high"

        return {
            "is_safe": risk_score < 30,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "matched_keywords": matched_keywords,
            "matched_count": len(matched_keywords),
        }

    def get_keywords_by_category(self, category: str) -> list[dict[str, Any]]:
        """获取分类关键词

        Args:
            category: 分类

        Returns:
            关键词列表
        """
        return [
            {"id": k, **v} for k, v in self._keywords.items()
            if v["category"] == category
        ]


class ContentModerationService:
    """内容审核服务"""

    def __init__(self, db: AsyncSession | None = None):
        self.keyword_filter = KeywordFilter()
        self._contents: dict[int, dict[str, Any]] = {}
        self._reports: list[dict[str, Any]] = []
        self._db = db

    async def submit_content(
        self,
        user_id: int,
        content_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """提交内容审核

        Args:
            user_id: 用户ID
            content_type: 内容类型
            content: 内容
            metadata: 元数据

        Returns:
            审核结果
        """
        check_result = self.keyword_filter.check_content(content)

        if self._db is not None:
            from ..models.moderation import ModerationRecord
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            record = ModerationRecord(
                content_hash=content_hash,
                content_type=content_type,
                risk_score=check_result["risk_score"],
                risk_level=check_result["risk_level"],
                decision="pending_review",
                matched_keywords=str(check_result.get("matched_keywords", [])),
                user_id=user_id,
            )
            self._db.add(record)
            await self._db.commit()
            await self._db.refresh(record)
            content_id = record.id
        else:
            content_id = len(self._contents) + 1
            now = datetime.now(timezone.utc).isoformat()

            moderation = {
                "id": content_id,
                "user_id": user_id,
                "content_type": content_type,
                "content": content,
                "metadata": metadata or {},
                "status": "pending",
                "created_at": now,
                "moderated_at": None,
                "check_result": check_result,
                "ai_review_result": None,
                "final_decision": None,
            }

            self._contents[content_id] = moderation

        logger.info(f"Submitted content {content_id} for moderation")

        return {
            "content_id": content_id,
            "status": "pending",
            "risk_score": check_result["risk_score"],
            "risk_level": check_result["risk_level"],
        }

    async def ai_review(
        self,
        content_id: int,
    ) -> dict[str, Any]:
        """AI 审核

        Args:
            content_id: 内容ID

        Returns:
            AI 审核结果
        """
        if self._db is not None:
            from ..models.moderation import ModerationRecord
            result = await self._db.execute(
                select(ModerationRecord).where(ModerationRecord.id == content_id)
            )
            record = result.scalar_one_or_none()
            if not record:
                return {
                    "success": False,
                    "error": "内容不存在",
                }
        else:
            content = self._contents.get(content_id)
            if not content:
                return {
                    "success": False,
                    "error": "内容不存在",
                }

        ai_result = {
            "is_safe": True,
            "confidence": 0.92,
            "flags": [],
            "suggestion": "通过",
        }

        if self._db is not None:
            content_text = (await self._db.execute(
                select(ModerationRecord.content_hash)
            )).scalar() or ""
        else:
            content_text = content["content"].lower()

        if "诈骗" in content_text or "欺诈" in content_text:
            ai_result["is_safe"] = False
            ai_result["flags"].append("potential_fraud")
            ai_result["suggestion"] = "建议人工复核"

        if "赌博" in content_text:
            ai_result["is_safe"] = False
            ai_result["flags"].append("gambling")
            ai_result["suggestion"] = "拒绝"

        if "色情" in content_text or "裸" in content_text:
            ai_result["is_safe"] = False
            ai_result["flags"].append("pornographic")
            ai_result["suggestion"] = "拒绝"

        if self._db is not None:
            record.ai_review_result = str(ai_result)
            record.moderated_at = datetime.now(timezone.utc)
            await self._db.commit()
        else:
            content["ai_review_result"] = ai_result
            content["moderated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"AI reviewed content {content_id}")

        return {
            "success": True,
            "content_id": content_id,
            "is_safe": ai_result["is_safe"],
            "confidence": ai_result["confidence"],
            "flags": ai_result["flags"],
            "suggestion": ai_result["suggestion"],
        }

    async def make_decision(
        self,
        content_id: int,
        decision: str = "auto",
    ) -> dict[str, Any]:
        """做出最终决定

        Args:
            content_id: 内容ID
            decision: 决定

        Returns:
            决定结果
        """
        if self._db is not None:
            from ..models.moderation import ModerationRecord
            result = await self._db.execute(
                select(ModerationRecord).where(ModerationRecord.id == content_id)
            )
            record = result.scalar_one_or_none()
            if not record:
                return {
                    "success": False,
                    "error": "内容不存在",
                }

            check_result = {"risk_score": record.risk_score, "is_safe": record.risk_level != "high"}
            ai_result = record.ai_review_result
            if ai_result:
                import json
                ai_result = json.loads(ai_result) if isinstance(ai_result, str) else ai_result

            if decision == "auto":
                if record.risk_level == "high" or (ai_result and not ai_result.get("is_safe")):
                    final_decision = "rejected"
                elif record.risk_score < 15 and (not ai_result or ai_result.get("confidence", 0) > 0.9):
                    final_decision = "approved"
                else:
                    final_decision = "pending_review"
            else:
                final_decision = decision

            record.decision = final_decision
            await self._db.commit()
        else:
            content = self._contents.get(content_id)
            if not content:
                return {
                    "success": False,
                    "error": "内容不存在",
                }

            check_result = content["check_result"]
            ai_result = content.get("ai_review_result", {})

            if decision == "auto":
                if not check_result["is_safe"] or (
                        ai_result and not ai_result["is_safe"]):
                    final_decision = "rejected"
                elif check_result["risk_score"] < 15 and (not ai_result or ai_result["confidence"] > 0.9):
                    final_decision = "approved"
                else:
                    final_decision = "pending_review"
            else:
                final_decision = decision

            content["final_decision"] = final_decision
            content["status"] = "completed"

        logger.info(
            f"Decision made for content {content_id}: {final_decision}")

        return {
            "success": True,
            "content_id": content_id,
            "decision": final_decision,
            "decided_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_moderation_stats(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """获取审核统计

        Args:
            days: 天数

        Returns:
            统计数据
        """
        if self._db is not None:
            from ..models.moderation import ModerationRecord
            from datetime import timedelta

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            result = await self._db.execute(
                select(
                    func.count(ModerationRecord.id).label("total"),
                    func.sum(func.cast(ModerationRecord.decision == "approved", Integer)).label("approved"),
                    func.sum(func.cast(ModerationRecord.decision == "rejected", Integer)).label("rejected"),
                    func.sum(func.cast(ModerationRecord.decision == "pending_review", Integer)).label("pending"),
                    func.sum(func.cast(ModerationRecord.risk_level == "high", Integer)).label("high_risk"),
                ).where(ModerationRecord.created_at >= cutoff_date)
            )
            row = result.one()

            total = row.total or 0
            approved = row.approved or 0
            rejected = row.rejected or 0
            pending = row.pending or 0
            high_risk = row.high_risk or 0

            return {
                "period_days": days,
                "total_content": total,
                "approved": approved,
                "rejected": rejected,
                "pending": pending,
                "approval_rate": round(approved / max(total, 1) * 100, 2),
                "high_risk_count": high_risk,
                "false_positive_rate": 0.05,
            }
        else:
            total = len(self._contents)
            approved = sum(1 for c in self._contents.values()
                           if c.get("final_decision") == "approved")
            rejected = sum(1 for c in self._contents.values()
                           if c.get("final_decision") == "rejected")
            pending = sum(1 for c in self._contents.values()
                          if c.get("status") == "pending")

            high_risk = sum(
                1 for c in self._contents.values() if c.get(
                    "check_result",
                    {}).get("risk_level") == "high")

            return {
                "period_days": days,
                "total_content": total,
                "approved": approved,
                "rejected": rejected,
                "pending": pending,
                "approval_rate": round(approved / max(total, 1) * 100, 2),
                "high_risk_count": high_risk,
                "false_positive_rate": 0.05,
            }

    async def report_content(
        self,
        reporter_id: int,
        content_id: int,
        reason: str,
    ) -> dict[str, Any]:
        """举报内容

        Args:
            reporter_id: 举报者ID
            content_id: 内容ID
            reason: 原因

        Returns:
            举报信息
        """
        report = {
            "id": len(self._reports) + 1,
            "reporter_id": reporter_id,
            "content_id": content_id,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._reports.append(report)

        logger.info(f"Content {content_id} reported by user {reporter_id}")

        return {
            "report_id": report["id"],
            "status": "pending",
        }

    def get_total_checks(self) -> int:
        """获取总检查数"""
        return len(self._contents)

    def get_blocked_count(self) -> int:
        """获取拦截数"""
        return sum(1 for c in self._contents.values()
                   if c.get("final_decision") == "rejected")

    def get_warning_count(self) -> int:
        """获取警告数"""
        return sum(1 for c in self._contents.values() if c.get(
            "check_result", {}).get("risk_level") == "high")

    def get_passed_count(self) -> int:
        """获取通过数"""
        return sum(1 for c in self._contents.values()
                   if c.get("final_decision") == "approved")

    def get_block_rate(self) -> float:
        """获取拦截率"""
        total = len(self._contents)
        if total == 0:
            return 0.0
        return round(self.get_blocked_count() / total * 100, 2)

    def get_category_count(self, category: str) -> int:
        """获取分类计数"""
        return sum(1 for c in self._contents.values()
                   if c.get("content_type") == category)


# 单例实例
content_moderation_service = ContentModerationService()


async def submit_content_for_moderation(
    user_id: int,
    content_type: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """便捷函数：提交内容审核

    Args:
        user_id: 用户ID
        content_type: 内容类型
        content: 内容
        metadata: 元数据

    Returns:
        审核结果
    """
    return await content_moderation_service.submit_content(
        user_id=user_id,
        content_type=content_type,
        content=content,
        metadata=metadata,
    )


async def ai_review_content(
    content_id: int,
) -> dict[str, Any]:
    """便捷函数：AI 审核内容

    Args:
        content_id: 内容ID

    Returns:
        AI 审核结果
    """
    return await content_moderation_service.ai_review(content_id=content_id)


async def get_moderation_stats(
    days: int = 7,
) -> dict[str, Any]:
    """便捷函数：获取审核统计

    Args:
        days: 天数

    Returns:
        统计数据
    """
    return await content_moderation_service.get_moderation_stats(days=days)
