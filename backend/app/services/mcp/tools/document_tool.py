"""文档生成工具"""

import logging
from typing import Any, Dict, Optional

from ..base import BaseTool, ToolResult, ToolCategory, ToolPermission

logger = logging.getLogger(__name__)


class DocumentGenerationTool(BaseTool):
    """法律文书生成工具"""

    name = "document_generation"
    description = """生成法律文书，包括民事起诉状、答辩状、和解协议书、律师函等。

    使用场景:
    - 用户需要正式的法律文书
    - AI 咨询后发现需要走诉讼程序
    - 当事人希望了解文书模板格式

    注意: 生成的文书仅供参考，正式使用前建议咨询专业律师"""

    version = "1.0.0"
    category = ToolCategory.DOCUMENT
    tags = ["文书", "起诉状", "法律文档"]
    permission = ToolPermission.USER_REQUIRED

    def __init__(self):
        super().__init__()
        self._template_cache: Optional[Dict] = None

    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "enum": [
                        "complaint",
                        "defense",
                        "agreement",
                        "letter"],
                    "description": "文书类型: complaint(起诉状), defense(答辩状), agreement(和解协议), letter(律师函)",
                },
                "case_type": {
                    "type": "string",
                    "enum": [
                        "labor_dispute",
                        "contract_dispute",
                        "marriage_family",
                        "property_dispute",
                        "consumer_rights",
                        "traffic_accident",
                        "loan_dispute"],
                    "description": "案件类型",
                },
                "plaintiff_name": {
                    "type": "string",
                    "description": "原告姓名/名称",
                },
                "defendant_name": {
                    "type": "string",
                    "description": "被告姓名/名称",
                },
                "facts": {
                    "type": "string",
                    "description": "案件事实经过",
                },
                "claims": {
                    "type": "string",
                    "description": "诉讼请求/诉求",
                },
                "evidence": {
                    "type": "string",
                    "description": "证据说明（可选）",
                },
                "court_name": {
                    "type": "string",
                    "description": "管辖法院（可选）",
                },
            },
            "required": [
                "document_type",
                "case_type",
                "plaintiff_name",
                "defendant_name",
                "facts",
                "claims"],
        }

    async def execute(
        self,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """执行文书生成"""
        try:
            document_type = str(params.get("document_type") or "")
            case_type = str(params.get("case_type") or "")
            plaintiff_name = str(params.get("plaintiff_name", ""))
            defendant_name = params.get("defendant_name", "")
            facts = params.get("facts", "")
            claims = params.get("claims", "")
            evidence = params.get("evidence", "")
            court_name = params.get("court_name", "有管辖权的人民法院")

            # 生成文书内容
            content = self._generate_document(
                document_type=document_type,
                case_type=case_type,
                plaintiff_name=plaintiff_name,
                defendant_name=defendant_name,
                facts=facts,
                claims=claims,
                evidence=evidence,
                court_name=court_name,
            )

            # 获取模板信息
            template_info = self._get_template_info(document_type, case_type)

            return ToolResult(
                success=True,
                data={
                    "content": content,
                    "document_type": document_type,
                    "case_type": case_type,
                    "template_name": template_info["name"],
                    "template_description": template_info["description"],
                    "generated_at": self._get_timestamp(),
                },
                metadata={
                    "word_count": len(content),
                    "is_builtin_template": True,
                }
            )

        except Exception as e:
            logger.exception("文书生成失败")
            return ToolResult(
                success=False,
                error=f"文书生成失败: {str(e)}"
            )

    def _generate_document(
        self,
        document_type: str,
        case_type: str,
        plaintiff_name: str,
        defendant_name: str,
        facts: str,
        claims: str,
        evidence: str,
        court_name: str,
    ) -> str:
        """生成文书内容"""
        # 格式化类型名称
        type_names = {
            "complaint": "民事起诉状",
            "defense": "民事答辩状",
            "agreement": "和解协议书",
            "letter": "律师函",
        }
        case_type_names = {
            "labor_dispute": "劳动争议",
            "contract_dispute": "合同纠纷",
            "marriage_family": "婚姻家庭纠纷",
            "property_dispute": "财产纠纷",
            "consumer_rights": "消费维权纠纷",
            "traffic_accident": "交通事故责任纠纷",
            "loan_dispute": "借贷纠纷",
        }

        doc_type_name = type_names.get(document_type, "法律文书")
        case_type_name = case_type_names.get(case_type, case_type)

        # 构建文书内容
        if document_type == "complaint":
            content = f"""民事起诉状

原告：{plaintiff_name}，性别：___，出生日期：____年__月__日，身份证号码：________________________，住所地：________________________________，联系电话：________________。

被告：{defendant_name}，_______________________________________________________________。

法定代表人：________________，职务：________________。

诉讼请求：

{claims}

事实与理由：

{facts}

证据及证据来源：

{evidence if evidence else '（无）'}

此致

{court_name}

起诉人（签名）：_______________

____年____月____日

---
注：本文书由 AI 自动生成，仅供参考。正式使用前请务必咨询专业律师进行审核和修改。
"""
        elif document_type == "defense":
            content = f"""民事答辩状

答辩人：{defendant_name}，_______________________________________________________________。

被答辩人：{plaintiff_name}，_______________________________________________________________。

案由：{case_type_name}

答辩意见：

针对原告的诉讼请求，答辩人提出如下答辩意见：

1. ________________________________________________________

2. ________________________________________________________

综上所述，答辩人认为原告的诉讼请求缺乏事实和法律依据，请求法院依法驳回原告的全部诉讼请求。

此致

{court_name}

答辩人（签名）：_______________

____年____月____日

---
注：本文书由 AI 自动生成，仅供参考。正式使用前请务必咨询专业律师进行审核和修改。
"""
        elif document_type == "agreement":
            content = f"""和解协议书

甲方：{plaintiff_name}，_______________________________________________________________。

乙方：{defendant_name}，_______________________________________________________________。

鉴于甲乙双方存在{case_type_name}纠纷，经双方友好协商，自愿达成如下和解协议：

第一条 争议事项

双方确认存在以下争议：________________________________________________________

第二条 和解方案

1. ________________________________________________________

2. ________________________________________________________

第三条 履行期限

双方应于本协议签订后____日内履行上述义务。

第四条 违约责任

如一方不履行本协议约定的义务，应向守约方支付违约金人民币______元。

第五条 争议解决

因本协议引起的争议，双方应协商解决；协商不成的，向{court_name}提起诉讼。

甲方（签名）：_______________

乙方（签名）：_______________

签订日期：____年____月____日

---
注：本文书由 AI 自动生成，仅供参考。正式使用前请务必咨询专业律师进行审核和修改。
"""
        elif document_type == "letter":
            content = f"""律师函

{defendant_name}：

本所依法接受{plaintiff_name}的委托，指派本律师就贵方与其之间的{case_type_name}事宜，发送本律师函。

事实概要：

{facts}

法律依据：

________________________________________________________

正式函告：

{claims}

请贵方于收到本函后____日内予以回复并妥善处理，否则委托人将依法采取进一步法律措施。

此致

敬礼

承办律师：_______________

____律师事务所

____年____月____日

---
注：本文书由 AI 自动生成，仅供参考。正式使用前请务必咨询专业律师进行审核和修改。
"""
        else:
            content = f"""法律文书

文书类型：{doc_type_name}
案件类型：{case_type_name}

原告/甲方：{plaintiff_name}
被告/乙方：{defendant_name}

{f"争议金额：{claims}" if claims else ""}

案件事实：

{facts}

此致

{court_name}

____年____月____日

---
注：本文书由 AI 自动生成，仅供参考。正式使用前请务必咨询专业律师进行审核和修改。
"""

        return content

    def _get_template_info(self, document_type: str,
                           case_type: str) -> Dict[str, str]:
        """获取模板信息"""
        # 模板信息映射
        templates = {
            "complaint": {"name": "民事起诉状", "description": "向法院提起民事诉讼的文书"},
            "defense": {"name": "民事答辩状", "description": "被告针对原告诉讼请求的答辩文书"},
            "agreement": {"name": "和解协议书", "description": "双方达成和解的协议文书"},
            "letter": {"name": "律师函", "description": "以律师名义发出的法律文书"},
        }
        return templates.get(
            document_type, {"name": f"{document_type} 模板", "description": ""})

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
