"""增强功能测试

测试新添加的后端功能组件。
"""
import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch


class TestCacheService:
    """测试缓存服务"""

    def test_lru_cache_set_and_get(self):
        """测试LRU缓存设置和获取"""
        from app.services.cache_service import (
            CacheService,
            _memory_cache,
            _MEMORY_CACHE_MAX_SIZE,
        )

        service = CacheService()

        asyncio.run(service.set("key1", "value1", expire=300))
        result = asyncio.run(service.get("key1"))

        assert result == "value1"

    def test_lru_cache_expiration(self):
        """测试缓存过期"""
        from app.services.cache_service import CacheService

        service = CacheService()

        asyncio.run(service.set("expiring", "value", expire=1))
        time.sleep(1.1)
        result = asyncio.run(service.get("expiring"))

        assert result is None

    def test_lru_cache_stats(self):
        """测试缓存统计"""
        from app.services.cache_service import CacheService

        service = CacheService()

        asyncio.run(service.set("key1", "value1", expire=300))
        asyncio.run(service.get("key1"))
        asyncio.run(service.get("nonexistent"))

        stats = service.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["total"] == 2

    def test_cache_reset_stats(self):
        """测试重置统计"""
        from app.services.cache_service import CacheService

        service = CacheService()

        asyncio.run(service.set("key1", "value1", expire=300))
        asyncio.run(service.get("key1"))

        service.reset_stats()
        stats = service.get_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0


class TestLogSanitizer:
    """测试日志脱敏"""

    def test_sanitize_password(self):
        """测试密码脱敏"""
        from app.core.middleware.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        result = sanitizer.sanitize_message('"password":"secret123"')

        assert "secret123" not in result
        assert "***" in result

    def test_sanitize_token(self):
        """测试令牌脱敏"""
        from app.core.middleware.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        result = sanitizer.sanitize_message('"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"')

        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_sanitize_dict(self):
        """测试字典脱敏"""
        from app.core.middleware.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        data = {
            "username": "testuser",
            "password": "secret",
            "email": "test@example.com",
        }

        result = sanitizer.sanitize_dict(data)

        assert result["username"] == "testuser"
        assert result["password"] == "***REDACTED***"
        assert result["email"] == "***REDACTED***"

    def test_sanitize_phone(self):
        """测试手机号脱敏"""
        from app.core.middleware.log_sanitizer import LogSanitizer

        sanitizer = LogSanitizer()
        result = sanitizer.sanitize_message('"phone":"13812345678"')

        assert "13812345678" not in result


class TestSecurityHeaders:
    """测试安全响应头"""

    def test_get_security_headers(self):
        """测试获取安全头"""
        from app.core.middleware.security_headers import get_security_headers

        headers = get_security_headers()

        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        assert "Content-Security-Policy" in headers

    def test_get_security_headers_csp_mode(self):
        """测试CSP模式"""
        from app.core.middleware.security_headers import get_security_headers

        strict_headers = get_security_headers(csp_mode="strict")
        relaxed_headers = get_security_headers(csp_mode="relaxed")

        assert "default-src" in strict_headers["Content-Security-Policy"]
        assert "frame-ancestors" in strict_headers["Content-Security-Policy"]


class TestHealthChecker:
    """测试健康检查"""

    @pytest.fixture
    def health_checker_available(self):
        """检查health模块是否可用"""
        try:
            from app.core.health import HealthChecker
            return True
        except ImportError:
            return False

    @pytest.mark.asyncio
    async def test_health_checker_init(self, health_checker_available):
        """测试健康检查器初始化"""
        if not health_checker_available:
            pytest.skip("health module not available")

        from app.core.health import HealthChecker

        checker = HealthChecker()
        assert checker is not None

    @pytest.mark.asyncio
    async def test_health_check_ai_service(self, health_checker_available):
        """测试AI服务检查"""
        if not health_checker_available:
            pytest.skip("health module not available")

        from app.core.health import HealthChecker

        checker = HealthChecker()
        result = await checker.check_ai_service()

        assert result.name == "ai_service"
        assert result.status in ["healthy", "degraded"]


class TestDatabasePoolMonitor:
    """测试数据库连接池监控"""

    def test_pool_monitor_init(self):
        """测试监控器初始化"""
        from app.core.monitoring.db_pool import DBPoolMonitor

        monitor = DBPoolMonitor()
        assert monitor is not None

    def test_get_stats(self):
        """测试获取统计"""
        from app.core.monitoring.db_pool import DBPoolMonitor

        monitor = DBPoolMonitor()
        stats = monitor.get_stats()

        # DBPoolMonitor返回字典格式
        assert isinstance(stats, dict)
        assert "total_queries" in stats
        assert "success_rate" in stats

    def test_get_recent_slow_queries(self):
        """测试获取最近慢查询"""
        from app.core.monitoring.db_pool import DBPoolMonitor

        monitor = DBPoolMonitor()
        # 先记录一个慢查询
        monitor.record_query(2.0, True, "SELECT * FROM users")
        slow_queries = monitor.get_recent_slow_queries()

        assert isinstance(slow_queries, list)


class TestMetrics:
    """测试指标收集"""

    @pytest.fixture
    def prometheus_available(self):
        """检查prometheus是否可用"""
        try:
            import prometheus_client
            return True
        except ImportError:
            return False

    def test_metrics_collector_init(self, prometheus_available):
        """测试指标收集器初始化"""
        if not prometheus_available:
            pytest.skip("prometheus_client not installed")

        from app.core.metrics import MetricsCollector

        collector = MetricsCollector()
        assert collector is not None

    def test_get_uptime(self, prometheus_available):
        """测试运行时间"""
        if not prometheus_available:
            pytest.skip("prometheus_client not installed")

        from app.core.metrics import MetricsCollector

        collector = MetricsCollector()
        time.sleep(0.1)
        uptime = collector.get_uptime_seconds()

        assert uptime >= 0.1

    def test_record_error(self, prometheus_available):
        """测试记录错误"""
        if not prometheus_available:
            pytest.skip("prometheus_client not installed")

        from app.core.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.record_error("/api/users", "validation_error")

        # Should not raise


class TestAlerting:
    """测试告警配置"""

    def test_generate_alert_rules(self):
        """测试生成告警规则"""
        from app.core.alerting import generate_alert_rules

        rules = generate_alert_rules()

        assert "groups" in rules
        assert len(rules["groups"]) > 0

    def test_get_alert_rules_summary(self):
        """测试获取告警规则摘要"""
        from app.core.alerting import get_alert_rules_summary

        summary = get_alert_rules_summary()

        assert "total_rules" in summary
        assert "by_severity" in summary
        assert summary["total_rules"] > 0

    def test_critical_rules_count(self):
        """测试严重级别规则数量"""
        from app.core.alerting import get_alert_rules_summary

        summary = get_alert_rules_summary()

        assert summary["by_severity"]["critical"] > 0


class TestSitemapCache:
    """测试Sitemap缓存"""

    def test_sitemap_cache_service_init(self):
        """测试Sitemap缓存服务初始化"""
        from app.services.sitemap_cache import SitemapCacheService

        service = SitemapCacheService()
        assert service is not None

    def test_get_stats(self):
        """测试获取统计"""
        from app.services.sitemap_cache import SitemapCacheService

        service = SitemapCacheService()
        stats = service.get_stats()

        assert "refresh_interval" in stats
        assert "auto_refresh_active" in stats
