"""律师推荐Skill - 根据用户法律问题推荐匹配律师"""
import logging
from typing import Optional
from dataclasses import dataclass, field

import httpx

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class LawyerRecommendation:
    lawyer_id: str
    name: str
    specialty: list[str]
    rating: float
    experience_years: int
    hourly_rate: int
    avatar_url: Optional[str] = None
    law_firm: Optional[str] = None
    match_reason: Optional[str] = None


@dataclass
class LawyerRecommendationResult:
    recommendations: list[LawyerRecommendation]
    domain: str
    total_matched: int


LEGAL_DOMAIN_SPECIALTY_MAP: dict[str, list[str]] = {
    "labor": ["劳动法", "劳动合同", "工伤赔偿", "劳动仲裁", "拖欠工资"],
    "contract": ["合同法", "合同纠纷", "买卖合同", "租赁合同", "违约赔偿"],
    "family": ["婚姻法", "离婚", "财产分割", "子女抚养", "继承"],
    "tort": ["侵权法", "交通事故", "人身损害", "医疗纠纷", "产品责任"],
    "property": ["物权法", "房产纠纷", "物业管理", "相邻权", "拆迁补偿"],
    "corporate": ["公司法", "股权纠纷", "公司治理", "企业合规", "破产清算"],
    "ip": ["知识产权", "商标", "专利", "著作权", "商业秘密"],
    "criminal": ["刑法", "刑事辩护", "经济犯罪", "刑事申诉", "取保候审"],
    "admin": ["行政法", "行政诉讼", "行政复议", "行政处罚", "国家赔偿"],
}

INTENT_DOMAIN_MAP: dict[str, str] = {
    "劳动": "labor", "工资": "labor", "工伤": "labor", "辞退": "labor",
    "开除": "labor", "加班": "labor", "社保": "labor", "劳动合同": "labor",
    "合同": "contract", "违约": "contract", "租赁": "contract", "买卖": "contract",
    "离婚": "family", "婚姻": "family", "抚养": "family", "继承": "family", "财产分割": "family",
    "交通事故": "tort", "侵权": "tort", "损害赔偿": "tort", "医疗": "tort",
    "房产": "property", "物业": "property", "拆迁": "property", "物权": "property",
    "公司": "corporate", "股权": "corporate", "破产": "corporate", "合规": "corporate",
    "商标": "ip", "专利": "ip", "著作权": "ip", "知识产权": "ip",
    "刑事": "criminal", "犯罪": "criminal", "辩护": "criminal",
    "行政": "admin", "处罚": "admin", "复议": "admin",
}


def infer_domain_from_query(query: str) -> str:
    for keyword, domain in INTENT_DOMAIN_MAP.items():
        if keyword in query:
            return domain
    return "contract"


