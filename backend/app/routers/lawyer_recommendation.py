"""律师推荐API

提供基于AI咨询内容的律师推荐接口
"""
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..utils.deps import get_current_user
from ..services.lawyer_matching_service import (
    LawyerMatchingService,
    LawyerMatchResult,
    get_lawyer_matching_service,
)
from ..services.lawyer_matching_service_enhanced import (
    LawyerMatchingServiceEnhanced,
    LawyerMatchResultEnhanced,
    get_lawyer_matching_service_enhanced,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lawyer-recommendation", tags=["律师推荐"])


@router.get("/recommend", summary="根据查询文本推荐律师")
async def recommend_lawyers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    query: Annotated[str, Query(description="查询文本", min_length=1, max_length=500)],
    limit: Annotated[int, Query(description="返回结果数量", ge=1, le=20)] = 10,
    use_enhanced: Annotated[bool, Query(description="是否使用增强算法")] = True,
    experiment_id: Annotated[Optional[str], Query(description="AB测试ID")] = None,
) -> dict:
    """
    根据查询文本推荐律师

    基于AI咨询内容提取关键词和领域，匹配律师专长，综合评分后返回推荐结果。

    **增强版评分维度**：
    - 专业领域匹配度 (40%)
    - 用户评价 (30%)
    - 响应速度 (20%)
    - 案例相似度 (10%)

    **冷启动处理**：
    - 新律师给予基础分65分
    - 专业领域匹配仍然适用
    - 保证新律师有展示机会

    **AB测试支持**：
    - 支持通过experiment_id参数进行AB测试
    - 可以对比不同算法的效果

    **返回字段**：
    - lawyer_id: 律师ID
    - lawyer_name: 律师姓名
    - specialties: 专长领域
    - rating: 评分 (0-5)
    - completed_count: 完成咨询数量
    - match_score: 专长匹配分数 (0-1)
    - response_time_score: 响应速度分数 (0-100)
    - case_similarity_score: 案例相似度分数 (0-100)
    - overall_score: 综合分数 (0-100)
    - match_reasons: 匹配原因列表
    - is_cold_start: 是否为冷启动律师
    - experiment_group: AB测试分组
    """
    if db is None:
        raise HTTPException(status_code=500, detail="数据库连接失败")

    try:
        if use_enhanced:
            # 使用增强版算法
            service = get_lawyer_matching_service_enhanced()
            results = await service.recommend_lawyers(
                db, query, limit=limit, experiment_id=experiment_id
            )

            return {
                "query": query,
                "algorithm": "enhanced",
                "experiment_id": experiment_id,
                "count": len(results),
                "lawyers": [
                    {
                        "lawyer_id": r.lawyer_id,
                        "lawyer_name": r.lawyer_name,
                        "specialties": r.specialties,
                        "rating": r.rating,
                        "completed_count": r.completed_count,
                        "match_score": r.match_score,
                        "response_time_score": r.response_time_score,
                        "case_similarity_score": r.case_similarity_score,
                        "overall_score": r.overall_score,
                        "match_reasons": r.match_reasons,
                        "is_cold_start": r.is_cold_start,
                        "experiment_group": r.experiment_group,
                    }
                    for r in results
                ],
            }
        else:
            # 使用原始算法
            service = get_lawyer_matching_service()
            results = await service.recommend_lawyers(db, query, limit=limit)

            return {
                "query": query,
                "algorithm": "original",
                "count": len(results),
                "lawyers": [
                    {
                        "lawyer_id": r.lawyer_id,
                        "lawyer_name": r.lawyer_name,
                        "specialties": r.specialties,
                        "rating": r.rating,
                        "completed_count": r.completed_count,
                        "match_score": r.match_score,
                        "overall_score": r.overall_score,
                        "match_reasons": r.match_reasons,
                    }
                    for r in results
                ],
            }
    except Exception as e:
        logger.exception("律师推荐失败: %s", str(e))
        raise HTTPException(status_code=500, detail=f"律师推荐失败: {str(e)}")


