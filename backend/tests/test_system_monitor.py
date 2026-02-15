"""Tests for system monitor and alerts"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from app.services.system_monitor import (
    SystemMonitor,
    AlertRule,
    Alert,
    AlertLevel,
    get_system_monitor,
    record_api_metric,
    record_business_metric,
    get_health_check,
)


class TestSystemMonitor:
    """Test SystemMonitor class"""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance"""
        return SystemMonitor()

    def test_init(self, monitor):
        """Test monitor initialization"""
        assert monitor is not None
        assert len(monitor._alert_rules) > 0

    def test_inc_counter(self, monitor):
        """Test counter increment"""
        monitor.inc_counter("test_counter", 5)
        assert monitor.get_counter("test_counter") == 5

    def test_dec_counter(self, monitor):
        """Test counter decrement"""
        monitor.inc_counter("test_counter", 10)
        monitor.dec_counter("test_counter", 3)
        assert monitor.get_counter("test_counter") == 7

    def test_record_timer(self, monitor):
        """Test timer recording"""
        monitor.record_timer("api.test", 0.5)
        stats = monitor.get_timer_stats("api.test")
        assert stats["count"] == 1
        assert stats["sum"] == 0.5

    def test_record_timer_multiple(self, monitor):
        """Test multiple timer recordings"""
        for i in range(10):
            monitor.record_timer("api.test", 0.1 * (i + 1))
        stats = monitor.get_timer_stats("api.test")
        assert stats["count"] == 10
        assert round(stats["sum"], 1) == 5.5
        assert round(stats["p50"], 1) == 0.6  # values[5] = 0.6
        assert round(stats["p95"], 1) == 1.0  # values[9] = 1.0

    def test_get_timer_stats_empty(self, monitor):
        """Test getting stats for empty timer"""
        stats = monitor.get_timer_stats("api.empty")
        assert stats["count"] == 0
        assert stats["sum"] == 0

    def test_record_api_response_success(self, monitor):
        """Test recording successful API response"""
        monitor.record_api_response("/api/test", 0.1, True)
        stats = monitor.get_timer_stats("api./api/test")
        assert stats["count"] == 1
        assert monitor.get_counter("api./api/test.total") == 1
        assert monitor.get_counter("api./api/test.success") == 1

    def test_record_api_response_error(self, monitor):
        """Test recording failed API response"""
        monitor.record_api_response("/api/test", 0.5, False)
        assert monitor.get_counter("api./api/test.error") == 1

    def test_record_ai_response(self, monitor):
        """Test recording AI response"""
        monitor.record_ai_response(1.5, 100)
        stats = monitor.get_timer_stats("ai.response")
        assert stats["count"] == 1
        assert monitor.get_counter("ai.response.total") == 1
        assert monitor.get_counter("ai.response.tokens") == 100

    def test_record_user_action(self, monitor):
        """Test recording user action"""
        monitor.record_user_action("login", True)
        monitor.record_user_action("login", False)
        assert monitor.get_counter("user.action.login.success") == 1
        assert monitor.get_counter("user.action.login.failure") == 1

    def test_get_error_rate_zero(self, monitor):
        """Test error rate with no requests"""
        assert monitor.get_error_rate() == 0.0

    def test_get_error_rate_with_errors(self, monitor):
        """Test error rate calculation"""
        monitor.inc_counter("api.total", 100)
        monitor.inc_counter("api.error", 5)
        assert monitor.get_error_rate() == 0.05

    def test_get_p95_response_time(self, monitor):
        """Test P95 response time"""
        for i in range(100):
            monitor.record_timer("api.total", 0.1 + i * 0.01)
        p95 = monitor.get_p95_response_time()
        assert p95 > 0.9
        assert p95 < 1.1

    def test_get_queue_size(self, monitor):
        """Test queue size tracking"""
        monitor.inc_counter("queue.ai_response", 50)
        assert monitor.get_queue_size("ai_response") == 50

    def test_get_user_activity_spike(self, monitor):
        """Test user activity spike calculation"""
        monitor.inc_counter("user.active", 100)
        monitor.inc_counter("user.active.baseline", 50)
        assert monitor.get_user_activity_spike() == 2.0

    def test_get_user_activity_spike_no_baseline(self, monitor):
        """Test spike with no baseline"""
        monitor.inc_counter("user.active", 100)
        assert monitor.get_user_activity_spike() == 1.0

    def test_get_p99_response_time(self, monitor):
        """Test P99 response time"""
        for i in range(100):
            monitor.record_timer("api.total", 0.1 + i * 0.01)
        p99 = monitor.get_p99_response_time()
        assert p99 > 1.08
        assert p99 < 1.10

    def test_get_uptime_seconds(self, monitor):
        """Test uptime calculation"""
        time.sleep(0.1)
        uptime = monitor.get_uptime_seconds()
        assert uptime >= 0.1
        assert uptime < 1.0

    def test_add_alert_rule(self, monitor):
        """Test adding alert rule"""
        rule = AlertRule(
            name="test_rule",
            description="Test description",
            condition=lambda m: m.get_counter("test") > 10,
            level=AlertLevel.WARNING,
        )
        monitor.add_alert_rule(rule)
        assert len(monitor._alert_rules) > 5  # 5 default rules + 1 new

    def test_check_alerts(self, monitor):
        """Test checking alerts"""
        monitor.inc_counter("api.total", 100)
        monitor.inc_counter("api.error", 10)  # 10% error rate
        alerts = monitor.check_alerts()
        assert len(alerts) > 0

    def test_check_alerts_with_cooldown(self, monitor):
        """Test alert cooldown"""
        monitor.inc_counter("api.total", 100)
        monitor.inc_counter("api.error", 10)
        # First check should trigger alert
        alerts1 = monitor.check_alerts()
        assert len(alerts1) > 0
        # Second check should not trigger due to cooldown
        alerts2 = monitor.check_alerts()
        assert len(alerts2) == 0

    def test_check_alerts_disabled_rule(self, monitor):
        """Test disabled alert rule"""
        rule = AlertRule(
            name="disabled_rule",
            description="Disabled rule",
            condition=lambda m: True,
            level=AlertLevel.WARNING,
            enabled=False,
        )
        monitor.add_alert_rule(rule)
        alerts = monitor.check_alerts()
        # Disabled rule should not trigger
        assert all(a.rule_name != "disabled_rule" for a in alerts)

    def test_get_recent_alerts(self, monitor):
        """Test getting recent alerts"""
        monitor.inc_counter("api.total", 100)
        monitor.inc_counter("api.error", 10)
        alerts = monitor.check_alerts()
        recent = monitor.get_recent_alerts(hours=24)
        assert len(recent) == len(alerts)

    def test_get_recent_alerts_old(self, monitor):
        """Test filtering out old alerts"""
        old_alert = Alert(
            rule_name="old",
            level=AlertLevel.INFO,
            message="Old alert",
            timestamp=datetime.now(timezone.utc) - timedelta(hours=25)
        )
        monitor._alerts.append(old_alert)
        recent = monitor.get_recent_alerts(hours=24)
        assert len(recent) == 0

    def test_get_health_status_healthy(self, monitor):
        """Test healthy status"""
        monitor.inc_counter("api.total", 100)
        monitor.inc_counter("api.error", 0)
        for i in range(10):
            monitor.record_timer("api.total", 0.1)
        status = monitor.get_health_status()
        assert status["status"] == "healthy"
        assert status["score"] >= 80

    def test_get_health_status_degraded(self, monitor):
        """Test degraded status"""
        monitor.inc_counter("api.total", 100)
        monitor.inc_counter("api.error", 10)  # 10% error rate
        for i in range(10):
            monitor.record_timer("api.total", 3.0)  # Slow response
        status = monitor.get_health_status()
        assert status["status"] in ["degraded", "critical"]

    def test_get_health_status_critical(self, monitor):
        """Test critical status"""
        monitor.inc_counter("api.total", 100)
        monitor.inc_counter("api.error", 20)  # 20% error rate
        for i in range(10):
            monitor.record_timer("api.total", 10.0)  # Very slow
        status = monitor.get_health_status()
        assert status["status"] == "critical"

    def test_format_duration_seconds(self, monitor):
        """Test formatting seconds"""
        assert monitor._format_duration(30) == "30s"

    def test_format_duration_minutes(self, monitor):
        """Test formatting minutes"""
        assert monitor._format_duration(90) == "1m 30s"

    def test_format_duration_hours(self, monitor):
        """Test formatting hours"""
        assert monitor._format_duration(3660) == "1h 1m"

    def test_format_duration_days(self, monitor):
        """Test formatting days"""
        assert monitor._format_duration(90000) == "1d 1h"

    def test_get_metrics_summary(self, monitor):
        """Test metrics summary"""
        monitor.inc_counter("api.total", 100)
        monitor.inc_counter("ai.response.total", 50)
        monitor.inc_counter("user.active", 10)
        summary = monitor.get_metrics_summary()
        assert "health" in summary
        assert "api" in summary
        assert "ai" in summary
        assert "users" in summary
        assert "business" in summary