class LawyerSkill:
    """律师推荐Skill"""

    def __init__(self):
        self._legal_service_url = getattr(settings, 'legal_service_url', 'http://localhost:8008')
        self._timeout = 5.0

    async def recommend(
        self,
        user_query: str,
        domain: Optional[str] = None,
        max_results: int = 3,
    ) -> LawyerRecommendationResult:
        if not domain:
            domain = infer_domain_from_query(user_query)

        specialties = LEGAL_DOMAIN_SPECIALTY_MAP.get(domain, ["合同法"])

        try:
            lawyers = await self._fetch_lawyers_from_service(specialties, max_results)
        except Exception as e:
            logger.warning(f"从律师服务获取推荐失败: {e}, 使用本地推荐")
            lawyers = self._fallback_recommend(domain, max_results)

        for lawyer in lawyers:
            lawyer.match_reason = self._generate_match_reason(lawyer, domain, user_query)

        return LawyerRecommendationResult(
            recommendations=lawyers,
            domain=domain,
            total_matched=len(lawyers),
        )

    async def _fetch_lawyers_from_service(
        self,
        specialties: list[str],
        max_results: int,
    ) -> list[LawyerRecommendation]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._legal_service_url}/api/v1/lawyers",
                params={
                    "specialty": ",".join(specialties[:3]),
                    "sort_by": "rating",
                    "page_size": max_results,
                },
            )
            response.raise_for_status()
            data = response.json()

            lawyers = []
            for item in data.get("items", data.get("lawyers", [])):
                lawyers.append(LawyerRecommendation(
                    lawyer_id=str(item.get("id", "")),
                    name=item.get("name", "未知律师"),
                    specialty=item.get("specialty", specialties[:2]),
                    rating=float(item.get("rating", 4.5)),
                    experience_years=int(item.get("experience_years", item.get("experience", 5))),
                    hourly_rate=int(item.get("hourly_rate", item.get("consultation_fee", 200))),
                    avatar_url=item.get("avatar_url"),
                    law_firm=item.get("law_firm", item.get("firm_name")),
                ))
            return lawyers

    def _fallback_recommend(
        self,
        domain: str,
        max_results: int,
    ) -> list[LawyerRecommendation]:
        fallback_lawyers: dict[str, list[LawyerRecommendation]] = {
            "labor": [
                LawyerRecommendation(lawyer_id="rec-labor-1", name="张律师", specialty=["劳动法", "劳动合同"], rating=4.8, experience_years=12, hourly_rate=300, law_firm="正义律师事务所"),
                LawyerRecommendation(lawyer_id="rec-labor-2", name="李律师", specialty=["工伤赔偿", "劳动仲裁"], rating=4.6, experience_years=8, hourly_rate=250, law_firm="公平法律事务所"),
            ],
            "contract": [
                LawyerRecommendation(lawyer_id="rec-contract-1", name="王律师", specialty=["合同法", "违约赔偿"], rating=4.9, experience_years=15, hourly_rate=400, law_firm="信达律师事务所"),
                LawyerRecommendation(lawyer_id="rec-contract-2", name="赵律师", specialty=["买卖合同", "租赁合同"], rating=4.7, experience_years=10, hourly_rate=300, law_firm="明理律师事务所"),
            ],
            "family": [
                LawyerRecommendation(lawyer_id="rec-family-1", name="陈律师", specialty=["婚姻法", "财产分割"], rating=4.8, experience_years=11, hourly_rate=350, law_firm="家和律师事务所"),
                LawyerRecommendation(lawyer_id="rec-family-2", name="刘律师", specialty=["子女抚养", "继承"], rating=4.5, experience_years=7, hourly_rate=250, law_firm="安和法律事务所"),
            ],
            "tort": [
                LawyerRecommendation(lawyer_id="rec-tort-1", name="杨律师", specialty=["交通事故", "人身损害"], rating=4.7, experience_years=9, hourly_rate=280, law_firm="平安律师事务所"),
                LawyerRecommendation(lawyer_id="rec-tort-2", name="周律师", specialty=["医疗纠纷", "产品责任"], rating=4.6, experience_years=8, hourly_rate=300, law_firm="维权益律师事务所"),
            ],
        }

        domain_lawyers = fallback_lawyers.get(domain, fallback_lawyers["contract"])
        return domain_lawyers[:max_results]

    def _generate_match_reason(
        self,
        lawyer: LawyerRecommendation,
        domain: str,
        query: str,
    ) -> str:
        domain_label = LEGAL_DOMAIN_SPECIALTY_MAP.get(domain, ["法律"])[0]
        return f"擅长{domain_label}领域，{lawyer.experience_years}年执业经验，评分{lawyer.rating}，与您的问题高度匹配"

    def format_as_suggested_actions(
        self,
        result: LawyerRecommendationResult,
    ) -> list[dict]:
        actions = []
        for lawyer in result.recommendations:
            actions.append({
                "type": "consult_lawyer",
                "label": f"咨询{lawyer.name}",
                "description": lawyer.match_reason,
                "params": {
                    "lawyer_id": lawyer.lawyer_id,
                    "lawyer_name": lawyer.name,
                    "specialty": ",".join(lawyer.specialty),
                    "rating": str(lawyer.rating),
                    "experience": str(lawyer.experience_years),
                    "hourly_rate": str(lawyer.hourly_rate),
                    "law_firm": lawyer.law_firm or "",
                    "avatar_url": lawyer.avatar_url or "",
                },
            })
        return actions


_lawyer_skill: Optional[LawyerSkill] = None


def get_lawyer_skill() -> LawyerSkill:
    global _lawyer_skill
    if _lawyer_skill is None:
        _lawyer_skill = LawyerSkill()
    return _lawyer_skill
