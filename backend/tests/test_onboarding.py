import pytest
from app.services.onboarding import (
    UserRole,
    NeedMatcher,
    FeatureDemo,
    OnboardingService,
)

class TestUserRole:
    def test_get_available_roles(self):
        role_manager = UserRole()
        roles = role_manager.get_available_roles()
        assert len(roles) == 3
        ids = [r["id"] for r in roles]
        assert "individual" in ids
        assert "lawyer" in ids
        assert "enterprise" in ids

    def test_select_role_success(self):
        role_manager = UserRole()
        result = role_manager.select_role(user_id=1, role_id="lawyer")
        assert result["success"] is True
        assert result["role_id"] == "lawyer"
        
        user_role = role_manager.get_user_role(1)
        assert user_role["role_id"] == "lawyer"

    def test_select_role_invalid(self):
        role_manager = UserRole()
        result = role_manager.select_role(user_id=1, role_id="invalid")
        assert result["success"] is False
        assert result["error"] == "无效的角色ID"
        
        user_role = role_manager.get_user_role(1)
        assert user_role is None

class TestNeedMatcher:
    def test_get_need_options(self):
        matcher = NeedMatcher()
        # Individual
        opts_ind = matcher.get_need_options("individual")
        assert len(opts_ind) > 0
        assert any(o["id"] == "labor" for o in opts_ind)
        
        # Lawyer
        opts_law = matcher.get_need_options("lawyer")
        assert any(o["id"] == "civil" for o in opts_law)
        
        # Invalid
        opts_inv = matcher.get_need_options("invalid")
        assert opts_inv == []

    def test_match_needs(self):
        matcher = NeedMatcher()
        needs = ["labor", "contract"]
        result = matcher.match_needs(user_id=1, need_ids=needs)
        
        assert result["success"] is True
        assert result["matched_count"] == 2
        assert result["need_ids"] == needs

class TestFeatureDemo:
    def test_get_feature_demos(self):
        demo_manager = FeatureDemo()
        demos = demo_manager.get_feature_demos("individual")
        assert len(demos) == 3
        assert demos[0]["id"] == "consultation"

    def test_complete_demo_and_rate(self):
        demo_manager = FeatureDemo()
        user_id = 1
        
        # Initial rate
        rate0 = demo_manager.get_completion_rate(user_id)
        assert rate0["rate"] == 0
        
        # Complete one
        res1 = demo_manager.complete_demo(user_id, "consultation")
        assert res1["success"] is True
        assert res1["completed_count"] == 1
        
        rate1 = demo_manager.get_completion_rate(user_id)
        assert rate1["completed"] == 1
        # Total is hardcoded as 3 in implementation
        assert rate1["total"] == 3
        assert rate1["rate"] == 33.33
        
        # Complete same one again (should not increment)
        res2 = demo_manager.complete_demo(user_id, "consultation")
        assert res2["completed_count"] == 1
        
        # Complete others
        demo_manager.complete_demo(user_id, "document")
        demo_manager.complete_demo(user_id, "case")
        
        rate3 = demo_manager.get_completion_rate(user_id)
        assert rate3["completed"] == 3
        assert rate3["rate"] == 100.0

