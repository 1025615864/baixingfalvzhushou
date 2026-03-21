"""新用户引导服务

提供角色选择、需求匹配、核心功能演示等新用户引导功能。
数据持久化到数据库。
"""
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.user_profile import UserOnboarding

logger = logging.getLogger(__name__)


class UserRole:
    """用户角色"""

    def __init__(self, db: AsyncSession):
        self._db = db

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

    async def select_role(
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

        # 从数据库获取或创建用户引导记录
        onboarding = await self._get_or_create_onboarding(user_id)
        
        # 更新角色信息
        onboarding.role_id = role_id
        onboarding.role_selected_at = datetime.now(timezone.utc)
        
        # 如果当前步骤小于角色选择步骤(1)，则更新步骤
        if onboarding.current_step < 1:
            onboarding.current_step = 1
        
        await self._db.commit()
        await self._db.refresh(onboarding)

        logger.info(f"User {user_id} selected role {role_id}")

        return {
            "success": True,
            "role_id": role_id,
            "selected_at": onboarding.role_selected_at.isoformat(),
        }

    async def get_user_role(self, user_id: int) -> dict[str, Any] | None:
        """获取用户角色

        Args:
            user_id: 用户ID

        Returns:
            用户角色信息
        """
        onboarding = await self._get_onboarding(user_id)
        if onboarding and onboarding.role_id:
            return {
                "user_id": user_id,
                "role_id": onboarding.role_id,
                "selected_at": onboarding.role_selected_at.isoformat() if onboarding.role_selected_at else None,
            }
        return None

    async def _get_onboarding(self, user_id: int) -> UserOnboarding | None:
        """获取用户引导记录"""
        result = await self._db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_onboarding(self, user_id: int) -> UserOnboarding:
        """获取或创建用户引导记录"""
        onboarding = await self._get_onboarding(user_id)
        if not onboarding:
            onboarding = UserOnboarding(user_id=user_id, current_step=0)
            self._db.add(onboarding)
            await self._db.flush()
        return onboarding


class NeedMatcher:
    """需求匹配器"""

    def __init__(self, db: AsyncSession):
        self._db = db

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

    async def match_needs(
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
        # 获取或创建用户引导记录
        onboarding = await self._get_or_create_onboarding(user_id)
        
        # 更新需求信息
        onboarding.matched_needs = need_ids
        onboarding.needs_matched_at = datetime.now(timezone.utc)
        
        # 如果当前步骤小于需求匹配步骤(2)，则更新步骤
        if onboarding.current_step < 2:
            onboarding.current_step = 2
        
        await self._db.commit()
        await self._db.refresh(onboarding)

        logger.info(f"User {user_id} matched needs: {need_ids}")

        return {
            "success": True,
            "need_ids": need_ids,
            "matched_count": len(need_ids),
        }

    async def _get_onboarding(self, user_id: int) -> UserOnboarding | None:
        """获取用户引导记录"""
        result = await self._db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_onboarding(self, user_id: int) -> UserOnboarding:
        """获取或创建用户引导记录"""
        onboarding = await self._get_onboarding(user_id)
        if not onboarding:
            onboarding = UserOnboarding(user_id=user_id, current_step=0)
            self._db.add(onboarding)
            await self._db.flush()
        return onboarding


class FeatureDemo:
    """功能演示"""

    def __init__(self, db: AsyncSession):
        self._db = db

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

    async def complete_demo(
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
        # 获取或创建用户引导记录
        onboarding = await self._get_or_create_onboarding(user_id)
        
        # 初始化已完成演示列表
        completed_list = onboarding.completed_demos or []
        
        # 添加新的已完成演示
        if demo_id not in completed_list:
            completed_list.append(demo_id)
            onboarding.completed_demos = completed_list
            
            # 如果是第一次完成演示，记录开始时间
            if not onboarding.demo_started_at:
                onboarding.demo_started_at = datetime.now(timezone.utc)
            
            # 如果当前步骤小于功能演示步骤(3)，则更新步骤
            if onboarding.current_step < 3:
                onboarding.current_step = 3
        
        await self._db.commit()
        await self._db.refresh(onboarding)

        logger.info(f"User {user_id} completed demo {demo_id}")

        return {
            "success": True,
            "demo_id": demo_id,
            "completed_count": len(completed_list),
        }

    async def get_completion_rate(self, user_id: int) -> dict[str, Any]:
        """获取完成率

        Args:
            user_id: 用户ID

        Returns:
            完成率信息
        """
        onboarding = await self._get_onboarding(user_id)
        if not onboarding or not onboarding.completed_demos:
            return {
                "completed": 0,
                "total": 3,
                "rate": 0,
            }

        completed = len(onboarding.completed_demos)

        return {
            "completed": completed,
            "total": 3,
            "rate": round(completed / 3 * 100, 2),
        }

    async def _get_onboarding(self, user_id: int) -> UserOnboarding | None:
        """获取用户引导记录"""
        result = await self._db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_onboarding(self, user_id: int) -> UserOnboarding:
        """获取或创建用户引导记录"""
        onboarding = await self._get_onboarding(user_id)
        if not onboarding:
            onboarding = UserOnboarding(user_id=user_id, current_step=0)
            self._db.add(onboarding)
            await self._db.flush()
        return onboarding


class OnboardingService:
    """引导服务"""

    def __init__(self, db: AsyncSession):
        self._db = db
        self.user_role = UserRole(db)
        self.need_matcher = NeedMatcher(db)
        self.feature_demo = FeatureDemo(db)

    async def start_onboarding(self, user_id: int) -> dict[str, Any]:
        """开始引导

        Args:
            user_id: 用户ID

        Returns:
            引导信息
        """
        # 从数据库获取用户引导记录
        result = await self._db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == user_id)
        )
        onboarding = result.scalar_one_or_none()

        current_step = 0
        if onboarding:
            current_step = onboarding.current_step

        # 根据当前步骤确定状态
        if onboarding and onboarding.completed:
            has_role = True
            current_step_name = "completed"
        elif onboarding and onboarding.role_id:
            has_role = True
            current_step_name = "need_matching"
        else:
            has_role = False
            current_step_name = "role_selection"

        return {
            "user_id": user_id,
            "has_role": has_role,
            "current_step": current_step_name,
            "current_step_value": current_step,
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
        # 获取或创建用户引导记录
        result = await self._db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == user_id)
        )
        onboarding = result.scalar_one_or_none()
        
        if not onboarding:
            onboarding = UserOnboarding(user_id=user_id, current_step=0)
            self._db.add(onboarding)
            await self._db.flush()

        if role_id:
            await self.user_role.select_role(user_id, role_id)

        if need_ids:
            await self.need_matcher.match_needs(user_id, need_ids)

        if demo_ids:
            for demo_id in demo_ids:
                await self.feature_demo.complete_demo(user_id, demo_id)

        completion_rate = await self.feature_demo.get_completion_rate(user_id)

        # 刷新获取最新数据
        await self._db.refresh(onboarding)
        
        # 检查是否完成整个引导流程
        if onboarding.role_id and onboarding.matched_needs and len(onboarding.completed_demos or []) >= 3:
            onboarding.completed = True
            onboarding.completed_at = datetime.now(timezone.utc)
            if onboarding.current_step < 4:
                onboarding.current_step = 4
            await self._db.commit()

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
        # 从数据库统计
        result = await self._db.execute(
            select(UserOnboarding)
        )
        all_onboardings = result.scalars().all()
        
        total_users = len(all_onboardings)
        completed_all = sum(
            1 for o in all_onboardings 
            if o.completed or (o.completed_demos and len(o.completed_demos) >= 3)
        )

        return {
            "total_users": total_users,
            "completed_all": completed_all,
            "completion_rate": round(completed_all / max(total_users, 1) * 100, 2),
        }


