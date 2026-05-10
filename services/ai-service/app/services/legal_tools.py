"""法律工具注册 - AI Agent可调用的工具集合"""
import logging
from typing import Optional
from dataclasses import dataclass

from app.services.lawyer_skill import get_lawyer_skill, infer_domain_from_query

logger = logging.getLogger(__name__)


@dataclass
class ToolCallResult:
    tool_name: str
    success: bool
    data: dict
    error: Optional[str] = None


LEGAL_TOOLS = {
    "query_law_article": {
        "name": "query_law_article",
        "description": "查询具体法律条文内容，输入法条名称和条款号",
        "parameters": {
            "law_name": {"type": "string", "description": "法律名称，如'劳动合同法'"},
            "article_number": {"type": "string", "description": "条款号，如'第44条'"},
        },
    },
    "search_legal_cases": {
        "name": "search_legal_cases",
        "description": "搜索相关法律案例，输入关键词和领域",
        "parameters": {
            "keywords": {"type": "string", "description": "搜索关键词"},
            "domain": {"type": "string", "description": "法律领域，如labor/contract/family"},
            "limit": {"type": "integer", "description": "返回数量，默认3"},
        },
    },
    "recommend_lawyer": {
        "name": "recommend_lawyer",
        "description": "根据用户法律问题推荐匹配的专业律师",
        "parameters": {
            "query": {"type": "string", "description": "用户的法律问题描述"},
            "domain": {"type": "string", "description": "法律领域（可选，自动推断）"},
            "max_results": {"type": "integer", "description": "最多推荐数量，默认3"},
        },
    },
    "calculate_compensation": {
        "name": "calculate_compensation",
        "description": "计算法律赔偿金额，如经济补偿金、工伤赔偿等",
        "parameters": {
            "calculation_type": {"type": "string", "description": "计算类型：severance_pay/work_injury/traffic_accident"},
            "salary": {"type": "number", "description": "月工资（元）"},
            "years": {"type": "number", "description": "工作年限"},
            "disability_level": {"type": "integer", "description": "伤残等级（1-10）"},
        },
    },
}


def get_tool_definitions() -> list[dict]:
    return list(LEGAL_TOOLS.values())


async def execute_tool(tool_name: str, parameters: dict) -> ToolCallResult:
    if tool_name not in LEGAL_TOOLS:
        return ToolCallResult(
            tool_name=tool_name,
            success=False,
            data={},
            error=f"未知工具: {tool_name}",
        )

    try:
        if tool_name == "recommend_lawyer":
            return await _execute_recommend_lawyer(parameters)
        elif tool_name == "query_law_article":
            return await _execute_query_law_article(parameters)
        elif tool_name == "search_legal_cases":
            return await _execute_search_legal_cases(parameters)
        elif tool_name == "calculate_compensation":
            return await _execute_calculate_compensation(parameters)
        else:
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                data={},
                error=f"工具未实现: {tool_name}",
            )
    except Exception as e:
        logger.error(f"工具执行失败 {tool_name}: {e}")
        return ToolCallResult(
            tool_name=tool_name,
            success=False,
            data={},
            error=str(e),
        )


async def _execute_recommend_lawyer(params: dict) -> ToolCallResult:
    query = params.get("query", "")
    domain = params.get("domain") or infer_domain_from_query(query)
    max_results = params.get("max_results", 3)

    lawyer_skill = get_lawyer_skill()
    result = await lawyer_skill.recommend(
        user_query=query,
        domain=domain,
        max_results=max_results,
    )

    return ToolCallResult(
        tool_name="recommend_lawyer",
        success=True,
        data={
            "domain": result.domain,
            "total_matched": result.total_matched,
            "recommendations": [
                {
                    "lawyer_id": r.lawyer_id,
                    "name": r.name,
                    "specialty": r.specialty,
                    "rating": r.rating,
                    "experience_years": r.experience_years,
                    "hourly_rate": r.hourly_rate,
                    "law_firm": r.law_firm,
                    "match_reason": r.match_reason,
                }
                for r in result.recommendations
            ],
            "suggested_actions": lawyer_skill.format_as_suggested_actions(result),
        },
    )


