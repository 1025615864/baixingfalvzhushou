"""律师匹配服务增强版

根据关键词和领域匹配律师专长，并进行综合评分优化
目标：提升推荐准确率到>80%
"""
import logging
import hashlib
import json
import math
from typing import Any, Optional
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lawfirm import Lawyer, LawyerConsultation
from .keyword_extraction_service import get_keyword_extraction_service
from .redis_service import get_redis_service

logger = logging.getLogger(__name__)


@dataclass
class LawyerMatchResultEnhanced:
    """律师匹配结果增强版"""
    lawyer_id: int
    lawyer_name: str
    specialties: str
    rating: float
    completed_count: int
    match_score: float  # 专长匹配分数
    response_time_score: float  # 响应速度分数
    case_similarity_score: float  # 案例相似度分数
    overall_score: float  # 综合分数
    match_reasons: list[str]
    is_cold_start: bool  # 是否为冷启动律师
    experiment_group: Optional[str] = None  # AB测试分组


class LawyerMatchingServiceEnhanced:
    """律师匹配服务增强版"""

    # 评分权重配置
    WEIGHT_PROFESSION_MATCH = 0.4  # 专业领域匹配度 40%
    WEIGHT_USER_RATING = 0.3  # 用户评价 30%
    WEIGHT_RESPONSE_TIME = 0.2  # 响应速度 20%
    WEIGHT_CASE_SIMILARITY = 0.1  # 案例相似度 10%

    # 冷启动基础分
    COLD_START_BASE_SCORE = 65.0

    def __init__(self):
        """初始化律师匹配服务"""
        self.keyword_service = get_keyword_extraction_service()
        self.redis_service = get_redis_service()

    async def match_lawyers_by_keywords(
        self,
        db: AsyncSession,
        keywords: list[str],
        domains: list[str],
        limit: int = 10,
        experiment_id: Optional[str] = None,
    ) -> list[LawyerMatchResultEnhanced]:
        """
        根据关键词和领域匹配律师（增强版）

        Args:
            db: 数据库会话
            keywords: 关键词列表
            domains: 法律领域列表
            limit: 返回结果数量
            experiment_id: AB测试ID

        Returns:
            律师匹配结果列表
        """
        if not keywords and not domains:
            return []

        # 尝试从缓存获取
        cache_key = self._generate_cache_key(keywords, domains, limit, experiment_id)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"从缓存获取律师推荐: {cache_key}")
            return cached_result

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
                db, lawyer, keywords, domains, experiment_id
            )
            if match_result.match_score > 0 or match_result.is_cold_start:
                match_results.append(match_result)

        # 按综合分数排序
        match_results = self._sort_lawyers_by_score(match_results)

        # 限制返回数量
        final_results = match_results[:limit]

        # 写入缓存（5分钟）
        await self._save_to_cache(cache_key, final_results)

        return final_results

    async def _calculate_lawyer_match(
        self,
        db: AsyncSession,
        lawyer: Lawyer,
        keywords: list[str],
        domains: list[str],
        experiment_id: Optional[str] = None,
    ) -> LawyerMatchResultEnhanced:
        """
        计算律师匹配分数（增强版）

        Args:
            db: 数据库会话
            lawyer: 律师对象
            keywords: 关键词列表
            domains: 法律领域列表
            experiment_id: AB测试ID

        Returns:
            律师匹配结果
        """
        # 获取律师专长
        specialties = str(lawyer.specialties or "").strip()
        if not specialties:
            specialties = ""

        # 计算专业领域匹配分数（40%）
        profession_match = self._calculate_profession_match(
            specialties, keywords, domains
        )
        profession_score = profession_match * 100

        # 获取律师评分（30%）
        rating = float(lawyer.rating or 0.0)
        rating_score = rating * 20  # 5星=100分

        # 获取律师完成咨询数量
        completed_result = await db.execute(
            select(func.count(LawyerConsultation.id)).where(
                LawyerConsultation.lawyer_id == lawyer.id,
                LawyerConsultation.status == "completed",
            )
        )
        completed_count = int(completed_result.scalar() or 0)

        # 计算响应速度分数（20%）
        response_time_score = self._calculate_response_time_score(
            completed_count, lawyer.rating
        )

        # 计算案例相似度分数（10%）
        case_similarity_score = self._calculate_case_similarity(
            specialties, keywords
        )

        # 判断是否为冷启动律师
        is_cold_start = rating == 0.0 and completed_count == 0

        # 计算综合分数
        if is_cold_start:
            # 冷启动处理：给予基础分，专业领域匹配仍然适用
            overall_score = self._calculate_cold_start_score(profession_match)
        else:
            # 正常计算综合分数
            overall_score = (
                profession_score * self.WEIGHT_PROFESSION_MATCH
                + rating_score * self.WEIGHT_USER_RATING
                + response_time_score * self.WEIGHT_RESPONSE_TIME
                + case_similarity_score * self.WEIGHT_CASE_SIMILARITY
            )

        overall_score = min(overall_score, 100.0)

        # 生成匹配原因
        match_reasons = self._generate_match_reasons(
            specialties, keywords, domains, rating, completed_count,
            response_time_score, case_similarity_score, is_cold_start
        )

        return LawyerMatchResultEnhanced(
            lawyer_id=int(lawyer.id),
            lawyer_name=str(lawyer.name or ""),
            specialties=specialties,
            rating=rating,
            completed_count=completed_count,
            match_score=profession_match,  # 0-1
            response_time_score=response_time_score,
            case_similarity_score=case_similarity_score,
            overall_score=round(overall_score, 2),
            match_reasons=match_reasons,
            is_cold_start=is_cold_start,
            experiment_group=experiment_id,
        )

    def _calculate_profession_match(
        self,
        specialties: str,
        keywords: list[str],
        domains: list[str],
    ) -> float:
        """
        计算专业领域匹配度

        Args:
            specialties: 律师专长
            keywords: 关键词列表
            domains: 法律领域列表

        Returns:
            匹配分数 (0-1)
        """
        if not keywords and not domains:
            return 1.0  # 没有要求，返回1.0

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

    def _calculate_response_time_score(
        self,
        completed_count: int,
        rating: float,
    ) -> float:
        """
        计算响应速度评分

        由于数据库中没有直接的响应时间字段，我们使用完成数量和评分来估算
        完成数量多且评分高通常意味着响应速度快

        Args:
            completed_count: 完成咨询数量
            rating: 律师评分

        Returns:
            响应速度分数 (0-100)
        """
        # 使用完成数量和评分的综合指标
        # 完成数量使用对数缩放：0单: 0分, 1单: 20分, 10单: 40分, 100单: 60分, 1000单: 80分
        if completed_count > 0:
            count_score = min(math.log10(completed_count + 1) / 4.0 * 100, 80.0)
        else:
            count_score = 0.0

        # 评分高也意味着响应快：5星=20分，4星=16分，3星=12分，2星=8分，1星=4分
        rating_score = rating * 4

        # 综合评分：完成数量权重70%，评分权重30%
        total_score = count_score * 0.7 + rating_score
        return min(total_score, 100.0)

    def _calculate_case_similarity(
        self,
        specialties: str,
        keywords: list[str],
    ) -> float:
        """
        计算案例相似度

        基于专长和关键词的匹配度来估算案例相似度

        Args:
            specialties: 律师专长
            keywords: 关键词列表

        Returns:
            案例相似度分数 (0-100)
        """
        if not specialties or not keywords:
            return 50.0  # 无数据，给中等分

        specialties_lower = specialties.lower()
        matched_keywords = 0

        for keyword in keywords:
            if keyword.lower() in specialties_lower:
                matched_keywords += 1

        # 每个匹配关键词给10分，最多100分
        similarity_score = matched_keywords * 10
        return min(similarity_score, 100.0)

    def _calculate_cold_start_score(
        self,
        profession_match: float,
    ) -> float:
        """
        计算冷启动律师的综合分数

        新律师由于没有评价和历史，给予基础分65分
        专业领域匹配仍然适用

        Args:
            profession_match: 专业领域匹配度 (0-1)

        Returns:
            综合分数 (0-100)
        """
        # 基础分65分的60% + 专业领域匹配分的40%
        base_score = self.COLD_START_BASE_SCORE * 0.6
        profession_score = profession_match * 100 * 0.4
        return base_score + profession_score

    def _generate_match_reasons(
        self,
        specialties: str,
        keywords: list[str],
        domains: list[str],
        rating: float,
        completed_count: int,
        response_time_score: float,
        case_similarity_score: float,
        is_cold_start: bool,
    ) -> list[str]:
        """
        生成匹配原因

        Args:
            specialties: 律师专长
            keywords: 关键词列表
            domains: 法律领域列表
            rating: 律师评分
            completed_count: 完成咨询数量
            response_time_score: 响应速度分数
            case_similarity_score: 案例相似度分数
            is_cold_start: 是否为冷启动律师

        Returns:
            匹配原因列表
        """
        reasons = []

        specialties_lower = specialties.lower()

        # 冷启动提示
        if is_cold_start:
            reasons.append("新入驻律师，期待您的评价")

        # 专长匹配原因
        matched_keywords = [
            kw for kw in keywords if kw.lower() in specialties_lower
        ]
        if matched_keywords:
            reasons.append(f"专长包含: {', '.join(matched_keywords[:3])}")

        matched_domains = [
            dm for dm in domains if dm.lower() in specialties_lower
        ]
        if matched_domains:
            reasons.append(f"擅长领域: {', '.join(matched_domains[:2])}")

        # 评分原因
        if rating >= 4.5:
            reasons.append(f"高评分律师 ({rating}分)")
        elif rating >= 4.0 and not is_cold_start:
            reasons.append(f"好评律师 ({rating}分)")

        # 经验原因
        if completed_count >= 100:
            reasons.append(f"经验丰富 (已完成{completed_count}单)")
        elif completed_count >= 50:
            reasons.append(f"经验丰富 (已完成{completed_count}单)")
        elif completed_count >= 10 and not is_cold_start:
            reasons.append(f"有经验 (已完成{completed_count}单)")

        # 响应速度原因
        if response_time_score >= 80:
            reasons.append("响应迅速")
        elif response_time_score >= 60 and not is_cold_start:
            reasons.append("响应及时")

        # 案例相似度原因
        if case_similarity_score >= 80:
            reasons.append("案例高度相似")
        elif case_similarity_score >= 60:
            reasons.append("案例较为相似")

        return reasons

    def _sort_lawyers_by_score(
        self,
        lawyer_list: list[LawyerMatchResultEnhanced],
    ) -> list[LawyerMatchResultEnhanced]:
        """
        按评分排序律师列表

        排序逻辑：
        - 主键：综合分数（降序）
        - 次键1：是否冷启动（非冷启动优先）
        - 次键2：平均评价（高评价优先）

        Args:
            lawyer_list: 律师列表

        Returns:
            排序后的律师列表
        """
        def sort_key(lawyer: LawyerMatchResultEnhanced):
            # 主键：综合分数（降序）
            # 次键1：是否冷启动（非冷启动优先，即is_cold_start=False在前）
            # 次键2：平均评价（高评价在前）
            return (
                -lawyer.overall_score,  # 降序
                int(lawyer.is_cold_start),  # False(0)在前，True(1)在后
                -lawyer.rating  # 高评价在前
            )

        return sorted(lawyer_list, key=sort_key)

    def _generate_cache_key(
        self,
        keywords: list[str],
        domains: list[str],
        limit: int,
        experiment_id: Optional[str],
    ) -> str:
        """
        生成缓存键

        Args:
            keywords: 关键词列表
            domains: 法律领域列表
            limit: 返回数量限制
            experiment_id: AB测试ID

        Returns:
            缓存键
        """
        # 创建一个hash来生成唯一的缓存键
        key_data = {
            "keywords": sorted(keywords),
            "domains": sorted(domains),
            "limit": limit,
            "experiment_id": experiment_id,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        hash_value = hashlib.md5(key_str.encode()).hexdigest()
        return f"lawyer_recommendation:{hash_value}"

    async def _get_from_cache(
        self,
        cache_key: str,
    ) -> Optional[list[LawyerMatchResultEnhanced]]:
        """
        从缓存获取推荐结果

        Args:
            cache_key: 缓存键

        Returns:
            缓存的推荐结果，如果不存在则返回None
        """
        try:
            cached_data = await self.redis_service.get(cache_key)
            if cached_data:
                logger.info(f"从Redis缓存获取推荐: {cache_key}")
                data = json.loads(cached_data)
                return [
                    LawyerMatchResultEnhanced(**item)
                    for item in data
                ]
        except Exception as e:
            logger.warning(f"从缓存获取失败: {e}")
        return None

    async def _save_to_cache(
        self,
        cache_key: str,
        results: list[LawyerMatchResultEnhanced],
    ) -> None:
        """
        保存推荐结果到缓存

        Args:
            cache_key: 缓存键
            results: 推荐结果列表
        """
        try:
            data = [item.__dict__ for item in results]
            cached_data = json.dumps(data, ensure_ascii=False)
            # 缓存5分钟（300秒）
            await self.redis_service.set(cache_key, cached_data, ttl=300)
            logger.info(f"推荐结果已缓存: {cache_key}")
        except Exception as e:
            logger.warning(f"保存到缓存失败: {e}")

    async def recommend_lawyers(
        self,
        db: AsyncSession,
        query_text: str,
        limit: int = 10,
        experiment_id: Optional[str] = None,
    ) -> list[LawyerMatchResultEnhanced]:
        """
        根据查询文本推荐律师（增强版）

        Args:
            db: 数据库会话
            query_text: 查询文本
            limit: 返回结果数量
            experiment_id: AB测试ID

        Returns:
            律师推荐结果列表
        """
        # 提取关键词和领域
        extraction_result = self.keyword_service.extract_with_confidence(
            query_text
        )
        keywords = extraction_result.get("keywords", [])
        domains = extraction_result.get("domains", [])

        # 匹配律师
        return await self.match_lawyers_by_keywords(
            db, keywords, domains, limit=limit, experiment_id=experiment_id
        )


# 全局实例
_lawyer_matching_service_enhanced = None


def get_lawyer_matching_service_enhanced() -> LawyerMatchingServiceEnhanced:
    """获取律师匹配服务增强版实例（懒加载）"""
    global _lawyer_matching_service_enhanced
    if _lawyer_matching_service_enhanced is None:
        _lawyer_matching_service_enhanced = LawyerMatchingServiceEnhanced()
    return _lawyer_matching_service_enhanced