"""内容质量评分体系服务

提供用户投票和 AI 评估功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class UserVotingSystem:
    """用户投票系统"""

    def __init__(self):
        self._votes: dict[str, dict[str, int]] = {}

    def vote(
        self,
        content_id: str,
        user_id: int,
        vote_type: str,
    ) -> dict[str, Any]:
        """投票

        Args:
            content_id: 内容ID
            user_id: 用户ID
            vote_type: 投票类型 (up/down)

        Returns:
            投票结果
        """
        if content_id not in self._votes:
            self._votes[content_id] = {"up": 0, "down": 0, "voters": {}}

        if user_id in self._votes[content_id]["voters"]:
            old_vote = self._votes[content_id]["voters"][user_id]
            self._votes[content_id][old_vote] -= 1

        self._votes[content_id]["voters"][user_id] = vote_type
        self._votes[content_id][vote_type] += 1

        return {
            "content_id": content_id,
            "vote_type": vote_type,
            "total_up": self._votes[content_id]["up"],
            "total_down": self._votes[content_id]["down"],
        }

    def get_vote_stats(self, content_id: str) -> dict[str, Any]:
        """获取投票统计

        Args:
            content_id: 内容ID

        Returns:
            投票统计
        """
        if content_id not in self._votes:
            return {"up": 0, "down": 0, "score": 0}

        votes = self._votes[content_id]
        score = votes["up"] - votes["down"]

        return {
            "up": votes["up"],
            "down": votes["down"],
            "score": score,
        }


class AIQualityEvaluator:
    """AI 质量评估器"""

    def __init__(self):
        self._evaluations: dict[str, dict[str, Any]] = {}

    def evaluate_content(
        self,
        content_id: str,
        content_text: str,
        category: str,
    ) -> dict[str, Any]:
        """评估内容质量

        Args:
            content_id: 内容ID
            content_text: 内容文本
            category: 分类

        Returns:
            评估结果
        """
        text_length = len(content_text)
        word_count = len(content_text.split())

        score_factors = {
            "length_score": min(
                text_length / 1000,
                1.0) * 20 if text_length > 0 else 0,
            "completeness_score": 25 if text_length > 100 else max(
                0,
                text_length / 4),
            "clarity_score": 25,
            "relevance_score": 30,
        }

        total_score = sum(score_factors.values())

        quality_level = "excellent" if total_score >= 90 else "good" if total_score >= 70 else "average" if total_score >= 50 else "poor"

        self._evaluations[content_id] = {
            "content_id": content_id,
            "total_score": round(total_score, 2),
            "quality_level": quality_level,
            "factors": score_factors,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "content_id": content_id,
            "total_score": round(total_score, 2),
            "quality_level": quality_level,
        }

    def get_evaluation(self, content_id: str) -> dict[str, Any]:
        """获取评估结果

        Args:
            content_id: 内容ID

        Returns:
            评估结果
        """
        if content_id not in self._evaluations:
            return {"content_id": content_id,
                    "total_score": 0, "quality_level": "unknown"}

        return self._evaluations[content_id]


class ContentQualityScoringService:
    """内容质量评分服务"""

    def __init__(self):
        self.voting_system = UserVotingSystem()
        self.ai_evaluator = AIQualityEvaluator()

    async def rate_content(
        self,
        content_id: str,
        user_id: int,
        content_text: str,
        category: str,
        vote_type: str | None = None,
    ) -> dict[str, Any]:
        """评价内容

        Args:
            content_id: 内容ID
            user_id: 用户ID
            content_text: 内容文本
            category: 分类
            vote_type: 投票类型

        Returns:
            评价结果
        """
        vote_result = None
        if vote_type:
            vote_result = self.voting_system.vote(
                content_id, user_id, vote_type)

        ai_result = self.ai_evaluator.evaluate_content(
            content_id, content_text, category)

        vote_stats = self.voting_system.get_vote_stats(content_id)

        combined_score = ai_result["total_score"] * \
            0.7 + (vote_stats["score"] + 100) * 0.3

        return {
            "content_id": content_id,
            "ai_score": ai_result["total_score"],
            "ai_level": ai_result["quality_level"],
            "vote_stats": vote_stats,
            "combined_score": round(combined_score, 2),
        }

    async def get_quality_score(self, content_id: str) -> dict[str, Any]:
        """获取质量评分

        Args:
            content_id: 内容ID

        Returns:
            评分数据
        """
        vote_stats = self.voting_system.get_vote_stats(content_id)
        ai_result = self.ai_evaluator.get_evaluation(content_id)

        return {
            "content_id": content_id,
            "vote_score": vote_stats["score"],
            "ai_score": ai_result.get("total_score", 0),
            "quality_level": ai_result.get("quality_level", "unknown"),
        }

    async def get_top_rated_content(
        self,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """获取高评分内容

        Args:
            category: 分类
            limit: 限制数量

        Returns:
            高评分内容列表
        """
        results = []

        for content_id in self.ai_evaluator._evaluations:
            if category:
                eval_result = self.ai_evaluator._evaluations[content_id]
                if eval_result.get("category") != category:
                    continue

            vote_stats = self.voting_system.get_vote_stats(content_id)
            ai_result = self.ai_evaluator.get_evaluation(content_id)

            combined_score = ai_result.get(
                "total_score", 0) * 0.7 + (vote_stats["score"] + 100) * 0.3

            results.append({
                "content_id": content_id,
                "combined_score": round(combined_score, 2),
                "ai_score": ai_result.get("total_score", 0),
                "vote_score": vote_stats["score"],
            })

        results.sort(key=lambda x: x["combined_score"], reverse=True)

        return results[:limit]

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计数据
        """
        total_content = len(self.ai_evaluator._evaluations)
        excellent = sum(1 for e in self.ai_evaluator._evaluations.values() if e.get(
            "quality_level") == "excellent")
        good = sum(1 for e in self.ai_evaluator._evaluations.values()
                   if e.get("quality_level") == "good")
        average = sum(1 for e in self.ai_evaluator._evaluations.values()
                      if e.get("quality_level") == "average")
        poor = sum(1 for e in self.ai_evaluator._evaluations.values()
                   if e.get("quality_level") == "poor")

        return {
            "total_content": total_content,
            "quality_distribution": {
                "excellent": excellent,
                "good": good,
                "average": average,
                "poor": poor,
            },
            "total_votes": sum(
                v["up"] +
                v["down"] for v in self.voting_system._votes.values()),
        }


# 单例实例
content_quality_service = ContentQualityScoringService()


async def rate_content(
    content_id: str,
    user_id: int,
    content_text: str,
    category: str,
    vote_type: str | None = None,
) -> dict[str, Any]:
    """便捷函数：评价内容

    Args:
        content_id: 内容ID
        user_id: 用户ID
        content_text: 内容文本
        category: 分类
        vote_type: 投票类型

    Returns:
        评价结果
    """
    return await content_quality_service.rate_content(
        content_id=content_id,
        user_id=user_id,
        content_text=content_text,
        category=category,
        vote_type=vote_type,
    )


async def get_quality_score(content_id: str) -> dict[str, Any]:
    """便捷函数：获取质量评分

    Args:
        content_id: 内容ID

    Returns:
        评分数据
    """
    return await content_quality_service.get_quality_score(content_id)
