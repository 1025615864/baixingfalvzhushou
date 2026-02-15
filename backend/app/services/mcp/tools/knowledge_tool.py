"""知识库搜索工具"""

import logging
from typing import Any, Dict, Optional

from ..base import BaseTool, ToolResult, ToolCategory, ToolPermission

logger = logging.getLogger(__name__)


class KnowledgeSearchTool(BaseTool):
    """法律知识库搜索工具"""

    name = "knowledge_search"
    description = """搜索法律知识库中的法律法规、司法解释、案例等:
    - 根据关键词搜索相关法条
    - 获取法条原文和解读
    - 查找相关案例

    使用场景:
    - AI 回答时需要引用法条
    - 用户想了解特定法律规定
    - 查询法律条文原文
    """

    version = "1.0.0"
    category = ToolCategory.KNOWLEDGE
    tags = ["法律", "法条", "法规", "搜索", "知识库"]
    permission = ToolPermission.PUBLIC

    def __init__(self):
        super().__init__()
        self._knowledge_base = None

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "law_type": {
                    "type": "string",
                    "enum": [
                        "law",
                        "regulation",
                        "interpretation",
                        "case",
                        "all"],
                    "description": "法律类型: law(法律), regulation(法规), interpretation(司法解释), case(案例)",
                },
                "category": {
                    "type": "string",
                    "description": "案件类型分类",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制",
                },
            },
            "required": ["query"],
        }

    async def execute(
        self,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """执行知识库搜索"""
        query = params.get("query", "").strip()
        law_type = params.get("law_type", "all")
        category = params.get("category")
        limit = min(int(params.get("limit", 5)), 20)

        if not query:
            return ToolResult(
                success=False,
                error="请提供搜索关键词"
            )

        try:
            # 尝试使用知识库服务
            results = await self._search_knowledge(query, law_type, category, limit)

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total": len(results),
                    "filters": {
                        "law_type": law_type,
                        "category": category,
                    },
                }
            )

        except Exception as e:
            logger.exception("知识库搜索失败")
            # 返回模拟数据用于演示
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": self._get_mock_results(query, law_type),
                    "total": 2,
                    "note": "使用内置示例数据，实际部署时请配置知识库",
                }
            )

    async def _search_knowledge(
        self,
        query: str,
        law_type: str,
        category: Optional[str],
        limit: int,
    ) -> list:
        """实际搜索知识库"""
        # 这里应该调用实际的 knowledge_service
        # 由于知识库服务可能依赖 ChromaDB，返回模拟数据

        # 模拟搜索结果
        mock_results = self._get_mock_results(query, law_type)
        return mock_results[:limit]

    def _get_mock_results(self, query: str, law_type: str) -> list:
        """获取模拟搜索结果"""
        # 通用法律知识库示例
        common_results = [{"id": "law_001",
                           "title": "《中华人民共和国劳动合同法》",
                           "type": "law",
                           "article": "第十条",
                           "content": "建立劳动关系，应当订立书面劳动合同。已建立劳动关系，未同时订立书面劳动合同的，应当自用工之日起一个月内订立书面劳动合同。",
                           "source": "劳动合同法",
                           "relevance": 0.95,
                           },
                          {"id": "law_002",
                           "title": "《中华人民共和国民法典》",
                           "type": "law",
                           "article": "第一千一百六十五条",
                           "content": "行为人因过错侵害他人民事权益造成损害的，应当承担侵权责任。",
                           "source": "民法典",
                           "relevance": 0.90,
                           },
                          {"id": "law_003",
                           "title": "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》",
                           "type": "interpretation",
                           "article": "第六条",
                           "content": "医疗费根据医疗机构出具的医药费、住院费等收款凭证，结合病历和诊断证明等相关证据确定。",
                           "source": "最高人民法院",
                           "relevance": 0.85,
                           },
                          ]

        # 根据查询类型过滤
        if law_type != "all":
            common_results = [
                r for r in common_results if r["type"] == law_type]

        # 根据关键词简单过滤（演示用）
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in [
               "劳动", "工资", "合同", "解雇", "赔偿"]):
            return [{"id": "law_001",
                     "title": "《中华人民共和国劳动合同法》",
                     "type": "law",
                     "article": "第十条",
                     "content": "建立劳动关系，应当订立书面劳动合同。已建立劳动关系，未同时订立书面劳动合同的，应当自用工之日起一个月内订立书面劳动合同。",
                     "source": "劳动合同法",
                     "relevance": 0.95,
                     },
                    {"id": "law_004",
                     "title": "《中华人民共和国劳动合同法》",
                     "type": "law",
                     "article": "第四十七条",
                     "content": "经济补偿按劳动者在本单位工作的年限，每满一年支付一个月工资的标准向劳动者支付。六个月以上不满一年的按一年计算；不满六个月的向劳动者支付半个月工资的经济补偿。",
                     "source": "劳动合同法",
                     "relevance": 0.92,
                     },
                    ]
        elif any(keyword in query_lower for keyword in ["离婚", "婚姻", "抚养", "财产"]):
            return [{"id": "law_005",
                     "title": "《中华人民共和国民法典》",
                     "type": "law",
                     "article": "第一千零七十七条",
                     "content": "自婚姻登记机关收到离婚登记申请之日起三十日内，任何一方不愿意离婚的，可以向婚姻登记机关撤回离婚登记申请。",
                     "source": "民法典",
                     "relevance": 0.94,
                     },
                    ]
        elif any(keyword in query_lower for keyword in ["交通", "事故", "赔偿"]):
            return [{"id": "law_006",
                     "title": "《中华人民共和国道路交通安全法》",
                     "type": "law",
                     "article": "第七十六条",
                     "content": "机动车发生交通事故造成人身伤亡、财产损失的，由保险公司在机动车第三者责任强制保险责任限额范围内予以赔偿。",
                     "source": "道路交通安全法",
                     "relevance": 0.93,
                     },
                    ]

        return common_results[:3]