@pytest.mark.asyncio
class TestOnboardingService:
    async def test_start_onboarding_new_user(self):
        service = OnboardingService()
        result = await service.start_onboarding(user_id=1)
        
        assert result["user_id"] == 1
        assert result["has_role"] is False
        assert result["current_step"] == "role_selection"

    async def test_start_onboarding_existing_role(self):
        service = OnboardingService()
        service.user_role.select_role(user_id=1, role_id="lawyer")
        
        result = await service.start_onboarding(user_id=1)
        assert result["has_role"] is True
        assert result["current_step"] == "need_matching"

    async def test_complete_onboarding_full_flow(self):
        service = OnboardingService()
        user_id = 100
        
        result = await service.complete_onboarding(
            user_id=user_id,
            role_id="individual",
            need_ids=["labor"],
            demo_ids=["consultation", "document"]
        )
        
        assert result["success"] is True
        assert result["role_id"] == "individual"
        assert result["demo_completion"]["completed"] == 2
        
        # Verify state in subsystems
        assert service.user_role.get_user_role(user_id)["role_id"] == "individual"
        assert service.feature_demo.get_completion_rate(user_id)["completed"] == 2

    async def test_get_onboarding_stats(self):
        service = OnboardingService()
        
        # User 1: 3 demos (complete)
        await service.complete_onboarding(1, demo_ids=["a", "b", "c"]) 
        # Note: demo IDs don't have to be real in Current Implementation of complete_demo logic, 
        # it just counts distinct IDs.
        
        # User 2: 1 demo
        await service.complete_onboarding(2, demo_ids=["a"])
        
        # User 3: 0 demos
        # (Just initialized implicitly if we accessed it, but here we didn't add it to demos map)
        # Actually complete_onboarding with demo_ids=[] does not create entry in _demos unless demo_ids provided?
        # Let's check code: iterate demo_ids. If empty, loop doesn't run.
        # But get_completion_rate called at end checks if user_id not in _demos.
        
        stats = await service.get_onboarding_stats()
        # total_users = len(self.feature_demo._demos)
        # User 1 and User 2 are in _demos. 
        
        assert stats["total_users"] == 2
        assert stats["completed_all"] == 1  # Only User 1
        assert stats["completion_rate"] == 50.0


@pytest.mark.asyncio
class TestOnboardingPersistence:
    """Onboarding 数据持久化测试"""

    async def test_role_selection_persistence(self, db):
        """测试角色选择数据持久化"""
        from app.services.onboarding import UserRole
        from app.models.user_profile import UserOnboarding
        
        role_manager = UserRole(db)
        
        # 选择角色
        result = await role_manager.select_role(user_id=100, role_id="lawyer")
        assert result["success"] is True
        
        # 验证数据已持久化到数据库
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 100)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert onboarding.role_id == "lawyer"
        assert onboarding.role_selected_at is not None
        assert onboarding.current_step >= 1

    async def test_need_matching_persistence(self, db):
        """测试需求匹配数据持久化"""
        from app.services.onboarding import NeedMatcher
        from app.models.user_profile import UserOnboarding
        
        matcher = NeedMatcher(db)
        
        # 匹配需求
        result = await matcher.match_needs(user_id=101, need_ids=["labor", "contract"])
        assert result["success"] is True
        
        # 验证数据已持久化到数据库
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 101)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert onboarding.matched_needs == ["labor", "contract"]
        assert onboarding.needs_matched_at is not None
        assert onboarding.current_step >= 2

    async def test_demo_completion_persistence(self, db):
        """测试演示完成数据持久化"""
        from app.services.onboarding import FeatureDemo
        from app.models.user_profile import UserOnboarding
        
        demo_manager = FeatureDemo(db)
        
        # 完成演示
        result = await demo_manager.complete_demo(user_id=102, demo_id="consultation")
        assert result["success"] is True
        
        # 验证数据已持久化到数据库
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 102)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert onboarding.completed_demos == ["consultation"]
        assert onboarding.demo_started_at is not None
        assert onboarding.current_step >= 3

    async def test_multiple_demo_completions_persistence(self, db):
        """测试多个演示完成数据持久化"""
        from app.services.onboarding import FeatureDemo
        from app.models.user_profile import UserOnboarding
        
        demo_manager = FeatureDemo(db)
        
        # 完成多个演示
        await demo_manager.complete_demo(user_id=103, demo_id="consultation")
        await demo_manager.complete_demo(user_id=103, demo_id="document")
        await demo_manager.complete_demo(user_id=103, demo_id="case")
        
        # 验证数据已持久化到数据库
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 103)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert len(onboarding.completed_demos) == 3
        assert "consultation" in onboarding.completed_demos
        assert "document" in onboarding.completed_demos
        assert "case" in onboarding.completed_demos

    async def test_duplicate_demo_completion_idempotency(self, db):
        """测试重复完成演示的幂等性"""
        from app.services.onboarding import FeatureDemo
        from app.models.user_profile import UserOnboarding
        
        demo_manager = FeatureDemo(db)
        
        # 完成同一演示两次
        await demo_manager.complete_demo(user_id=104, demo_id="consultation")
        await demo_manager.complete_demo(user_id=104, demo_id="consultation")
        
        # 验证数据只记录一次
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 104)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert onboarding.completed_demos == ["consultation"]
        assert len(onboarding.completed_demos) == 1

    async def test_full_onboarding_flow_persistence(self, db):
        """测试完整引导流程数据持久化"""
        from app.services.onboarding import OnboardingService
        from app.models.user_profile import UserOnboarding
        
        service = OnboardingService(db)
        
        # 完成整个引导流程
        result = await service.complete_onboarding(
            user_id=105,
            role_id="individual",
            need_ids=["labor", "contract"],
            demo_ids=["consultation", "document", "case"]
        )
        
        assert result["success"] is True
        
        # 验证数据已持久化到数据库
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 105)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert onboarding.role_id == "individual"
        assert onboarding.matched_needs == ["labor", "contract"]
        assert len(onboarding.completed_demos) == 3
        assert onboarding.completed is True
        assert onboarding.completed_at is not None
        assert onboarding.current_step >= 4


