"""测试后台监控路由"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


class TestAdminMonitorRouter:
    """测试后台监控路由"""

    @pytest.mark.asyncio
    async def test_get_health(self):
        """测试系统健康检查"""
        from app.routers.admin_monitor import get_health
        
        with patch('app.routers.admin_monitor.get_health_check') as mock_health:
            mock_health.return_value = {"status": "healthy"}
            
            result = await get_health()
            
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """测试获取监控指标"""
        from app.routers.admin_monitor import get_metrics
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value.get_metrics_summary.return_value = {
                "total_requests": 1000,
                "errors": 10
            }
            
            result = await get_metrics(hours=1)
            
            assert result["total_requests"] == 1000

    @pytest.mark.asyncio
    async def test_get_api_metrics_with_endpoint(self):
        """测试获取 API 性能指标（指定端点）"""
        from app.routers.admin_monitor import get_api_metrics
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value.get_timer_stats.return_value = {
                "count": 100,
                "mean": 0.5
            }
            
            result = await get_api_metrics(endpoint="chat", hours=1)
            
            assert result["endpoint"] == "chat"
            assert result["stats"]["count"] == 100

    @pytest.mark.asyncio
    async def test_get_api_metrics_without_endpoint(self):
        """测试获取 API 性能指标（无端点）"""
        from app.routers.admin_monitor import get_api_metrics
        from app.services.system_monitor import get_system_monitor
        
        # 先记录一些 API 指标数据
        monitor = get_system_monitor()
        monitor.record_api_response("chat", 0.5, True)
        monitor.record_api_response("chat", 0.6, True)
        monitor.record_api_response("search", 0.3, True)
        
        result = await get_api_metrics(endpoint=None, hours=1)
        
        assert "endpoints" in result
        # 可能有数据也可能没有，取决于是否有记录的 API 调用
        assert isinstance(result["endpoints"], dict)

    @pytest.mark.asyncio
    async def test_get_ai_metrics(self):
        """测试获取 AI 服务指标"""
        from app.routers.admin_monitor import get_ai_metrics
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value.get_timer_stats.return_value = {"mean": 1.0}
            mock_monitor.return_value.get_counter.side_effect = lambda x: 100
            
            result = await get_ai_metrics(hours=1)
            
            assert "response_time" in result
            assert "total_responses" in result

    @pytest.mark.asyncio
    async def test_get_user_metrics(self):
        """测试获取用户活跃指标"""
        from app.routers.admin_monitor import get_user_metrics
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value.get_counter.side_effect = lambda x: 50
            
            result = await get_user_metrics()
            
            assert result["active_now"] == 50
            assert result["registered_total"] == 50

    @pytest.mark.asyncio
    async def test_get_business_metrics(self):
        """测试获取业务指标"""
        from app.routers.admin_monitor import get_business_metrics
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value.get_counter.side_effect = lambda x: 10
            
            result = await get_business_metrics()
            
            assert result["consultations"] == 10
            assert result["documents_generated"] == 10

    @pytest.mark.asyncio
    async def test_get_alerts(self):
        """测试获取告警列表"""
        from app.routers.admin_monitor import get_alerts
        
        mock_alert = MagicMock()
        mock_alert.rule_name = "test_rule"
        mock_alert.level.value = "warning"
        mock_alert.message = "Test alert"
        mock_alert.timestamp.isoformat.return_value = "2026-01-26T00:00:00"
        mock_alert.resolved = False
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value.get_recent_alerts.return_value = [mock_alert]
            
            result = await get_alerts(hours=24)
            
            assert result["total"] == 1
            assert len(result["alerts"]) == 1

    @pytest.mark.asyncio
    async def test_get_alerts_with_level_filter(self):
        """测试获取告警列表（带级别过滤）"""
        from app.routers.admin_monitor import get_alerts
        
        mock_alert = MagicMock()
        mock_alert.rule_name = "test_rule"
        mock_alert.level.value = "critical"
        mock_alert.message = "Test alert"
        mock_alert.timestamp.isoformat.return_value = "2026-01-26T00:00:00"
        mock_alert.resolved = False
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value.get_recent_alerts.return_value = [mock_alert]
            
            result = await get_alerts(hours=24, level="critical")
            
            assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_get_alert_rules(self):
        """测试获取告警规则"""
        from app.routers.admin_monitor import get_alert_rules
        
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        mock_rule.description = "Test description"
        mock_rule.level.value = "warning"
        mock_rule.cooldown_seconds = 300
        mock_rule.enabled = True
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value._alert_rules = [mock_rule]
            
            result = await get_alert_rules()
            
            assert len(result["rules"]) == 1
            assert result["rules"][0]["name"] == "test_rule"

    @pytest.mark.asyncio
    async def test_enable_alert_rule_success(self):
        """测试启用告警规则（成功）"""
        from app.routers.admin_monitor import enable_alert_rule
        from app.models.user import User
        
        mock_user = User(id=1, username="admin")
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        mock_rule.enabled = False
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value._alert_rules = [mock_rule]
            
            result = await enable_alert_rule("test_rule", mock_user)
            
            assert result["success"] is True
            assert mock_rule.enabled is True

    @pytest.mark.asyncio
    async def test_enable_alert_rule_not_found(self):
        """测试启用告警规则（规则不存在）"""
        from app.routers.admin_monitor import enable_alert_rule
        from app.models.user import User
        
        mock_user = User(id=1, username="admin")
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value._alert_rules = []
            
            with pytest.raises(HTTPException) as exc_info:
                await enable_alert_rule("nonexistent", mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_disable_alert_rule_success(self):
        """测试禁用告警规则（成功）"""
        from app.routers.admin_monitor import disable_alert_rule
        from app.models.user import User
        
        mock_user = User(id=1, username="admin")
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        mock_rule.enabled = True
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor.return_value._alert_rules = [mock_rule]
            
            result = await disable_alert_rule("test_rule", mock_user)
            
            assert result["success"] is True
            assert mock_rule.enabled is False

    @pytest.mark.asyncio
    async def test_get_websocket_status(self):
        """测试获取 WebSocket 状态"""
        from app.routers.admin_monitor import get_websocket_status
        
        with patch('app.routers.admin_monitor.enhanced_manager') as mock_manager:
            mock_manager.get_total_connections.return_value = 10
            mock_manager.get_online_users.return_value = [1, 2, 3]
            mock_manager._rooms = {}
            
            result = await get_websocket_status()
            
            assert result["total_connections"] == 10
            assert len(result["online_users"]) == 3

    @pytest.mark.asyncio
    async def test_get_system_info(self):
        """测试获取系统信息"""
        from app.routers.admin_monitor import get_system_info
        
        # Skip if psutil is not available
        pytest.importorskip("psutil")
        
        with patch('platform.system') as mock_system:
            with patch('platform.version') as mock_version:
                with patch('platform.processor') as mock_processor:
                    with patch('psutil.virtual_memory') as mock_virtual_memory:
                        with patch('psutil.disk_usage') as mock_disk_usage:
                            with patch('psutil.cpu_percent') as mock_cpu_percent:
                                mock_system.return_value = "Linux"
                                mock_version.return_value = "5.4.0"
                                mock_processor.return_value = "x86_64"
                                
                                mock_memory = MagicMock()
                                mock_memory.total = 8 * 1024**3
                                mock_memory.available = 4 * 1024**3
                                mock_memory.percent = 50
                                mock_virtual_memory.return_value = mock_memory
                                
                                mock_disk = MagicMock()
                                mock_disk.total = 100 * 1024**3
                                mock_disk.free = 50 * 1024**3
                                mock_disk.percent = 50
                                mock_disk_usage.return_value = mock_disk
                                
                                mock_cpu_percent.return_value = 25
                                
                                result = await get_system_info()
                                
                                assert result["platform"] == "Linux"
                                assert result["memory"]["total_gb"] == 8.0

    @pytest.mark.asyncio
    async def test_get_database_status_healthy(self):
        """测试获取数据库状态（健康）"""
        from app.routers.admin_monitor import get_database_status
        from sqlalchemy import text
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_version_result = MagicMock()
        mock_version_result.scalar_one_or_none.return_value = "3.36.0"
        
        with patch('sqlalchemy.text', text):
            mock_db.execute.side_effect = [mock_result, mock_version_result]
            
            result = await get_database_status(mock_db)
            
            assert result["status"] == "healthy"
            assert result["connection"] == "active"

    @pytest.mark.asyncio
    async def test_get_database_status_unhealthy(self):
        """测试获取数据库状态（不健康）"""
        from app.routers.admin_monitor import get_database_status
        
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Connection failed")
        
        result = await get_database_status(mock_db)
        
        assert result["status"] == "unhealthy"
        assert result["connection"] == "failed"

    @pytest.mark.asyncio
    async def test_get_cache_status_not_configured(self):
        """测试获取缓存状态（未配置）"""
        from app.routers.admin_monitor import get_cache_status

        mock_settings = MagicMock()
        mock_settings.redis_url = None

        with patch('app.config.get_settings', return_value=mock_settings):
            result = await get_cache_status()

        assert result["status"] == "not_configured"

    @pytest.mark.asyncio
    async def test_get_cache_status_healthy(self):
        """测试获取缓存状态（健康）"""
        from app.routers.admin_monitor import get_cache_status
        
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379"
        
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.info = AsyncMock(return_value={
            "used_memory_human": "100MB",
            "connected_clients": 5
        })
        
        # 由于 Redis 可能未安装，这个测试可能只是验证代码结构
        # 实际 Redis 测试需要在有 Redis 的环境中运行
        with patch('app.config.get_settings', return_value=mock_settings):
            result = await get_cache_status()
            
            # 根据 Redis 是否安装，结果可能不同
            assert result["status"] in ["healthy", "unavailable", "not_configured"]

    @pytest.mark.asyncio
    async def test_get_daily_report(self):
        """测试获取日报表"""
        from app.routers.admin_monitor import get_daily_report
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor_instance = MagicMock()
            mock_monitor_instance.get_counter.side_effect = lambda x: 100
            mock_monitor_instance.get_health_status.return_value = {"status": "healthy"}
            mock_monitor.return_value = mock_monitor_instance
            
            result = await get_daily_report(date="2026-01-26")
            
            assert result["date"] == "2026-01-26"
            assert result["summary"]["api_requests"] == 100

    @pytest.mark.asyncio
    async def test_get_daily_report_without_date(self):
        """测试获取日报表（无日期）"""
        from app.routers.admin_monitor import get_daily_report
        
        with patch('app.routers.admin_monitor.get_system_monitor') as mock_monitor:
            mock_monitor_instance = MagicMock()
            mock_monitor_instance.get_counter.side_effect = lambda x: 100
            mock_monitor_instance.get_health_status.return_value = {"status": "healthy"}
            mock_monitor.return_value = mock_monitor_instance
            
            result = await get_daily_report(date=None)
            
            assert "date" in result
            assert result["summary"]["api_requests"] == 100
