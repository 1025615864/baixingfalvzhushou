"""推荐系统冷启动服务

提供新用户引导和初始画像构建功能，解决推荐系统的冷启动问题。
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OnboardingQuestion:
    """引导问卷问题"""
    id: str
    question: str
    question_type: str  # single_choice, multiple_choice, slider
    options: List[Dict[str, Any]]
    required: bool = True
    category: str = "general"
    description: Optional[str] = None
    placeholder: Optional[str] = None


@dataclass
class UserInterestProfile:
    """用户兴趣画像"""
    user_id: int
    interest_tags: List[str] = field(default_factory=list)
    interest_weights: Dict[str, float] = field(default_factory=dict)
    preferred_content_types: List[str] = field(default_factory=list)
    usage_frequency: str = "unknown"  # often, sometimes, rarely
    consultation_history: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    onboarding_completed: bool = False


class ColdStartService:
    """冷启动服务"""

    # 引导问卷问题
    ONBOARDING_SURVEY: List[OnboardingQuestion] = [
        OnboardingQuestion(
            id="legal_need",
            question="您最关注哪类法律问题？（可多选）",
            question_type="multiple_choice",
            category="interests",
            options=[
                {"value": "labor_dispute", "label": "劳动纠纷",
                    "weight": 1.0, "icon": "💼"},
                {"value": "contract_dispute", "label": "合同纠纷",
                    "weight": 0.9, "icon": "📝"},
                {"value": "marriage_family", "label": "婚姻家庭",
                    "weight": 0.8, "icon": "👨‍👩‍👧"},
                {"value": "property_dispute", "label": "房产纠纷",
                    "weight": 0.7, "icon": "🏠"},
                {"value": "consumer_rights", "label": "消费维权",
                    "weight": 0.6, "icon": "🛒"},
                {"value": "traffic_accident", "label": "交通事故",
                    "weight": 0.5, "icon": "🚗"},
                {"value": "loan_dispute", "label": "借贷纠纷",
                    "weight": 0.5, "icon": "💰"},
                {"value": "criminal", "label": "刑事问题", "weight": 0.3, "icon": "⚖️"},
                {"value": "ip", "label": "知识产权", "weight": 0.4, "icon": "💡"},
                {"value": "other", "label": "其他", "weight": 0.5, "icon": "📌"},
            ],
            required=True,
        ),
        OnboardingQuestion(
            id="usage_frequency",
            question="您预计多久使用一次法律服务？",
            question_type="single_choice",
            category="behavior",
            options=[
                {"value": "often", "label": "经常（每月多次）", "weight": 1.0},
                {"value": "sometimes", "label": "偶尔（每月一次左右）", "weight": 0.6},
                {"value": "rarely", "label": "很少（偶尔需要时）", "weight": 0.3},
            ],
            required=True,
        ),
        OnboardingQuestion(
            id="preferred_service",
            question="您最常使用哪些功能？（可多选）",
            question_type="multiple_choice",
            category="preferences",
            options=[
                {"value": "ai_chat", "label": "AI 法律咨询", "weight": 1.0},
                {"value": "document_generator", "label": "文书生成", "weight": 0.8},
                {"value": "lawyer_consultation", "label": "律师咨询", "weight": 0.7},
                {"value": "news", "label": "法律资讯", "weight": 0.5},
                {"value": "forum", "label": "法律论坛", "weight": 0.4},
                {"value": "tools", "label": "法律工具（计算器等）", "weight": 0.6},
            ],
            required=False,
        ),
        OnboardingQuestion(
            id="experience_level",
            question="您的法律问题处理经验如何？",
            question_type="single_choice",
            category="profile",
            options=[
                {"value": "novice", "label": "完全新手，第一次处理", "weight": 1.0},
                {"value": "basic", "label": "有过一些了解或经历", "weight": 0.7},
                {"value": "experienced", "label": "比较熟悉流程", "weight": 0.4},
            ],
            required=True,
        ),
        OnboardingQuestion(
            id="location",
            question="您所在的城市（用于推荐本地律所）",
            question_type="single_choice",
            category="profile",
            options=[
                {"value": "beijing", "label": "北京", "weight": 1.0},
                {"value": "shanghai", "label": "上海", "weight": 1.0},
                {"value": "guangzhou", "label": "广州", "weight": 1.0},
                {"value": "shenzhen", "label": "深圳", "weight": 1.0},
                {"value": "hangzhou", "label": "杭州", "weight": 1.0},
                {"value": "chengdu", "label": "成都", "weight": 1.0},
                {"value": "wuhan", "label": "武汉", "weight": 1.0},
                {"value": "nanjing", "label": "南京", "weight": 1.0},
                {"value": "other", "label": "其他城市", "weight": 0.8},
            ],
            required=False,
        ),
        OnboardingQuestion(
            id="budget_range",
            question="您对法律服务的预算范围？",
            question_type="single_choice",
            category="behavior",
            options=[
                {"value": "free", "label": "主要使用免费服务", "weight": 1.0},
                {"value": "low", "label": "几百元以内", "weight": 0.8},
                {"value": "medium", "label": "几百到几千元", "weight": 0.6},
                {"value": "high", "label": "可以承担较高费用", "weight": 0.4},
            ],
            required=False,
        ),
    ]

    def __init__(self):
        self._profiles: Dict[int, UserInterestProfile] = {}

    def get_onboarding_survey(self) -> List[Dict[str, Any]]:
        """获取引导问卷"""
        return [
            {
                "id": q.id,
                "question": q.question,
                "type": q.question_type,
                "options": q.options,
                "required": q.required,
                "category": q.category,
                "description": q.description,
                "placeholder": q.placeholder,
            }
            for q in self.ONBOARDING_SURVEY
        ]

    def get_survey_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按分类获取问卷问题"""
        return [
            {
                "id": q.id,
                "question": q.question,
                "type": q.question_type,
                "options": q.options,
                "required": q.required,
            }
            for q in self.ONBOARDING_SURVEY
            if q.category == category
        ]

    def process_onboarding_answers(
        self,
        user_id: int,
        answers: Dict[str, Any],
    ) -> UserInterestProfile:
        """处理引导问卷答案，构建用户画像

        Args:
            user_id: 用户ID
            answers: 答案字典，key 为问题ID，value 为用户选择

        Returns:
            UserInterestProfile: 用户兴趣画像
        """
        profile = UserInterestProfile(user_id=user_id)

        for question in self.ONBOARDING_SURVEY:
            answer = answers.get(question.id)
            if not answer:
                if question.required:
                    logger.warning(f"用户 {user_id} 未回答必填问题: {question.id}")
                continue

            # 处理单选
            if question.question_type == "single_choice":
                option = self._find_option(question.options, answer)
                if option:
                    self._apply_answer_to_profile(
                        profile,
                        question.id,
                        answer,
                        option.get("weight", 1.0),
                        question.category,
                    )

            # 处理多选
            elif question.question_type == "multiple_choice":
                if isinstance(answer, list):
                    for value in answer:
                        option = self._find_option(question.options, value)
                        if option:
                            self._apply_answer_to_profile(
                                profile,
                                question.id,
                                value,
                                option.get("weight", 1.0),
                                question.category,
                            )

        profile.onboarding_completed = True
        profile.updated_at = datetime.now()

        # 保存画像
        self._profiles[user_id] = profile

        logger.info(f"用户 {user_id} 引导完成，兴趣标签: {profile.interest_tags}")

        return profile

    def _apply_answer_to_profile(
        self,
        profile: UserInterestProfile,
        question_id: str,
        answer_value: str,
        weight: float,
        category: str,
    ) -> None:
        """将答案应用到用户画像"""
        if category == "interests":
            # 法律需求标签
            if answer_value not in profile.interest_tags:
                profile.interest_tags.append(answer_value)
            profile.interest_weights[answer_value] = weight

        elif category == "behavior":
            if question_id == "usage_frequency":
                profile.usage_frequency = answer_value

        elif category == "preferences":
            if answer_value not in profile.preferred_content_types:
                profile.preferred_content_types.append(answer_value)

        elif category == "profile":
            # 可以存储到其他字段
            pass

    def _find_option(
        self,
        options: List[Dict[str, Any]],
        value: str,
    ) -> Optional[Dict[str, Any]]:
        """查找选项"""
        for opt in options:
            if opt.get("value") == value:
                return opt
        return None

    def get_user_profile(self, user_id: int) -> Optional[UserInterestProfile]:
        """获取用户画像"""
        return self._profiles.get(user_id)

    def update_profile_from_behavior(
        self,
        user_id: int,
        behavior_type: str,
        content_tags: List[str],
    ) -> Optional[UserInterestProfile]:
        """根据用户行为更新画像

        Args:
            user_id: 用户ID
            behavior_type: 行为类型（chat, document, lawyer, news, forum）
            content_tags: 内容标签列表
        """
        profile = self._profiles.get(user_id)
        if not profile:
            # 如果没有画像，创建一个
            profile = UserInterestProfile(user_id=user_id)
            self._profiles[user_id] = profile

        # 根据行为类型调整权重
        behavior_weights = {
            "chat": 0.8,
            "document": 0.9,
            "lawyer": 1.0,
            "news": 0.5,
            "forum": 0.6,
            "tool": 0.4,
        }

        base_weight = behavior_weights.get(behavior_type, 0.5)

        for tag in content_tags:
            current_weight = profile.interest_weights.get(tag, 0.5)
            # 累加权重，但不超过1.0
            new_weight = min(1.0, current_weight + base_weight * 0.1)
            profile.interest_weights[tag] = new_weight

            # 如果是新的兴趣标签，添加到列表
            if tag not in profile.interest_tags:
                profile.interest_tags.append(tag)

        profile.updated_at = datetime.now()

        return profile

    def get_recommendation_weights(self, user_id: int) -> Dict[str, float]:
        """获取推荐权重，用于个性化推荐"""
        profile = self._profiles.get(user_id)
        if not profile:
            # 返回默认权重
            return {
                "labor_dispute": 0.5,
                "contract_dispute": 0.5,
                "marriage_family": 0.5,
                "property_dispute": 0.5,
                "consumer_rights": 0.5,
                "traffic_accident": 0.5,
                "loan_dispute": 0.5,
            }

        # 返回用户兴趣权重
        weights = {}
        all_tags = [
            "labor_dispute",
            "contract_dispute",
            "marriage_family",
            "property_dispute",
            "consumer_rights",
            "traffic_accident",
            "loan_dispute",
        ]

        for tag in all_tags:
            weights[tag] = profile.interest_weights.get(tag, 0.3)

        return weights

    def should_show_onboarding(self, user_id: int) -> bool:
        """判断是否应该显示引导"""
        profile = self._profiles.get(user_id)
        if not profile:
            return True
        return not profile.onboarding_completed


_cold_start_service: ColdStartService | None = None


def get_cold_start_service() -> ColdStartService:
    """获取冷启动服务单例"""
    global _cold_start_service
    if _cold_start_service is None:
        _cold_start_service = ColdStartService()
    return _cold_start_service