async def _execute_query_law_article(params: dict) -> ToolCallResult:
    law_name = params.get("law_name", "")
    article_number = params.get("article_number", "")

    common_articles: dict[str, dict[str, str]] = {
        "劳动合同法第44条": "有下列情形之一的，劳动合同终止：（一）劳动合同期满的；（二）劳动者开始依法享受基本养老保险待遇的；（三）劳动者死亡，或者被人民法院宣告死亡或者宣告失踪的；（四）用人单位被依法宣告破产的；（五）用人单位被吊销营业执照、责令关闭、撤销或者用人单位决定提前解散的；（六）法律、行政法规规定的其他情形。",
        "劳动合同法第46条": "有下列情形之一的，用人单位应当向劳动者支付经济补偿：（一）劳动者依照本法第三十八条规定解除劳动合同的；（二）用人单位依照本法第三十六条规定向劳动者提出解除劳动合同并与劳动者协商一致解除劳动合同的；（三）用人单位依照本法第四十条规定解除劳动合同的；（四）用人单位依照本法第四十一条第一款规定解除劳动合同的；（五）除用人单位维持或者提高劳动合同约定条件续订劳动合同，劳动者不同意续订的情形外，依照本法第四十四条第一项规定终止固定期限劳动合同的；（六）依照本法第四十四条第四项、第五项规定终止劳动合同的；（七）法律、行政法规规定的其他情形。",
        "劳动合同法第47条": "经济补偿按劳动者在本单位工作的年限，每满一年支付一个月工资的标准向劳动者支付。六个月以上不满一年的，按一年计算；不满六个月的，向劳动者支付半个月工资的经济补偿。劳动者月工资高于用人单位所在直辖市、设区的市级人民政府公布的本地区上年度职工月平均工资三倍的，向其支付经济补偿的标准按职工月平均工资三倍的数额支付，向其支付经济补偿的年限最高不超过十二年。本条所称月工资是指劳动者在劳动合同解除或者终止前十二个月的平均工资。",
        "民法典第1165条": "行为人因过错侵害他人民事权益造成损害的，应当承担侵权责任。依照法律规定推定行为人有过错，其不能证明自己没有过错的，应当承担侵权责任。",
        "民法典第1179条": "侵害他人造成人身损害的，应当赔偿医疗费、护理费、交通费、营养费、住院伙食补助费等为治疗和康复支出的合理费用，以及因误工减少的收入。造成残疾的，还应当赔偿辅助器具费和残疾赔偿金；造成死亡的，还应当赔偿丧葬费和死亡赔偿金。",
    }

    key = f"{law_name}{article_number}"
    content = common_articles.get(key)

    if content:
        return ToolCallResult(
            tool_name="query_law_article",
            success=True,
            data={"law_name": law_name, "article_number": article_number, "content": content},
        )

    return ToolCallResult(
        tool_name="query_law_article",
        success=False,
        data={"law_name": law_name, "article_number": article_number},
        error=f"未找到 {law_name} {article_number} 的内容，请通过RAG检索获取",
    )


async def _execute_search_legal_cases(params: dict) -> ToolCallResult:
    keywords = params.get("keywords", "")
    domain = params.get("domain", "")
    limit = params.get("limit", 3)

    return ToolCallResult(
        tool_name="search_legal_cases",
        success=True,
        data={
            "keywords": keywords,
            "domain": domain,
            "cases": [],
            "note": "案例检索需通过RAG知识库完成，此工具为占位实现",
        },
    )


async def _execute_calculate_compensation(params: dict) -> ToolCallResult:
    calc_type = params.get("calculation_type", "")
    salary = params.get("salary", 0)
    years = params.get("years", 0)

    if calc_type == "severance_pay" and salary > 0 and years > 0:
        months = years
        if years < 1:
            months = 0.5 if years < 0.5 else 1
        compensation = salary * months
        return ToolCallResult(
            tool_name="calculate_compensation",
            success=True,
            data={
                "calculation_type": "经济补偿金",
                "formula": f"月工资({salary}元) × 工作年限({years}年) = {compensation}元",
                "result": compensation,
                "legal_basis": "《劳动合同法》第47条",
                "note": "此为估算值，实际金额可能因具体情况而异",
            },
        )

    return ToolCallResult(
        tool_name="calculate_compensation",
        success=False,
        data={},
        error="缺少必要参数，请提供月工资和工作年限",
    )
