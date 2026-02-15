"""模块联动服务

处理跨模块的业务流程，如 咨询→文书→律师 闭环。
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """工作流类型"""
    CONSULTATION_TO_DOCUMENT = "consultation_to_document"
    CONSULTATION_TO_LAWYER = "consultation_to_lawyer"
    DOCUMENT_TO_LAWYER = "document_to_lawyer"
    NEWS_TO_FORUM = "news_to_forum"
    FORUM_TO_AI = "forum_to_ai"


@dataclass
class WorkflowContext:
    """工作流上下文"""
    user_id: int
    workflow_type: WorkflowType
    source_module: str
    target_module: str
    data: Dict[str, Any] = field(default_factory=dict)
    completed_steps: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class ConsultationDocumentIntegration:
    """咨询到文书的联动服务"""

    # 触发关键词
    DOCUMENT_TRIGGERS = [
        "生成文书", "写起诉状", "写答辩状", "写协议",
        "需要文书", "帮我写", "起草", "范本",
    ]

    # 案件类型关键词映射
    CASE_TYPE_KEYWORDS = {
        "labor_dispute": ["劳动", "工资", "解雇", "劳动合同", "赔偿", "补偿"],
        "contract_dispute": ["合同", "违约", "条款", "解除合同"],
        "marriage_family": ["离婚", "财产分割", "抚养", "继承", "婚姻"],
        "property_dispute": ["房产", "物业", "房屋", "产权"],
        "consumer_rights": ["消费", "维权", "假货", "质量", "退款"],
        "traffic_accident": ["交通事故", "撞车", "责任", "赔偿"],
        "loan_dispute": ["借款", "贷款", "欠钱", "债务"],
    }

    def __init__(self):
        # user_id -> workflows
        self._workflows: Dict[int, List[WorkflowContext]] = {}

    def detect_document_intent(self, message: str) -> Optional[Dict[str, Any]]:
        """检测是否需要生成文书

        Returns:
            如果检测到文书需求，返回 {'case_type': str, 'document_type': str, 'context': str}
        """
        message_lower = message.lower()

        # 检查触发词
        for trigger in self.DOCUMENT_TRIGGERS:
            if trigger.lower() in message_lower:
                # 推断案件类型
                case_type = self._infer_case_type(message)
                document_type = self._infer_document_type(message, case_type)

                return {
                    "case_type": case_type,
                    "document_type": document_type,
                    "context": message[:500],  # 截取上下文
                    "confidence": 0.8,
                }

        return None

    def _infer_case_type(self, message: str) -> str:
        """推断案件类型"""
        message_lower = message.lower()
        for case_type, keywords in self.CASE_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return case_type
        return "contract_dispute"  # 默认

    def _infer_document_type(self, message: str, case_type: str) -> str:
        """推断文书类型"""
        message_lower = message.lower()

        if any(w in message_lower for w in ["起诉状", "起诉", "诉讼"]):
            return "complaint"
        elif any(w in message_lower for w in ["答辩状", "答辩", "回应"]):
            return "defense"
        elif any(w in message_lower for w in ["协议", "和解", "协商"]):
            return "agreement"
        elif any(w in message_lower for w in ["律师函", "函", "警告"]):
            return "letter"

        return "complaint"  # 默认起诉状

    def suggest_document_generation(
        self,
        conversation: List[Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """根据对话历史建议生成文书

        Args:
            conversation: 对话历史 [{role: 'user'|'assistant', content: str}]

        Returns:
            建议信息或 None
        """
        # 检查最近的消息
        recent_messages = conversation[-5:] if len(
            conversation) > 5 else conversation

        for msg in reversed(recent_messages):
            if msg["role"] == "user":
                result = self.detect_document_intent(msg["content"])
                if result:
                    return {
                        "suggested": True,
                        "case_type": result["case_type"],
                        "document_type": result["document_type"],
                        "message": f"根据您的咨询，建议生成{self._get_document_name(result['document_type'])}",
                        "quick_action": {
                            "label": "生成文书",
                            "params": {
                                "case_type": result["case_type"],
                                "document_type": result["document_type"],
                                "context": result["context"],
                            },
                        },
                    }

        return None

    def _get_document_name(self, doc_type: str) -> str:
        """获取文书类型名称"""
        names = {
            "complaint": "民事起诉状",
            "defense": "民事答辩状",
            "agreement": "和解协议书",
            "letter": "律师函",
        }
        return names.get(doc_type, "法律文书")

    def create_workflow(
        self,
        user_id: int,
        conversation_id: str,
        suggestion: Dict[str, Any],
    ) -> WorkflowContext:
        """创建咨询→文书工作流"""
        workflow = WorkflowContext(
            user_id=user_id,
            workflow_type=WorkflowType.CONSULTATION_TO_DOCUMENT,
            source_module="ai_chat",
            target_module="document_generator",
            data={
                "conversation_id": conversation_id,
                "case_type": suggestion.get("case_type"),
                "document_type": suggestion.get("document_type"),
                "context": suggestion.get("context"),
            },
        )

        if user_id not in self._workflows:
            self._workflows[user_id] = []
        self._workflows[user_id].append(workflow)

        return workflow

    def get_pending_workflows(self, user_id: int) -> List[WorkflowContext]:
        """获取用户待完成的工作流"""
        return self._workflows.get(user_id, [])

    def complete_step(
        self,
        user_id: int,
        workflow_id: str,
        step: str,
        result: Dict[str, Any],
    ) -> bool:
        """完成工作流步骤"""
        workflows = self._workflows.get(user_id, [])
        for workflow in workflows:
            if str(id(workflow)) == workflow_id:
                workflow.completed_steps.append(step)
                workflow.data.update(result)
                return True
        return False


class ConsultationLawyerIntegration:
    """咨询到律师的联动服务"""

    # 需要转人工的信号
    REDIRECT_SIGNALS = [
        "金额较大", "超过10万", "复杂案件",
        "需要见面", "详细咨询", "正式委托",
        "诉讼代理", "刑事案件", "涉及犯罪",
    ]

    def __init__(self):
        self._referral_count: Dict[int, int] = {}  # user_id -> count

    def should_recommend_lawyer(
        self,
        conversation: List[Dict[str, str]],
        risk_level: str,
        confidence: str,
    ) -> Dict[str, Any]:
        """判断是否应该推荐律师

        Returns:
            {'recommended': bool, 'reason': str, 'lawyers': list}
        """
        # 检查高风险信号
        recent_message = ""
        for msg in reversed(conversation):
            if msg["role"] == "user":
                recent_message = msg["content"]
                break

        for signal in self.REDIRECT_SIGNALS:
            if signal in recent_message:
                return {
                    "recommended": True,
                    "reason": f"根据您的问题描述（{signal}），建议咨询专业律师获得更准确的服务",
                    "priority": "high",
                }

        # 高风险案件
        if risk_level in ["high", "medium_high"]:
            return {
                "recommended": True,
                "reason": "您的案件涉及较高风险，建议寻求专业律师帮助",
                "priority": "medium",
            }

        # 低置信度
        if confidence == "low":
            return {
                "recommended": True,
                "reason": "为确保建议的准确性，建议咨询专业律师",
                "priority": "low",
            }

        return {"recommended": False}

    async def get_recommended_lawyers(
        self,
        user_id: int,
        case_type: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """获取推荐的律师列表"""
        from ...services.mcp import execute_tool

        result = await execute_tool(
            tool_name="lawfirm_search",
            params={
                "action": "recommend",
                "case_type": case_type,
                "city": city,
                "limit": limit,
            },
            context={"user_id": user_id},
            user_id=user_id,
        )

        if result.success:
            if hasattr(result, 'data') and result.data:
                data = result.data
                if isinstance(data, dict) and "recommendations" in data:
                    return data["recommendations"]
        return []

    def track_referral(self, user_id: int) -> int:
        """记录律师推荐次数"""
        self._referral_count[user_id] = self._referral_count.get(
            user_id, 0) + 1
        return self._referral_count[user_id]


class NewsForumIntegration:
    """新闻到论坛的联动服务"""

    def create_discussion_from_news(
        self,
        news_id: int,
        news_title: str,
        news_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """基于新闻创建讨论帖建议"""
        return {
            "suggested": True,
            "title": f"讨论：{news_title}",
            "content_template": f"""近日，关于"{news_title}"的新闻引发了广泛关注。