@router.get("/recommend-by-keywords", summary="根据关键词推荐律师")
async def recommend_lawyers_by_keywords(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    keywords: Annotated[list[str], Query(description="关键词列表")] = [],
    domains: Annotated[list[str], Query(description="法律领域列表")] = [],
    limit: Annotated[int, Query(description="返回结果数量", ge=1, le=20)] = 10,
    use_enhanced: Annotated[bool, Query(description="是否使用增强算法")] = True,
    experiment_id: Annotated[Optional[str], Query(description="AB测试ID")] = None,
) -> dict:
    """
    根据关键词和领域推荐律师

    直接使用关键词和领域进行律师匹配，不进行关键词提取。

    **增强版特性**：
    - 多维度评分（专业领域、评价、响应速度、案例相似度）
    - 冷启动处理
    - 排序优化
    - 缓存机制
    - AB测试支持

    **参数**：
    - keywords: 关键词列表，如 ["劳动纠纷", "合同纠纷"]
    - domains: 法律领域列表，如 ["劳动纠纷", "婚姻家庭"]
    - limit: 返回结果数量
    - use_enhanced: 是否使用增强算法（默认True）
    - experiment_id: AB测试ID
    """
    if db is None:
        raise HTTPException(status_code=500, detail="数据库连接失败")

    if not keywords and not domains:
        raise HTTPException(status_code=400, detail="关键词和领域不能同时为空")

    try:
        if use_enhanced:
            # 使用增强版算法
            service = get_lawyer_matching_service_enhanced()
            results = await service.match_lawyers_by_keywords(
                db, keywords, domains, limit=limit, experiment_id=experiment_id
            )

            return {
                "keywords": keywords,
                "domains": domains,
                "algorithm": "enhanced",
                "experiment_id": experiment_id,
                "count": len(results),
                "lawyers": [
                    {
                        "lawyer_id": r.lawyer_id,
                        "lawyer_name": r.lawyer_name,
                        "specialties": r.specialties,
                        "rating": r.rating,
                        "completed_count": r.completed_count,
                        "match_score": r.match_score,
                        "response_time_score": r.response_time_score,
                        "case_similarity_score": r.case_similarity_score,
                        "overall_score": r.overall_score,
                        "match_reasons": r.match_reasons,
                        "is_cold_start": r.is_cold_start,
                        "experiment_group": r.experiment_group,
                    }
                    for r in results
                ],
            }
        else:
            # 使用原始算法
            service = get_lawyer_matching_service()
            results = await service.match_lawyers_by_keywords(
                db, keywords, domains, limit=limit
            )

            return {
                "keywords": keywords,
                "domains": domains,
                "algorithm": "original",
                "count": len(results),
                "lawyers": [
                    {
                        "lawyer_id": r.lawyer_id,
                        "lawyer_name": r.lawyer_name,
                        "specialties": r.specialties,
                        "rating": r.rating,
                        "completed_count": r.completed_count,
                        "match_score": r.match_score,
                        "overall_score": r.overall_score,
                        "match_reasons": r.match_reasons,
                    }
                    for r in results
                ],
            }
    except Exception as e:
        logger.exception("律师推荐失败: %s", str(e))
        raise HTTPException(status_code=500, detail=f"律师推荐失败: {str(e)}")


@router.get("/compare-algorithms", summary="对比推荐算法")
async def compare_algorithms(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    keywords: Annotated[list[str], Query(description="关键词列表")] = [],
    domains: Annotated[list[str], Query(description="法律领域列表")] = [],
    limit: Annotated[int, Query(description="返回结果数量", ge=1, le=20)] = 10,
) -> dict:
    """
    对比原始算法和增强版算法的推荐结果

    同时使用两种算法进行推荐，返回结果对比，便于分析算法效果。

    **返回字段**：
    - original: 原始算法推荐结果
    - enhanced: 增强版算法推荐结果
    - differences: 算法差异分析
    """
    if db is None:
        raise HTTPException(status_code=500, detail="数据库连接失败")

    if not keywords and not domains:
        raise HTTPException(status_code=400, detail="关键词和领域不能同时为空")

    try:
        # 原始算法
        original_service = get_lawyer_matching_service()
        original_results = await original_service.match_lawyers_by_keywords(
            db, keywords, domains, limit=limit
        )

        # 增强版算法
        enhanced_service = get_lawyer_matching_service_enhanced()
        enhanced_results = await enhanced_service.match_lawyers_by_keywords(
            db, keywords, domains, limit=limit
        )

        # 分析差异
        original_ids = set(r.lawyer_id for r in original_results)
        enhanced_ids = set(r.lawyer_id for r in enhanced_results)

        common_ids = original_ids & enhanced_ids
        only_original = original_ids - enhanced_ids
        only_enhanced = enhanced_ids - original_ids

        return {
            "keywords": keywords,
            "domains": domains,
            "original": {
                "count": len(original_results),
                "lawyers": [
                    {
                        "lawyer_id": r.lawyer_id,
                        "lawyer_name": r.lawyer_name,
                        "overall_score": r.overall_score,
                    }
                    for r in original_results
                ],
            },
            "enhanced": {
                "count": len(enhanced_results),
                "lawyers": [
                    {
                        "lawyer_id": r.lawyer_id,
                        "lawyer_name": r.lawyer_name,
                        "overall_score": r.overall_score,
                        "is_cold_start": r.is_cold_start,
                    }
                    for r in enhanced_results
                ],
            },
            "differences": {
                "common_count": len(common_ids),
                "only_original_count": len(only_original),
                "only_enhanced_count": len(only_enhanced),
                "common_ids": sorted(list(common_ids)),
                "only_original_ids": sorted(list(only_original)),
                "only_enhanced_ids": sorted(list(only_enhanced)),
            },
        }
    except Exception as e:
        logger.exception("算法对比失败: %s", str(e))
        raise HTTPException(status_code=500, detail=f"算法对比失败: {str(e)}")
