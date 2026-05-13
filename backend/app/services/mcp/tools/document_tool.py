from __future__ import annotations

from typing import Any

from app.services.mcp.base import BaseTool, ToolCategory, ToolPermission, ToolResult


class DocumentGenerationTool(BaseTool):
    name = "document_generation"
    description = "法律文书生成工具，支持起诉状、答辩状等法律文书的自动生成"
    version = "1.0.0"
    category = ToolCategory.DOCUMENT
    permission = ToolPermission.AUTHENTICATED
    tags = ["文书", "起诉状", "答辩状", "生成"]

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "enum": ["complaint", "defense", "appeal", "counterclaim"],
                    "description": "文书类型",
                },
                "case_type": {
                    "type": "string",
                    "description": "案件类型",
                },
                "plaintiff_name": {
                    "type": "string",
                    "description": "原告姓名",
                },
                "defendant_name": {
                    "type": "string",
                    "description": "被告姓名",
                },
                "facts": {
                    "type": "string",
                    "description": "事实与理由",
                },
                "claims": {
                    "type": "string",
                    "description": "诉讼请求",
                },
            },
            "required": ["document_type", "case_type", "plaintiff_name", "defendant_name"],
        }

    async def execute(self, params: dict, context: dict) -> ToolResult:
        document_type = params.get("document_type")
        if not document_type:
            return ToolResult(success=True, data={"message": "请提供文书类型"})

        try:
            content = await self._generate_document(params)
            return ToolResult(
                success=True,
                data={
                    "document_type": document_type,
                    "content": content,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"文书生成失败: {str(e)}")

    async def _generate_document(self, params: dict) -> str:
        document_type = params.get("document_type", "")
        case_type = params.get("case_type", "")
        plaintiff = params.get("plaintiff_name", "")
        defendant = params.get("defendant_name", "")
        facts = params.get("facts", "")
        claims = params.get("claims", "")

        if document_type == "complaint":
            return f"起诉状\n原告：{plaintiff}\n被告：{defendant}\n案由：{case_type}\n事实与理由：{facts}\n诉讼请求：{claims}"
        elif document_type == "defense":
            return f"答辩状\n答辩人：{defendant}\n被答辩人：{plaintiff}\n案由：{case_type}\n答辩意见：{facts}"
        else:
            return f"法律文书\n类型：{document_type}"