{news_summary or '以下是相关报道摘要...'}

大家对这个看法？欢迎分享您的观点和经验。

#法律 #热点讨论""",
            "tags": ["新闻讨论", "法律热点"],
            "related_news_id": news_id,
        }


class ForumAIIntegration:
    """论坛到AI的联动服务

    实现从论坛帖子触发AI法律咨询的功能。
    当用户发布或浏览法律相关帖子时，推荐使用AI咨询获取初步建议。
    """

    # 需要AI咨询的法律问题类型
    LEGAL_QUESTION_PATTERNS = {
        "劳动纠纷": ["工资", "劳动合同", "解雇", "赔偿", "加班费", "社保", "工伤"],
        "婚姻家庭": ["离婚", "抚养费", "财产分割", "继承", "婚姻", "家庭暴力"],
        "合同纠纷": ["合同", "违约", "解除", "条款", "无效", "欺诈"],
        "房产纠纷": ["房产", "购房", "租房", "物业", "产权", "违约金"],
        "交通事故": ["交通事故", "责任", "赔偿", "肇事", "保险"],
        "债务纠纷": ["借款", "欠款", "贷款", "债务", "催收"],
        "消费维权": ["消费", "维权", "假货", "质量", "退款", "欺诈"],
        "刑事咨询": ["刑事", "拘留", "逮捕", "判刑", "辩护"],
    }

    # AI咨询建议关键词
    AI_SUGGESTION_TRIGGERS = [
        "怎么办", "怎么处理", "如何解决",
        "犯法吗", "违法吗", "有罪吗",
        "能告吗", "能起诉吗", "可以索赔吗",
        "需要什么证据", "怎么收集证据",
    ]

    def __init__(self):
        self._ai_referral_count: Dict[int, int] = {}  # user_id -> count

    def detect_ai_consultation_need(
        self,
        post_title: str,
        post_content: str,
    ) -> Optional[Dict[str, Any]]:
        """检测是否需要AI法律咨询

        Args:
            post_title: 帖子标题
            post_content: 帖子内容

        Returns:
            如果需要AI咨询，返回建议信息；否则返回None
        """
        combined_text = f"{post_title} {post_content}".lower()

        # 检查是否涉及法律问题
        detected_category = None
        for category, keywords in self.LEGAL_QUESTION_PATTERNS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    detected_category = category
                    break
            if detected_category:
                break

        # 如果没有识别到法律问题类别，检查是否包含AI咨询建议触发词
        if not detected_category:
            for trigger in self.AI_SUGGESTION_TRIGGERS:
                if trigger in combined_text:
                    return {
                        "suggested": True,
                        "category": "general",
                        "reason": "您的问题可能涉及法律纠纷，建议先咨询AI助手获取初步分析",
                        "quick_action": {
                            "label": "AI法律咨询",
                            "description": "快速获取专业法律建议",
                        },
                        "confidence": 0.7,
                    }
            return None

        # 构建AI咨询建议
        urgency_level = self._assess_urgency(combined_text)

        return {
            "suggested": True,
            "category": detected_category,
            "reason": f"您的帖子涉及{detected_category}相关问题，建议使用AI咨询获取初步法律建议",
            "quick_action": {
                "label": "咨询AI助手",
                "description": f"针对{detected_category}的智能分析",
            },
            "urgency": urgency_level,
            "confidence": 0.85,
        }

    def _assess_urgency(self, text: str) -> str:
        """评估问题的紧急程度"""
        urgent_keywords = [
            "紧急", "马上", "立即", " deadline", "截止",
            "明天", "今天", "尽快", "急",
        ]

        for keyword in urgent_keywords:
            if keyword in text:
                return "high"

        normal_keywords = ["以后", "以后再说", "不急"]
        for keyword in normal_keywords:
            if keyword in text:
                return "low"

        return "normal"

    def create_ai_consultation_link(
        self,
        post_id: int,
        suggestion: Dict[str, Any],
    ) -> Dict[str, Any]:
        """创建AI咨询快捷链接

        Args:
            post_id: 帖子ID
            suggestion: AI咨询建议

        Returns:
            快捷咨询链接信息
        """
        # 生成预填充的咨询内容
        prefill_content = f"""我在论坛发布了一个关于{suggestion.get('category', '法律')}的问题：

{suggestion.get('reason', '')}

请帮我分析：
1. 这个问题涉及哪些法律要点？
2. 我应该收集哪些证据？
3. 后续应该怎么处理？

谢谢！"""

        return {
            "action": "open_ai_chat",
            "prefill_content": prefill_content,
            "post_id": post_id,
            "category": suggestion.get("category"),
        }

    def track_ai_referral(self, user_id: int) -> int:
        """记录从论坛到AI咨询的转化"""
        if self._ai_referral_count is None:
            self._ai_referral_count = {}
        self._ai_referral_count[user_id] = self._ai_referral_count.get(
            user_id, 0) + 1
        return self._ai_referral_count[user_id]

    def get_ai_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户的论坛→AI转化统计"""
        return {
            "total_referrals": self._ai_referral_count.get(user_id, 0),
        }


class DocumentLawyerIntegration:
    """文书到律师的联动服务

    实现从法律文书生成后推荐匹配律师的功能。
    根据文书类型、案件类型、涉及的法律领域等维度推荐律师。
    """

    # 文书类型到律师专长的映射
    DOCUMENT_TYPE_TO_SPECIALTY = {
        "complaint": ["民事诉讼", "合同纠纷", "侵权纠纷"],
        "defense": ["民事诉讼", "合同纠纷", "公司法"],
        "agreement": ["合同法", "婚姻家庭", "劳动法"],
        "letter": ["公司法", "合同法", "知识产权"],
    }

    # 法律领域关键词映射
    LEGAL_FIELD_KEYWORDS = {
        "劳动法": ["劳动", "劳动合同", "工资", "解雇", "赔偿", "补偿", "社保"],
        "婚姻家庭": ["离婚", "抚养", "继承", "财产分割", "婚姻", "家庭"],
        "合同法": ["合同", "违约", "解除", "条款", "履行"],
        "公司法": ["公司", "股权", "股东", "法人", "经营"],
        "房产": ["房产", "房屋", "物业", "产权", "购房", "租房"],
        "知识产权": ["商标", "专利", "版权", "著作权", "侵权"],
        "刑事": ["犯罪", "刑事", "拘留", "逮捕", "判刑"],
    }

    def __init__(self):
        self._referral_cache: Dict[int, List[Dict[str, Any]]] = {}

    def analyze_document_for_lawyer_recommendation(
        self,
        document_type: str,
        case_type: str,
        document_content: str,
    ) -> Dict[str, Any]:
        """分析文书内容，为律师推荐提供依据

        Args:
            document_type: 文书类型 (complaint/defense/agreement/letter)
            case_type: 案件类型
            document_content: 文书内容

        Returns:
            推荐律师所需的分析结果
        """
        content_lower = document_content.lower()

        # 识别法律领域
        identified_fields = []
        for field, keywords in self.LEGAL_FIELD_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_lower:
                    identified_fields.append(field)
                    break

        # 如果没有识别到，使用默认的法律领域
        if not identified_fields:
            identified_fields = self.DOCUMENT_TYPE_TO_SPECIALTY.get(
                document_type, ["民事诉讼"])

        # 推断律师专长
        suggested_specialties = set()
        for field in identified_fields:
            suggested_specialties.add(field)
        for specialty in self.DOCUMENT_TYPE_TO_SPECIALTY.get(
                document_type, []):
            suggested_specialties.add(specialty)

        return {
            "document_type": document_type,
            "case_type": case_type,
            "identified_legal_fields": identified_fields,
            "suggested_specialties": list(suggested_specialties),
            "urgency": self._assess_urgency(document_content),
            "complexity": self._assess_complexity(document_content),
        }

    def _assess_urgency(self, content: str) -> str:
        """评估案件的紧急程度"""
        urgency_keywords = {
            "high": ["紧急", "立即", "马上", "时效", "过期", "截止"],
            "medium": ["尽快", "早日", "及时"],
        }

        for level, keywords in urgency_keywords.items():
            for keyword in keywords:
                if keyword in content:
                    return level

        return "normal"

    def _assess_complexity(self, content: str) -> str:
        """评估案件的复杂程度"""
        complexity_indicators = {
            "high": ["涉及多人", "多重法律关系", "跨国", "金额巨大"],
            "medium": ["金额较大", "时间较长", "多次纠纷"],
        }

        for level, keywords in complexity_indicators.items():
            for keyword in keywords:
                if keyword in content:
                    return level

        return "normal"

    async def get_recommended_lawyers(
        self,
        user_id: int,
        analysis_result: Dict[str, Any],
        city: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """根据文书分析结果推荐匹配的律师

        Args:
            user_id: 用户ID
            analysis_result: 文书分析结果
            city: 城市筛选
            limit: 返回数量限制

        Returns:
            推荐律师列表
        """
        from ...services.mcp import execute_tool

        specialties = analysis_result.get("suggested_specialties", [])
        case_type = analysis_result.get("case_type")

        result = await execute_tool(
            tool_name="lawfirm_search",
            params={
                "action": "recommend",
                "specialties": specialties,
                "case_type": case_type,
                "city": city,
                "limit": limit,
            },
            context={"user_id": user_id},
            user_id=user_id,
        )

        if result.success:
            recommendations = (result.data or {}).get("recommendations", [])

            # 缓存推荐结果
            if user_id not in self._referral_cache:
                self._referral_cache[user_id] = []
            self._referral_cache[user_id].extend(recommendations)

            return recommendations

        return []

    def create_lawyer_referral_suggestion(
        self,
        document_info: Dict[str, Any],
        lawyers: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """创建律师推荐建议

        Args:
            document_info: 文书信息
            lawyers: 推荐的律师列表

        Returns:
            推荐建议或None（无可推荐律师时）
        """
        if not lawyers:
            return None

        analysis = document_info.get("analysis", {})
        urgency = analysis.get("urgency", "normal")
        document_type = document_info.get("document_type", "文书")

        # 根据紧急程度调整建议文案
        urgency_messages = {
            "high": "您的文书涉及紧急事项，建议尽快咨询专业律师",
            "medium": "根据您的文书内容，建议咨询律师获取专业意见",
            "normal": "如果您需要律师协助，以下律师可能对您的案件有帮助",
        }

        return {
            "suggested": True,
            "message": urgency_messages.get(urgency, urgency_messages["normal"]),
            "document_type": document_type,
            "urgency": urgency,
            "lawyers": lawyers[:3],  # 只返回前3个
            "quick_action": {
                "label": "咨询律师",
                "description": "基于您的文书类型匹配",
            },
            "reason": f"根据您生成的{document_type}和案件特点推荐",
        }

    def get_referral_history(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的律师推荐历史"""
        return self._referral_cache.get(user_id, [])

    def track_lawyer_consultation_from_document(
        self,
        user_id: int,
        document_id: int,
        lawyer_id: int,
    ) -> bool:
        """跟踪从文书到律师咨询的转化

        Args:
            user_id: 用户ID
            document_id: 文书ID
            lawyer_id: 律师ID

        Returns:
            是否记录成功
        """
        # 可以在此记录转化数据，用于后续分析
        logger.info(
            f"Document to lawyer referral: user={user_id}, doc={document_id}, lawyer={lawyer_id}")
        return True