class TestServiceRestartPersistence:
    """服务重启后数据持久化测试"""

    @pytest.mark.asyncio
    async def test_role_data_survives_service_restart(self, db):
        """测试角色数据在服务重启后不丢失"""
        from app.services.onboarding import UserRole
        from app.models.user_profile import UserOnboarding
        
        # 第一次服务实例：选择角色
        role_manager1 = UserRole(db)
        await role_manager1.select_role(user_id=200, role_id="enterprise")
        
        # 模拟服务重启：创建新的服务实例
        role_manager2 = UserRole(db)
        
        # 验证数据仍然存在
        user_role = await role_manager2.get_user_role(user_id=200)
        
        assert user_role is not None
        assert user_role["role_id"] == "enterprise"

    @pytest.mark.asyncio
    async def test_needs_data_survives_service_restart(self, db):
        """测试需求数据在服务重启后不丢失"""
        from app.services.onboarding import NeedMatcher
        from app.models.user_profile import UserOnboarding
        
        # 第一次服务实例：匹配需求
        matcher1 = NeedMatcher(db)
        await matcher1.match_needs(user_id=201, need_ids=["compliance", "contract"])
        
        # 模拟服务重启：创建新的服务实例
        matcher2 = NeedMatcher(db)
        
        # 验证数据仍然存在 - 通过查询数据库
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 201)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert onboarding.matched_needs == ["compliance", "contract"]

    @pytest.mark.asyncio
    async def test_demo_data_survives_service_restart(self, db):
        """测试演示数据在服务重启后不丢失"""
        from app.services.onboarding import FeatureDemo
        from app.models.user_profile import UserOnboarding
        
        # 第一次服务实例：完成演示
        demo_manager1 = FeatureDemo(db)
        await demo_manager1.complete_demo(user_id=202, demo_id="workbench")
        
        # 模拟服务重启：创建新的服务实例
        demo_manager2 = FeatureDemo(db)
        
        # 验证完成率仍然存在
        rate = await demo_manager2.get_completion_rate(user_id=202)
        
        assert rate["completed"] == 1
        assert rate["total"] == 3
        assert rate["rate"] == 33.33

    @pytest.mark.asyncio
    async def test_full_onboarding_data_survives_restart(self, db):
        """测试完整引导数据在服务重启后不丢失"""
        from app.services.onboarding import OnboardingService
        from app.models.user_profile import UserOnboarding
        
        # 第一次服务实例：完成引导
        service1 = OnboardingService(db)
        await service1.complete_onboarding(
            user_id=203,
            role_id="lawyer",
            need_ids=["civil", "commercial"],
            demo_ids=["workbench", "leads", "templates"]
        )
        
        # 模拟服务重启：创建新的服务实例
        service2 = OnboardingService(db)
        
        # 验证引导状态仍然存在
        onboarding_info = await service2.start_onboarding(user_id=203)
        
        assert onboarding_info["has_role"] is True
        assert onboarding_info["current_step"] == "completed"
        
        # 验证数据库记录
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 203)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert onboarding.role_id == "lawyer"
        assert onboarding.matched_needs == ["civil", "commercial"]
        assert len(onboarding.completed_demos) == 3
        assert onboarding.completed is True

    @pytest.mark.asyncio
    async def test_partial_onboarding_resumable_after_restart(self, db):
        """测试部分完成的引导在服务重启后可继续"""
        from app.services.onboarding import OnboardingService
        from app.models.user_profile import UserOnboarding
        
        # 第一次服务实例：只完成角色选择
        service1 = OnboardingService(db)
        await service1.complete_onboarding(
            user_id=204,
            role_id="individual",
            need_ids=None,  # 未完成需求匹配
            demo_ids=None   # 未完成演示
        )
        
        # 模拟服务重启：创建新的服务实例
        service2 = OnboardingService(db)
        
        # 验证可以继续进行下一步
        onboarding_info = await service2.start_onboarding(user_id=204)
        
        assert onboarding_info["has_role"] is True
        assert onboarding_info["current_step"] == "need_matching"
        
        # 继续完成需求匹配
        result = await service2.complete_onboarding(
            user_id=204,
            role_id=None,  # 已完成
            need_ids=["labor"],
            demo_ids=["consultation"]
        )
        
        assert result["success"] is True
        
        # 验证数据正确
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 204)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert onboarding.role_id == "individual"
        assert onboarding.matched_needs == ["labor"]
        assert onboarding.completed_demos == ["consultation"]


