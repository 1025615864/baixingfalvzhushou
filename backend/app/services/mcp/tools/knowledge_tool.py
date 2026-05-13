from __future__ import annotations

from typing import Any

from app.services.mcp.base import BaseTool, ToolCategory, ToolPermission, ToolResult


class KnowledgeSearchTool(BaseTool):
    name = "knowledge_search"
    description = "法律知识搜索工具，支持法条查询、案例检索等"
    version = "1.0.0"
    category = ToolCategory.KNOWLEDGE
    permission = ToolPermission.PUBLIC
    tags = ["知识", "法条", "案例", "搜索"]

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "law_type": {
                    "type": "string",
                    "description": "法律类型筛选",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制",
                    "default": 10,
                },
            },
            "required": ["query"],
        }

    async def execute(self, params: dict, context: dict) -> ToolResult:
        query = params.get("query", "").strip()
        if not query:
            return ToolResult(success=False, error="请提供搜索关键词")

        limit = params.get("limit", 10)

        try:
            results = await self._search_knowledge(query, params.get("law_type"), limit)
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total": len(results),
                    "limit": limit,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"搜索失败: {str(e)}")

    async def _search_knowledge(self, query: str, law_type: str | None = None, limit: int = 10) -> list:
        return []
