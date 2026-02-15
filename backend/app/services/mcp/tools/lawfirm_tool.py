"""律所查询工具"""

import logging
from typing import Any, Dict, List, Optional

from ..base import BaseTool, ToolResult, ToolCategory, ToolPermission

logger = logging.getLogger(__name__)


class LawfirmSearchTool(BaseTool):
    """律所和律师查询工具"""

    name = "lawfirm_search"
    description = """查询律师事务所和律师信息:
    - 按城市、专长领域筛选律所
    - 查询律师信息和预约咨询
    - 获取律师专长评分和评价

    使用场景:
    - 用户想找律师
    - 用户想了解律所信息
    - AI 推荐合适律师
    """

    version = "1.0.0"
    category = ToolCategory.LAWFIRM
    tags = ["律所", "律师", "查询", "咨询"]
    permission = ToolPermission.PUBLIC

    def __init__(self):
        super().__init__()

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "search_firms",
                        "search_lawyers",
                        "get_firm_detail",
                        "get_lawyer_detail",
                        "recommend"],
                    "description": "操作类型",
                },
                "city": {
                    "type": "string",
                    "description": "城市名称（可选）",
                },
                "specialty": {
                    "type": "string",
                    "description": "专业领域（可选，如 labor_dispute, contract_dispute）",
                },
                "firm_id": {
                    "type": "integer",
                    "description": "律所ID（获取详情时必需）",
                },
                "lawyer_id": {
                    "type": "integer",
                    "description": "律师ID（获取详情时必需）",
                },
                "case_type": {
                    "type": "string",
                    "description": "案件类型，用于推荐匹配的律师",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制",
                },
            },
            "required": ["action"],
        }

    async def execute(
        self,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """执行律所查询"""
        action = params.get("action")

        try:
            if action == "search_firms":
                return await self._search_firms(params)
            elif action == "search_lawyers":
                return await self._search_lawyers(params)
            elif action == "get_firm_detail":
                return await self._get_firm_detail(params)
            elif action == "get_lawyer_detail":
                return await self._get_lawyer_detail(params)
            elif action == "recommend":
                return await self._recommend_lawyers(params)
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作: {action}"
                )
        except Exception as e:
            logger.exception("律所查询失败")
            return ToolResult(
                success=False,
                error=f"查询失败: {str(e)}"
            )

    async def _search_firms(self, params: Dict[str, Any]) -> ToolResult:
        """搜索律所"""
        city = params.get("city")
        specialty = params.get("specialty")
        limit = min(int(params.get("limit", 10)), 50)

        try:
            from sqlalchemy import select, desc, and_, func
            from ...database import get_db
            from ...models.lawfirm import LawFirm

            async with get_db() as db:
                conditions = []
                if city:
                    conditions.append(func.lower(
                        LawFirm.city).like(f"%{city.lower()}%"))
                if specialty:
                    conditions.append(
                        LawFirm.specialties.contains(
                            [specialty]))

                query = select(LawFirm)
                if conditions:
                    query = query.where(and_(*conditions))
                query = query.order_by(desc(LawFirm.rating)).limit(limit)

                result = await db.execute(query)
                firms = result.scalars().all()

                firm_list = []
                for firm in firms:
                    firm_list.append({
                        "id": firm.id,
                        "name": firm.name,
                        "city": firm.city,
                        "province": firm.province,
                        "rating": firm.rating,
                        "review_count": firm.review_count,
                        "lawyer_count": firm.lawyer_count,
                        "is_verified": firm.is_verified,
                        "specialties": firm.specialties[:5] if firm.specialties else [],
                    })

                return ToolResult(
                    success=True,
                    data={
                        "firms": firm_list,
                        "total": len(firm_list),
                        "filters": {
                            "city": city,
                            "specialty": specialty,
                        },
                    }
                )

        except Exception as e:
            logger.exception("搜索律所失败")
            return ToolResult(
                success=False,
                error=f"搜索律所失败: {str(e)}"
            )

    async def _search_lawyers(self, params: Dict[str, Any]) -> ToolResult:
        """搜索律师"""
        city = params.get("city")
        specialty = params.get("specialty")
        limit = min(int(params.get("limit", 10)), 50)

        try:
            from sqlalchemy import select, desc, and_, or_, func
            from ...database import get_db
            from ...models.lawfirm import LawFirm, Lawyer

            async with get_db() as db:
                conditions = [Lawyer.is_verified]

                if city:
                    city_condition = or_(
                        LawFirm.city.ilike(f"%{city}%"),
                        Lawyer.city.ilike(f"%{city}%"),
                    )
                    conditions.append(city_condition)

                if specialty:
                    conditions.append(
                        Lawyer.specialties.ilike(
                            f"%{specialty}%"))

                query = (
                    select(Lawyer)
                    .join(LawFirm, Lawyer.firm_id == LawFirm.id)
                    .where(and_(*conditions))
                    .order_by(desc(Lawyer.rating))
                    .limit(limit)
                )

                result = await db.execute(query)
                lawyers = result.scalars().all()

                lawyer_list = []
                for lawyer in lawyers:
                    lawyer_list.append({
                        "id": lawyer.id,
                        "name": lawyer.name,
                        "title": lawyer.title,
                        "firm_id": lawyer.firm_id,
                        "firm_name": lawyer.firm.name if lawyer.firm else None,
                        "rating": lawyer.rating,
                        "review_count": lawyer.review_count,
                        "consultation_fee": lawyer.consultation_fee,
                        "specialties": lawyer.specialties[:5] if lawyer.specialties else [],
                        "city": lawyer.city,
                    })

                return ToolResult(
                    success=True,
                    data={
                        "lawyers": lawyer_list,
                        "total": len(lawyer_list),
                    }
                )

        except Exception as e:
            logger.exception("搜索律师失败")
            return ToolResult(
                success=False,
                error=f"搜索律师失败: {str(e)}"
            )

    async def _get_firm_detail(self, params: Dict[str, Any]) -> ToolResult:
        """获取律所详情"""
        firm_id = params.get("firm_id")

        if not firm_id:
            return ToolResult(
                success=False,
                error="请提供律所ID"
            )

        try:
            from sqlalchemy import select
            from ...database import get_db
            from ...models.lawfirm import LawFirm

            async with get_db() as db:
                result = await db.execute(
                    select(LawFirm).where(LawFirm.id == firm_id)
                )
                firm = result.scalar_one_or_none()

                if not firm:
                    return ToolResult(
                        success=False,
                        error=f"未找到ID为 {firm_id} 的律所"
                    )

                return ToolResult(
                    success=True,
                    data={
                        "id": firm.id,
                        "name": firm.name,
                        "description": firm.description,
                        "address": firm.address,
                        "city": firm.city,
                        "province": firm.province,
                        "phone": firm.phone,
                        "email": firm.email,
                        "website": firm.website,
                        "rating": firm.rating,
                        "review_count": firm.review_count,
                        "lawyer_count": firm.lawyer_count,
                        "is_verified": firm.is_verified,
                        "specialties": firm.specialties or [],
                    }
                )

        except Exception as e:
            logger.exception("获取律所详情失败")
            return ToolResult(
                success=False,
                error=f"获取律所详情失败: {str(e)}"
            )

    async def _get_lawyer_detail(self, params: Dict[str, Any]) -> ToolResult:
        """获取律师详情"""
        lawyer_id = params.get("lawyer_id")

        if not lawyer_id:
            return ToolResult(
                success=False,
                error="请提供律师ID"
            )

        try:
            from sqlalchemy import select
            from ...database import get_db
            from ...models.lawfirm import Lawyer

            async with get_db() as db:
                result = await db.execute(
                    select(Lawyer).where(Lawyer.id == lawyer_id)
                )
                lawyer = result.scalar_one_or_none()

                if not lawyer:
                    return ToolResult(
                        success=False,
                        error=f"未找到ID为 {lawyer_id} 的律师"
                    )

                return ToolResult(
                    success=True,
                    data={
                        "id": lawyer.id,
                        "name": lawyer.name,
                        "title": lawyer.title,
                        "firm_id": lawyer.firm_id,
                        "firm_name": lawyer.firm.name if lawyer.firm else None,
                        "rating": lawyer.rating,
                        "review_count": lawyer.review_count,
                        "consultation_fee": lawyer.consultation_fee,
                        "consultation_way": lawyer.consultation_way,
                        "specialties": lawyer.specialties or [],
                        "bio": lawyer.bio,
                        "city": lawyer.city,
                        "years_of_practice": lawyer.years_of_practice,
                        "education": lawyer.education,
                    }
                )

        except Exception as e:
            logger.exception("获取律师详情失败")
            return ToolResult(
                success=False,
                error=f"获取律师详情失败: {str(e)}"
            )

    async def _recommend_lawyers(self, params: Dict[str, Any]) -> ToolResult:
        """推荐律师"""
        case_type = params.get("case_type")
        city = params.get("city")
        limit = min(int(params.get("limit", 5)), 20)

        try:
            from sqlalchemy import select, desc, and_
            from ...database import get_db
            from ...models.lawfirm import LawFirm, Lawyer

            # 根据案件类型映射专长标签
            specialty_map = {
                "labor_dispute": ["劳动争议", "劳动纠纷", "劳动合同"],
                "contract_dispute": ["合同纠纷", "合同法", "民商事"],
                "marriage_family": ["婚姻家庭", "离婚", "继承"],
                "property_dispute": ["房产纠纷", "物业", "房地产"],
                "consumer_rights": ["消费维权", "消费者权益", "产品质量"],
                "traffic_accident": ["交通事故", "交通肇事", "保险理赔"],
                "loan_dispute": ["借贷纠纷", "借款", "债务"],
            }

            target_specialties = specialty_map.get(
                str(case_type) if case_type else "", [
                    str(case_type) if case_type else ""])

            async with get_db() as db:
                conditions = [
                    Lawyer.is_verified,
                    Lawyer.consultation_fee.isnot(None),
                ]

                if city:
                    conditions.append(Lawyer.city.ilike(f"%{city}%"))

                query = (
                    select(Lawyer)
                    .join(LawFirm, Lawyer.firm_id == LawFirm.id)
                    .where(and_(*conditions))
                    .order_by(desc(Lawyer.rating), desc(Lawyer.review_count))
                    .limit(limit * 2)
                )

                result = await db.execute(query)
                lawyers = result.scalars().all()

                scored_lawyers = []
                for lawyer in lawyers:
                    score = 0
                    lawyer_specialties = [s.lower()
                                          for s in (lawyer.specialties or [])]

                    for target in target_specialties:
                        for ls in lawyer_specialties:
                            if target.lower() in ls or ls in target.lower():
                                score += 10
                                break

                    score += lawyer.rating * 2
                    score += min(lawyer.review_count / 10, 5)

                    scored_lawyers.append((lawyer, score))

                scored_lawyers.sort(key=lambda x: x[1], reverse=True)

                recommendations = []
                for lawyer, score in scored_lawyers[:limit]:
                    if score > 0:
                        recommendations.append({
                            "id": lawyer.id,
                            "name": lawyer.name,
                            "title": lawyer.title,
                            "firm_name": lawyer.firm.name if lawyer.firm else None,
                            "rating": lawyer.rating,
                            "review_count": lawyer.review_count,
                            "consultation_fee": lawyer.consultation_fee,
                            "specialties": lawyer.specialties[:5],
                            "match_score": round(score, 1),
                            "match_reason": f"专长匹配 · 评分 {lawyer.rating:.1f} · {lawyer.review_count} 条评价",
                        })

                return ToolResult(
                    success=True,
                    data={
                        "recommendations": recommendations,
                        "total": len(recommendations),
                        "case_type": case_type,
                        "city": city,
                    }
                )

        except Exception as e:
            logger.exception("推荐律师失败")
            return ToolResult(
                success=False,
                error=f"推荐律师失败: {str(e)}"
            )
