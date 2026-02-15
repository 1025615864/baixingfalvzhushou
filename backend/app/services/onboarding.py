"""新用户引导服务

提供角色选择、需求匹配、核心功能演示等新用户引导功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class UserRole:
    """用户角色"""

    def __init__(self):
        self._roles: dict[str, dict[str, Any]] = {}
        self._user_roles: dict[int, dict[str, Any]] = {}

    def get_available_roles(self) -> list[dict[str, Any]]:
        """获取可用角色

        Returns:
            角色列表
        """
        return [
            {
                "id": "individual",
                "name": "个人用户",
                "description": "有法律咨询需求的个人用户",
                "icon": "person",
                "features": ["智能法律咨询", "文书生成", "案例检索"],
            },
            {
                "id": "lawyer",
                "name": "律师",
                "description": "执业律师，提供法律服务",
                "icon": "gavel",
                "features": ["案源线索", "工作台", "模板库"],
            },
            {
                "id": "enterprise",
                "name": "企业用户",
                "description": "企业法务、合规需求",
                "icon": "business",
                "features": ["合同审查", "合规管理", "团队协作"],
            },
        ]

    def select_role(
        self,
        user_id: int,
        role_id: str,
    ) -> dict[str, Any]:
        """选择角色

        Args:
            user_id: 用户ID
            role_id: 角色ID

        Returns:
            选择结果
        """
        available_roles = [r["id"] for r in self.get_available_roles()]

        if role_id not in available_roles:
            return {
                "success": False,
                "error": "无效的角色ID",
            }

        self._user_roles[user_id] = {
            "user_id": user_id,
            "role_id": role_id,
            "selected_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"User {user_id} selected role {role_id}")

        return {
            "success": True,
            "role_id": role_id,
            "selected_at": self._user_roles[user_id]["selected_at"],
        }

    def get_user_role(self, user_id: int) -> dict[str, Any] | None:
        """获取用户角色

        Args:
            user_id: 用户ID

        Returns:
            用户角色信息
        """
        return self._user_roles.get(user_id)


class NeedMatcher:
    """需求匹配器"""

    def __init__(self):
        self._needs: dict[int, dict[str, Any]] = {}

    def get_need_options(self, role_id: str) -> list[dict[str, Any]]:
        """获取需求选项

        Args:
            role_id: 角色ID

        Returns:
            需求选项列表
        """
        options = {
            "individual": [
                {"id": "labor", "name": "劳动纠纷", "icon": "work"},
                {"id": "divorce", "name": "婚姻家庭", "icon": "family"},
                {"id": "contract", "name": "合同纠纷", "icon": "description"},
                {"id": "debt", "name": "债权债务", "icon": "money"},
                {"id": "traffic", "name": "交通事故", "icon": "car"},
                {"id": "other", "name": "其他问题", "icon": "help"},
            ],
            "lawyer": [
                {"id": "civil", "name": "民事案件", "icon": "balance"},
                {"id": "commercial", "name": "商业法律", "icon": "business"},
                {"id": "corporate", "name": "公司法务", "icon": "corporate"},
                {"id": "ip", "name": "知识产权", "icon": "lightbulb"},
            ],
            "enterprise": [
                {"id": "compliance", "name": "合规审查", "icon": "verified"},
                {"id": "contract", "name": "合同管理", "icon": "description"},
                {"id": "labor", "name": "劳动用工", "icon": "people"},
                {"id": "risk", "name": "风险管理", "icon": "warning"},
            ],
        }

        return options.get(role_id, [])

    def match_needs(
        self,
        user_id: int,
        need_ids: list[str],
    ) -> dict[str, Any]:
        """匹配需求

        Args:
            user_id: 用户ID
            need_ids: 需求ID列表

        Returns:
            匹配结果
        """
        self._needs[user_id] = {
            "user_id": user_id,
            "need_ids": need_ids,
            "matched_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"User {user_id} matched needs: {need_ids}")

        return {
            "success": True,
            "need_ids": need_ids,
            "matched_count": len(need_ids),
        }


class FeatureDemo:
    """功能演示"""

    def __init__(self):
        self._demos: dict[int, dict[str, Any]] = {}

    def get_feature_demos(self, role_id: str) -> list[dict[str, Any]]:
        """获取功能演示

        Args:
            role_id: 角色ID

        Returns:
            功能演示列表
        """
        demos: dict[str, list[dict[str, Any]]] = {
            "individual": [
                {
                    "id": "consultation",
                    "title": "智能法律咨询",
                    "description": "输入您的法律问题，AI 助手为您提供专业解答",
                    "steps": [
                        "在输入框中描述您的问题",
                        "AI 自动分析并给出建议",
                        "如需深入咨询，可继续对话",
                    ],
                    "action": "开始咨询",
                },
                {
                    "id": "document",
                    "title": "文书生成",
                    "description": "根据您的需求自动生成法律文书",
                    "steps": [
                        "选择文书类型",
                        "填写必要信息",
                        "生成文书并可编辑",
                    ],
                    "action": "生成文书",
                },
                {
                    "id": "case",
                    "title": "案例检索",
                    "description": "查找相关法律案例作为参考",
                    "steps": [
                        "输入关键词",
                        "浏览检索结果",
                        "查看详情",
                    ],
                    "action": "检索案例",
                },
            ],
            "lawyer": [
                {
                    "id": "workbench",
                    "title": "律师工作台",
                    "description": "集中管理您的案件和任务",
                    "steps": [
                        "查看待办任务",
                        "管理案件进度",
                        "使用快捷工具",
                    ],
                    "action": "打开工作台",
                },
                {
                    "id": "leads",
                    "title": "案源线索",
                    "description": "获取潜在案源机会",
                    "steps": [
                        "浏览线索列表",
                        "查看详情并接单",
                        "跟进案件",
                    ],
                    "action": "查看线索",
                },
                {
                    "id": "templates",
                    "title": "模板库",
                    "description": "使用常用法律模板",
                    "steps": [
                        "搜索模板",
                        "选择并使用",
                        "编辑保存",
                    ],
                    "action": "使用模板",
                },
            ],
            "enterprise": [
                {
                    "id": "contract",
                    "title": "合同审查",
                    "description": "上传合同，AI 自动审查并给出建议",
                    "steps": [
                        "上传合同文件",
                        "等待 AI 分析",
                        "查看审查结果",
                    ],
                    "action": "开始审查",
                },
                {
                    "id": "compliance",
                    "title": "合规检查",
                    "description": "检查企业合规情况",
                    "steps": [
                        "选择检查项目",
                        "填写相关信息",
                        "获取检查报告",
                    ],
                    "action": "开始检查",
                },
            ],
        }

        return demos.get(role_id, [])

    def complete_demo(
        self,
        user_id: int,
        demo_id: str,
    ) -> dict[str, Any]:
        """完成演示

        Args:
            user_id: 用户ID
            demo_id: 演示ID

        Returns:
            完成结果
        """
        if user_id not in self._demos:
            self._demos[user_id] = {
                "user_id": user_id,
                "completed_demos": [],
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

        if demo_id not in self._demos[user_id]["completed_demos"]:
            self._demos[user_id]["completed_demos"].append(demo_id)

        logger.info(f"User {user_id} completed demo {demo_id}")

        return {
            "success": True,
            "demo_id": demo_id,
            "completed_count": len(self._demos[user_id]["completed_demos"]),
        }

    def get_completion_rate(self, user_id: int) -> dict[str, Any]:
        """获取完成率

        Args:
            user_id: 用户ID

        Returns:
            完成率信息
        """
        if user_id not in self._demos:
            return {
                "completed": 0,
                "total": 0,
                "rate": 0,
            }

        completed = len(self._demos[user_id]["completed_demos"])

        return {
            "completed": completed,
            "total": 3,
            "rate": round(completed / 3 * 100, 2),
        }


class OnboardingService:
    """引导服务"""

    def __init__(self):
        self.user_role = UserRole()
        self.need_matcher = NeedMatcher()
        self.feature_demo = FeatureDemo()

    async def start_onboarding(self, user_id: int) -> dict[str, Any]:
        """开始引导

        Args:
            user_id: 用户ID

        Returns:
            引导信息
        """
        current_role = self.user_role.get_user_role(user_id)

        return {
            "user_id": user_id,
            "has_role": current_role is not None,
            "current_step": "role_selection" if not current_role else "need_matching",
            "roles": self.user_role.get_available_roles(),
        }

    async def complete_onboarding(
        self,
        user_id: int,
        role_id: str | None = None,
        need_ids: list[str] | None = None,
        demo_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """完成引导

        Args:
            user_id: 用户ID
            role_id: 角色ID
            need_ids: 需求ID列表
            demo_ids: 演示ID列表

        Returns:
            完成结果
        """
        if role_id:
            self.user_role.select_role(user_id, role_id)

        if need_ids:
            self.need_matcher.match_needs(user_id, need_ids)

        if demo_ids:
            for demo_id in demo_ids:
                self.feature_demo.complete_demo(user_id, demo_id)

        completion_rate = self.feature_demo.get_completion_rate(user_id)

        logger.info(f"User {user_id} completed onboarding")

        return {
            "success": True,
            "user_id": user_id,
            "role_id": role_id,
            "need_ids": need_ids,
            "demo_completion": completion_rate,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_onboarding_stats(self) -> dict[str, Any]:
        """获取引导统计

        Returns:
            统计数据
        """
        total_users = len(self.feature_demo._demos)
        completed_all = sum(
            1 for d in self.feature_demo._demos.values()
            if len(d["completed_demos"]) >= 3
        )

        return {
            "total_users": total_users,
            "completed_all": completed_all,
            "completion_rate": round(completed_all / max(total_users, 1) * 100, 2),
        }


# 单例实例
onboarding_service = OnboardingService()


async def start_onboarding(user_id: int) -> dict[str, Any]:
    """便捷函数：开始引导

    Args:
        user_id: 用户ID

    Returns:
        引导信息
    """
    return await onboarding_service.start_onboarding(user_id=user_id)


async def complete_onboarding(
    user_id: int,
    role_id: str | None = None,
    need_ids: list[str] | None = None,
    demo_ids: list[str] | None = None,
) -> dict[str, Any]:
    """便捷函数：完成引导

    Args:
        user_id: 用户ID
        role_id: 角色ID
        need_ids: 需求ID列表
        demo_ids: 演示ID列表

    Returns:
        完成结果
    """
    return await onboarding_service.complete_onboarding(
        user_id=user_id,
        role_id=role_id,
        need_ids=need_ids,
        demo_ids=demo_ids,
    )


async def get_onboarding_stats() -> dict[str, Any]:
    """便捷函数：获取引导统计

    Returns:
        统计数据
    """
    return await onboarding_service.get_onboarding_stats()
