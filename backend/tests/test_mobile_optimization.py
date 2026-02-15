import pytest
from app.services.mobile_optimization import (
    DeviceDetector,
    ResponsiveLayout,
    TouchInteraction,
    MobileOptimizationService,
    optimize_for_device,
    register_touch
)

class TestDeviceDetector:
    @pytest.fixture
    def detector(self):
        return DeviceDetector()

    def test_detect_mobile(self, detector):
        ua = "Mozilla/5.0 (Linux; Android 10; SM-G960F)"
        info = detector.detect_device(ua)
        assert info["device_type"] == "mobile"
        assert info["is_mobile"] is True

    def test_detect_tablet(self, detector):
        ua = "Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X)"
        info = detector.detect_device(ua)
        # The logic is: if mobile/android in ua -> device_type=mobile
        # AND THEN if tablet/ipad in ua -> device_type=tablet
        # iPad UA often contains "Mobile" too?
        # But let's check code:
        # if "mobile" in ua or "android" in ua:
        #     type = "mobile"
        #     if "tablet" in ua or "ipad" in ua:
        #         type = "tablet"
        # else:
        #     type = "desktop"
        
        # iPad UA: "Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Mobile/15E148 Safari/604.1"
        # "Mobile" is present, so logic enters first block. Then "iPad" present -> "tablet".
        
        assert info["device_type"] == "tablet"

    def test_detect_desktop(self, detector):
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        info = detector.detect_device(ua)
        assert info["device_type"] == "desktop"
        assert info["is_mobile"] is False

    def test_get_screen_sizes(self, detector):
        assert detector.get_screen_sizes("mobile") == {"width": 375, "height": 667}
        assert detector.get_screen_sizes("unknown") == {"width": 1920, "height": 1080}


class TestResponsiveLayout:
    @pytest.fixture
    def layout(self):
        return ResponsiveLayout()

    def test_get_breakpoint(self, layout):
        assert layout.get_breakpoint(300) == "xs"
        assert layout.get_breakpoint(600) == "sm"
        assert layout.get_breakpoint(800) == "md"
        assert layout.get_breakpoint(1000) == "lg"
        assert layout.get_breakpoint(1300) == "xl"
        assert layout.get_breakpoint(2000) == "xxl"

    def test_get_layout_config(self, layout):
        config_xs = layout.get_layout_config("xs")
        assert config_xs["columns"] == 1
        
        config_xxl = layout.get_layout_config("xxl")
        assert config_xxl["columns"] == 6
        
        # Fallback
        config_unknown = layout.get_layout_config("unknown")
        assert config_unknown["columns"] == 3 # defaults to md


class TestTouchInteraction:
    @pytest.fixture
    def interaction(self):
        return TouchInteraction()

    def test_register_and_detect_tap(self, interaction):
        user_id = 1
        # Need at least 2 points for gesture
        interaction.register_touch(user_id, "start", 100, 100)
        interaction.register_touch(user_id, "end", 102, 102) # minimal movement
        
        gesture = interaction.detect_gesture(user_id)
        assert gesture["gesture"] == "tap"

    def test_detect_swipe_right(self, interaction):
        user_id = 2
        interaction.register_touch(user_id, "start", 100, 100)
        interaction.register_touch(user_id, "end", 200, 100) # delta_x +100
        
        gesture = interaction.detect_gesture(user_id)
        assert gesture["gesture"] == "swipe_right"

    def test_get_touch_stats(self, interaction):
        user_id = 3
        interaction.register_touch(user_id, "tap", 10, 10)
        
        stats = interaction.get_touch_stats(user_id)
        assert stats["total_touches"] == 1
        assert stats["touch_types"]["tap"] == 1


class TestMobileOptimizationService:
    @pytest.fixture
    def service(self):
        return MobileOptimizationService()

    @pytest.mark.asyncio
    async def test_optimize_for_device(self, service):
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)"
        res = await service.optimize_for_device(ua, 375)
        
        assert res["device_type"] == "mobile"
        assert res["breakpoint"] == "xs"
        assert res["layout_config"]["columns"] == 1

    @pytest.mark.asyncio
    async def test_register_touch(self, service):
        res = await service.register_touch(user_id=1, touch_type="start", x=10, y=10)
        assert res["success"] is True
        
        # Only one point, gesture unknown
        assert res["detected_gesture"] == "unknown"


@pytest.mark.asyncio
async def test_global_helper_functions():
    res1 = await optimize_for_device("Mozilla/5.0", 1920)
    assert res1["device_type"] == "desktop"
    
    res2 = await register_touch(999, "test", 0, 0)
    assert res2["success"] is True