class TestAlertRules:
    """Test alert rule functionality"""

    @pytest.fixture
    def monitor(self):
        """Create monitor with data"""
        m = SystemMonitor()
        m.inc_counter("api.total", 100)
        m.inc_counter("api.error", 10)  # 10% error rate
        return m

    def test_high_error_rate_rule_exists(self):
        """Test that high error rate rule exists"""
        monitor = SystemMonitor()
        rule_names = [r.name for r in monitor._alert_rules]
        assert "high_error_rate" in rule_names

    def test_slow_response_rule_exists(self):
        """Test that slow response rule exists"""
        monitor = SystemMonitor()
        rule_names = [r.name for r in monitor._alert_rules]
        assert "slow_response" in rule_names

    def test_very_slow_response_rule_exists(self):
        """Test that very slow response rule exists"""
        monitor = SystemMonitor()
        rule_names = [r.name for r in monitor._alert_rules]
        assert "very_slow_response" in rule_names

    def test_alert_rule_evaluation_high_error(self, monitor):
        """Test alert rule evaluation for high error rate"""
        rule = AlertRule(
            name="test_high_error",
            description="Test rule",
            condition=lambda m: m.get_error_rate() > 0.05,
            level=AlertLevel.WARNING,
        )
        assert rule.condition(monitor) is True

    def test_alert_rule_evaluation_normal(self):
        """Test alert rule evaluation for normal state"""
        monitor = SystemMonitor()
        monitor.inc_counter("api.total", 100)
        monitor.inc_counter("api.error", 1)  # 1% error rate
        rule = AlertRule(
            name="test_high_error",
            description="Test rule",
            condition=lambda m: m.get_error_rate() > 0.05,
            level=AlertLevel.WARNING,
        )
        assert rule.condition(monitor) is False


