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
