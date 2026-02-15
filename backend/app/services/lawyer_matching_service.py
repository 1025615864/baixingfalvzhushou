"""律师匹配服务

根据关键词和领域匹配律师专长，并进行综合评分
"""
import logging
from typing import Any
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lawfirm import Lawyer, LawyerConsultation
from .keyword_extraction_service import get_keyword_extraction_service

logger = logging.getLogger(__name__)


@dataclass
class LawyerMatchResult:
    """律师匹配结果"""
    lawyer_id: int
    lawyer_name: str
    specialties: str
    rating: float
    completed_count: int
    match_score: float
    overall_score: float
    match_reasons: list[str]


class LawyerMatchingService:
    """律师匹配服务"""

    def __init__(self):
        """初始化律师匹配服务"""
        self.keyword_service = get_keyword_extraction_service()

    async def match_lawyers_by_keywords(
        self,
        db: AsyncSession,
        keywords: list[str],
        domains: list[str],
        limit: int = 10,
    ) -> list[LawyerMatchResult]:
        """
        根据关键词和领域匹配律师

        Args:
            db: 数据库会话
            keywords: 关键词列表
            domains: 法律领域列表
            limit: 返回结果数量

        Returns:
            律师匹配结果列表
        """
        if not keywords and not domains:
            return []

        # 查询所有认证且活跃的律师
        result = await db.execute(
            select(Lawyer).where(
                Lawyer.is_verified,
                Lawyer.is_active,
            )
        )
        lawyers = result.scalars().all()

        if not lawyers:
            return []

        # 为每个律师计算匹配分数
        match_results = []
        for lawyer in lawyers:
            match_result = await self._calculate_lawyer_match(
                db, lawyer, keywords, domains
            )
            if match_result.match_score > 0:
                match_results.append(match_result)

        # 按综合分数排序
        match_results.sort(key=lambda x: x.overall_score, reverse=True)

        return match_results[:limit]

    async def _calculate_lawyer_match(
        self,
        db: AsyncSession,
        lawyer: Lawyer,
        keywords: list[str],
        domains: list[str],
    ) -> LawyerMatchResult:
        """
        计算律师匹配分数

        Args:
            db: 数据库会话
            lawyer: 律师对象
            keywords: 关键词列表
            domains: 法律领域列表

        Returns:
            律师匹配结果
        """
        # 获取律师专长
        specialties = str(lawyer.specialties or "").strip()
        if not specialties:
            specialties = ""

        # 计算专长匹配分数
        specialty_score = self._calculate_specialty_match(
            specialties, keywords, domains)

        # 获取律师完成咨询数量
        completed_result = await db.execute(
            select(func.count(LawyerConsultation.id)).where(
                LawyerConsultation.lawyer_id == lawyer.id,
                LawyerConsultation.status == "completed",
            )
        )
        completed_count = int(completed_result.scalar() or 0)

        # 获取律师评分
        rating = float(lawyer.rating or 0.0)

        # 计算综合分数
        overall_score = self._calculate_overall_score(
            specialty_score, rating, completed_count
        )

        # 生成匹配原因
        match_reasons = self._generate_match_reasons(
            specialties, keywords, domains, rating, completed_count
        )

        return LawyerMatchResult(
            lawyer_id=int(lawyer.id),
            lawyer_name=str(lawyer.name or ""),
            specialties=specialties,
            rating=rating,
            completed_count=completed_count,
            match_score=specialty_score,
            overall_score=overall_score,
            match_reasons=match_reasons,
        )

    def _calculate_specialty_match(
        self,
        specialties: str,
        keywords: list[str],
        domains: list[str],
    ) -> float:
        """
        计算专长匹配分数

        Args:
            specialties: 律师专长
            keywords: 关键词列表
            domains: 法律领域列表

        Returns:
            匹配分数 (0-1)
        """
        if not specialties:
            return 0.0

        specialties_lower = specialties.lower()
        score = 0.0

        # 关键词匹配
        keyword_matches = 0
        for keyword in keywords:
            if keyword.lower() in specialties_lower:
                keyword_matches += 1

        if keywords:
            keyword_score = keyword_matches / len(keywords)
            score += keyword_score * 0.6  # 关键词权重60%

        # 领域匹配
        domain_matches = 0
        for domain in domains:
            if domain.lower() in specialties_lower:
                domain_matches += 1

        if domains:
            domain_score = domain_matches / len(domains)
            score += domain_score * 0.4  # 领域权重40%

        return min(score, 1.0)

    def _calculate_overall_score(
        self,
        specialty_score: float,
        rating: float,
        completed_count: int,
    ) -> float:
        """
        计算综合分数

        Args:
            specialty_score: 专长匹配分数
            rating: 律师评分
            completed_count: 完成咨询数量

        Returns:
            综合分数 (0-100)
        """
        # 专长匹配分数权重 50%
        specialty_weight = 0.5

        # 评分权重 30% (评分范围0-5，归一化到0-1)
        rating_score = rating / 5.0 if rating > 0 else 0.0
        rating_weight = 0.3

        # 完成数量权重 20% (使用对数缩放，避免数量差异过大)
        # 0单: 0分, 1单: 0.2分, 10单: 0.4分, 100单: 0.6分, 1000单: 0.8分
        import math
        if completed_count > 0:
            count_score = min(math.log10(completed_count + 1) / 4.0, 1.0)
        else:
            count_score = 0.0
        count_weight = 0.2

        overall_score = (
            specialty_score * specialty_weight +
            rating_score * rating_weight +
            count_score * count_weight
        )

        return round(overall_score * 100, 2)

    def _generate_match_reasons(
        self,
        specialties: str,
        keywords: list[str],
        domains: list[str],
        rating: float,
        completed_count: int,
    ) -> list[str]:
        """
        生成匹配原因

        Args:
            specialties: 律师专长
            keywords: 关键词列表
            domains: 法律领域列表
            rating: 律师评分
            completed_count: 完成咨询数量

        Returns:
            匹配原因列表
        """
        reasons = []

        specialties_lower = specialties.lower()

        # 专长匹配原因
        matched_keywords = [
            kw for kw in keywords if kw.lower() in specialties_lower]
        if matched_keywords:
            reasons.append(f"专长包含: {', '.join(matched_keywords[:3])}")

        matched_domains = [
            dm for dm in domains if dm.lower() in specialties_lower]
        if matched_domains:
            reasons.append(f"擅长领域: {', '.join(matched_domains[:2])}")

        # 评分原因
        if rating >= 4.5:
            reasons.append(f"高评分律师 ({rating}分)")
        elif rating >= 4.0:
            reasons.append(f"好评律师 ({rating}分)")

        # 经验原因
        if completed_count >= 100:
            reasons.append(f"经验丰富 (已完成{completed_count}单)")
        elif completed_count >= 50:
            reasons.append(f"经验丰富 (已完成{completed_count}单)")
        elif completed_count >= 10:
            reasons.append(f"有经验 (已完成{completed_count}单)")

        return reasons

    async def recommend_lawyers(
        self,
        db: AsyncSession,
        query_text: str,
        limit: int = 10,
    ) -> list[LawyerMatchResult]:
        """
        根据查询文本推荐律师

        Args:
            db: 数据库会话
            query_text: 查询文本
            limit: 返回结果数量

        Returns:
            律师推荐结果列表
        """
        # 提取关键词和领域
        extraction_result = self.keyword_service.extract_with_confidence(
            query_text)
        keywords = extraction_result.get("keywords", [])
        domains = extraction_result.get("domains", [])

        # 匹配律师
        return await self.match_lawyers_by_keywords(
            db, keywords, domains, limit=limit
        )


# 全局实例
_lawyer_matching_service = None


def get_lawyer_matching_service() -> LawyerMatchingService:
    """获取律师匹配服务实例（懒加载）"""
    global _lawyer_matching_service
    if _lawyer_matching_service is None:
        _lawyer_matching_service = LawyerMatchingService()
    return _lawyer_matching_service