class TestAlert:
    """Test Alert class"""

    def test_alert_creation(self):
        """Test alert creation"""
        alert = Alert(
            rule_name="test_rule",
            level=AlertLevel.WARNING,
            message="Test message"
        )
        assert alert.rule_name == "test_rule"
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "Test message"
        assert alert.resolved is False

    def test_alert_with_timestamp(self):
        """Test alert with custom timestamp"""
        custom_time = datetime.now(timezone.utc)
        alert = Alert(
            rule_name="test_rule",
            level=AlertLevel.ERROR,
            message="Test",
            timestamp=custom_time
        )
        assert alert.timestamp == custom_time


class TestAlertLevel:
    """Test AlertLevel enum"""

    def test_alert_level_values(self):
        """Test alert level values"""
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.ERROR.value == "error"
        assert AlertLevel.CRITICAL.value == "critical"


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_get_system_monitor_singleton(self):
        """Test system monitor singleton"""
        monitor1 = get_system_monitor()
        monitor2 = get_system_monitor()
        assert monitor1 is monitor2

    def test_record_api_metric(self):
        """Test recording API metric"""
        record_api_metric("/api/test", 0.5, True)
        monitor = get_system_monitor()
        assert monitor.get_counter("api./api/test.total") == 1

    def test_record_business_metric(self):
        """Test recording business metric"""
        record_business_metric("consultation", 5)
        monitor = get_system_monitor()
        assert monitor.get_counter("business.consultation") == 5

    def test_get_health_check(self):
        """Test getting health check"""
        health = get_health_check()
        assert "status" in health
        assert "score" in health