# ==================== 服务履约闭环相关 ====================

class ServiceCompletion:
    """服务履约闭环管理"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def track_service_progress(
        self,
        user_id: int,
        service_type: str,
        service_id: int,
        status: str,
    ) -> dict[str, Any]:
        """追踪服务进度

        Args:
            user_id: 用户ID
            service_type: 服务类型 (consultation/lawyer/contract等)
            service_id: 服务ID
            status: 服务状态 (pending/in_progress/completed/cancelled)

        Returns:
            追踪结果
        """
        # 获取或创建用户引导记录
        onboarding = await self._get_or_create_onboarding(user_id)
        
        # 初始化服务进度列表
        service_progress = onboarding.service_progress or {}
        
        # 更新服务进度
        if service_type not in service_progress:
            service_progress[service_type] = []
        
        # 查找是否已存在该服务记录
        existing_index = None
        for i, s in enumerate(service_progress[service_type]):
            if s.get('service_id') == service_id:
                existing_index = i
                break
        
        service_record = {
            'service_id': service_id,
            'status': status,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        
        if existing_index is not None:
            service_progress[service_type][existing_index] = service_record
        else:
            service_progress[service_type].append(service_record)
        
        onboarding.service_progress = service_progress
        await self._db.commit()
        await self._db.refresh(onboarding)

        logger.info(f"User {user_id} service progress updated: {service_type}/{service_id} -> {status}")

        return {
            "success": True,
            "service_type": service_type,
            "service_id": service_id,
            "status": status,
        }

    async def get_service_progress(
        self,
        user_id: int,
        service_type: str | None = None,
    ) -> dict[str, Any]:
        """获取服务进度

        Args:
            user_id: 用户ID
            service_type: 服务类型 (可选)

        Returns:
            服务进度信息
        """
        onboarding = await self._get_onboarding(user_id)
        if not onboarding or not onboarding.service_progress:
            return {
                "services": [],
                "summary": {
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "pending": 0,
                }
            }
        
        service_progress = onboarding.service_progress
        
        if service_type:
            services = service_progress.get(service_type, [])
        else:
            # 返回所有服务
            all_services = []
            for st, svcs in service_progress.items():
                for svc in svcs:
                    svc['service_type'] = st
                    all_services.append(svc)
            services = all_services
        
        # 统计各状态数量
        summary = {
            "total": len(services),
            "completed": sum(1 for s in services if s.get('status') == 'completed'),
            "in_progress": sum(1 for s in services if s.get('status') == 'in_progress'),
            "pending": sum(1 for s in services if s.get('status') == 'pending'),
        }
        
        return {
            "services": services,
            "summary": summary,
        }

    async def confirm_service_completion(
        self,
        user_id: int,
        service_type: str,
        service_id: int,
        rating: int | None = None,
        feedback: str | None = None,
    ) -> dict[str, Any]:
        """确认服务完成

        Args:
            user_id: 用户ID
            service_type: 服务类型
            service_id: 服务ID
            rating: 评分 (1-5)
            feedback: 反馈内容

        Returns:
            确认结果
        """
        # 更新服务进度为完成
        await self.track_service_progress(user_id, service_type, service_id, 'completed')
        
        # 获取或创建用户引导记录
        onboarding = await self._get_onboarding(user_id)
        
        # 初始化服务评价列表
        service_reviews = onboarding.service_reviews or []
        
        # 添加新评价
        review = {
            'service_type': service_type,
            'service_id': service_id,
            'rating': rating,
            'feedback': feedback,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        service_reviews.append(review)
        onboarding.service_reviews = service_reviews
        
        await self._db.commit()
        await self._db.refresh(onboarding)

        logger.info(f"User {user_id} confirmed service completion: {service_type}/{service_id}")

        return {
            "success": True,
            "service_type": service_type,
            "service_id": service_id,
            "rating": rating,
        }

    async def get_service_reviews(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        """获取服务评价

        Args:
            user_id: 用户ID

        Returns:
            服务评价列表
        """
        onboarding = await self._get_onboarding(user_id)
        if not onboarding or not onboarding.service_reviews:
            return {
                "reviews": [],
                "average_rating": 0,
            }
        
        reviews = onboarding.service_reviews
        
        # 计算平均评分
        ratings = [r.get('rating') for r in reviews if r.get('rating')]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        
        return {
            "reviews": reviews,
            "average_rating": round(average_rating, 1),
            "total_count": len(reviews),
        }

    async def _get_onboarding(self, user_id: int) -> UserOnboarding | None:
        """获取用户引导记录"""
        result = await self._db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_onboarding(self, user_id: int) -> UserOnboarding:
        """获取或创建用户引导记录"""
        onboarding = await self._get_onboarding(user_id)
        if not onboarding:
            onboarding = UserOnboarding(user_id=user_id, current_step=0)
            self._db.add(onboarding)
            await self._db.flush()
        return onboarding


# 便捷函数 - 需要传入 db session
async def get_onboarding_service(db: AsyncSession) -> OnboardingService:
    """获取 OnboardingService 实例

    Args:
        db: 数据库会话

    Returns:
        OnboardingService 实例
    """
    return OnboardingService(db)


async def start_onboarding(db: AsyncSession, user_id: int) -> dict[str, Any]:
    """便捷函数：开始引导

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        引导信息
    """
    service = OnboardingService(db)
    return await service.start_onboarding(user_id=user_id)


async def complete_onboarding(
    db: AsyncSession,
    user_id: int,
    role_id: str | None = None,
    need_ids: list[str] | None = None,
    demo_ids: list[str] | None = None,
) -> dict[str, Any]:
    """便捷函数：完成引导

    Args:
        db: 数据库会话
        user_id: 用户ID
        role_id: 角色ID
        need_ids: 需求ID列表
        demo_ids: 演示ID列表

    Returns:
        完成结果
    """
    service = OnboardingService(db)
    return await service.complete_onboarding(
        user_id=user_id,
        role_id=role_id,
        need_ids=need_ids,
        demo_ids=demo_ids,
    )


async def get_onboarding_stats(db: AsyncSession) -> dict[str, Any]:
    """便捷函数：获取引导统计

    Args:
        db: 数据库会话

    Returns:
        统计数据
    """
    service = OnboardingService(db)
    return await service.get_onboarding_stats()


async def track_service_progress(
    db: AsyncSession,
    user_id: int,
    service_type: str,
    service_id: int,
    status: str,
) -> dict[str, Any]:
    """便捷函数：追踪服务进度

    Args:
        db: 数据库会话
        user_id: 用户ID
        service_type: 服务类型
        service_id: 服务ID
        status: 服务状态

    Returns:
        追踪结果
    """
    service = ServiceCompletion(db)
    return await service.track_service_progress(user_id, service_type, service_id, status)


async def confirm_service_completion(
    db: AsyncSession,
    user_id: int,
    service_type: str,
    service_id: int,
    rating: int | None = None,
    feedback: str | None = None,
) -> dict[str, Any]:
    """便捷函数：确认服务完成

    Args:
        db: 数据库会话
        user_id: 用户ID
        service_type: 服务类型
        service_id: 服务ID
        rating: 评分
        feedback: 反馈

    Returns:
        确认结果
    """
    service = ServiceCompletion(db)
    return await service.confirm_service_completion(user_id, service_type, service_id, rating, feedback)