class TestServiceCompletionPersistence:
    """服务履约闭环持久化测试"""

    @pytest.mark.asyncio
    async def test_service_progress_tracking(self, db):
        """测试服务进度追踪持久化"""
        from app.services.onboarding import ServiceCompletion
        from app.models.user_profile import UserOnboarding
        
        service = ServiceCompletion(db)
        
        # 追踪服务进度
        result = await service.track_service_progress(
            user_id=300,
            service_type="consultation",
            service_id=1,
            status="in_progress"
        )
        
        assert result["success"] is True
        
        # 验证数据已持久化
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 300)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert onboarding.service_progress is not None
        assert "consultation" in onboarding.service_progress

    @pytest.mark.asyncio
    async def test_service_completion_with_rating(self, db):
        """测试服务完成评价持久化"""
        from app.services.onboarding import ServiceCompletion
        from app.models.user_profile import UserOnboarding
        
        service = ServiceCompletion(db)
        
        # 确认服务完成并评价
        result = await service.confirm_service_completion(
            user_id=301,
            service_type="lawyer",
            service_id=2,
            rating=5,
            feedback="非常满意"
        )
        
        assert result["success"] is True
        
        # 验证数据已持久化
        onboarding_result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == 301)
        )
        onboarding = onboarding_result.scalar_one_or_none()
        
        assert onboarding is not None
        assert onboarding.service_reviews is not None
        assert len(onboarding.service_reviews) == 1
        assert onboarding.service_reviews[0]["rating"] == 5
        assert onboarding.service_reviews[0]["feedback"] == "非常满意"

    @pytest.mark.asyncio
    async def test_service_progress_survives_restart(self, db):
        """测试服务进度在服务重启后不丢失"""
        from app.services.onboarding import ServiceCompletion
        
        # 第一次服务实例：更新进度
        service1 = ServiceCompletion(db)
        await service1.track_service_progress(
            user_id=302,
            service_type="contract",
            service_id=3,
            status="completed"
        )
        
        # 模拟服务重启：创建新的服务实例
        service2 = ServiceCompletion(db)
        
        # 验证进度仍然存在
        progress = await service2.get_service_progress(user_id=302)
        
        assert progress["summary"]["total"] == 1
        assert progress["summary"]["completed"] == 1