class ModuleIntegrationService:
    """模块联动服务总入口

    协调各模块之间的联动逻辑
    """

    def __init__(self):
        self.consultation_document = ConsultationDocumentIntegration()
        self.consultation_lawyer = ConsultationLawyerIntegration()
        self.news_forum = NewsForumIntegration()
        self.document_lawyer = DocumentLawyerIntegration()
        self.forum_ai = ForumAIIntegration()

    async def process_message(
        self,
        user_id: int,
        message: str,
        conversation: List[Dict[str, str]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """处理消息，检测是否需要模块联动

        Returns:
            {'action': str, 'data': dict}
            action: 'none' | 'suggest_document' | 'suggest_lawyer' | 'create_discussion'
        """
        # 检查是否需要生成文书
        doc_suggestion = self.consultation_document.suggest_document_generation(
            conversation)
        if doc_suggestion:
            return {
                "action": "suggest_document",
                "data": doc_suggestion,
            }

        # 检查是否需要推荐律师
        risk_level = context.get("risk_level", "low")
        confidence = context.get("confidence", "high")
        lawyer_check = self.consultation_lawyer.should_recommend_lawyer(
            conversation, risk_level, confidence
        )
        if lawyer_check.get("recommended"):
            # 获取推荐律师
            case_type = self.consultation_document.detect_document_intent(
                message)
            lawyers = await self.consultation_lawyer.get_recommended_lawyers(
                user_id=user_id,
                case_type=case_type.get("case_type") if case_type else None,
            )
            return {
                "action": "suggest_lawyer",
                "data": {
                    **lawyer_check,
                    "lawyers": lawyers,
                },
            }

        return {"action": "none", "data": {}}

    async def process_forum_post(
        self,
        user_id: int,
        post_id: int,
        post_title: str,
        post_content: str,
    ) -> Dict[str, Any]:
        """处理论坛帖子，检测是否需要AI咨询联动

        Args:
            user_id: 用户ID
            post_id: 帖子ID
            post_title: 帖子标题
            post_content: 帖子内容

        Returns:
            {'action': str, 'data': dict}
        """
        # 检测是否需要AI咨询
        ai_suggestion = self.forum_ai.detect_ai_consultation_need(
            post_title, post_content)
        if ai_suggestion:
            # 创建AI咨询链接
            ai_link = self.forum_ai.create_ai_consultation_link(
                post_id, ai_suggestion)

            # 记录转化
            self.forum_ai.track_ai_referral(user_id)

            return {
                "action": "suggest_ai_consultation",
                "data": {
                    **ai_suggestion,
                    "ai_link": ai_link,
                },
            }

        return {"action": "none", "data": {}}

    async def process_document_generation(
        self,
        user_id: int,
        document_type: str,
        case_type: str,
        document_content: str,
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        """处理文书生成后的联动逻辑

        在用户生成文书后，分析文书内容并推荐合适的律师

        Args:
            user_id: 用户ID
            document_type: 文书类型
            case_type: 案件类型
            document_content: 文书内容
            city: 城市筛选（可选）

        Returns:
            {'action': str, 'data': dict}
        """
        # 分析文书
        analysis = self.document_lawyer.analyze_document_for_lawyer_recommendation(
            document_type=document_type,
            case_type=case_type,
            document_content=document_content,
        )

        # 获取推荐律师
        lawyers = await self.document_lawyer.get_recommended_lawyers(
            user_id=user_id,
            analysis_result=analysis,
            city=city,
        )

        # 创建推荐建议
        document_info = {
            "document_type": document_type,
            "case_type": case_type,
            "analysis": analysis,
        }

        suggestion = self.document_lawyer.create_lawyer_referral_suggestion(
            document_info=document_info,
            lawyers=lawyers,
        )

        if suggestion:
            return {
                "action": "suggest_lawyer_after_document",
                "data": suggestion,
            }

        return {"action": "none", "data": {}}

    def get_integration_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户的模块联动统计"""
        workflows = self.consultation_document.get_pending_workflows(user_id)
        referral_count = self.consultation_lawyer._referral_count.get(
            user_id, 0) if self.consultation_lawyer._referral_count else 0
        document_referrals = len(
            self.document_lawyer.get_referral_history(user_id))
        forum_ai_referrals = self.forum_ai.get_ai_referral_stats(
            user_id).get("total_referrals", 0) if self.forum_ai else 0

        return {
            "pending_workflows": len(workflows),
            "lawyer_referrals": referral_count,
            "document_lawyer_referrals": document_referrals,
            "forum_ai_referrals": forum_ai_referrals,
            "completed_documents": sum(
                1 for w in workflows
                if "document_generated" in w.completed_steps
            ),
        }


# 单例
_integration_service: Optional[ModuleIntegrationService] = None


def get_integration_service() -> ModuleIntegrationService:
    """获取模块联动服务单例"""
    global _integration_service
    if _integration_service is None:
        _integration_service = ModuleIntegrationService()
    return _integration_service
