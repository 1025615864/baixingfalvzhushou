import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.voice_manager import (
    VoiceProvider,
    VoiceProviderStatus,
    VoiceProviderHealth,
    VoiceManager,
    get_voice_manager,
)


class TestVoiceProvider:
    """测试语音提供商枚举"""

    def test_provider_values(self):
        """测试提供商枚举值"""
        assert VoiceProvider.AUTO.value == "auto"
        assert VoiceProvider.OPENAI.value == "openai"
        assert VoiceProvider.SHERPA.value == "sherpa"


class TestVoiceProviderStatus:
    """测试语音提供商状态枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        assert VoiceProviderStatus.AVAILABLE.value == "available"
        assert VoiceProviderStatus.UNAVAILABLE.value == "unavailable"
        assert VoiceProviderStatus.DEGRADED.value == "degraded"


class TestVoiceProviderHealth:
    """测试语音提供商健康状态"""

    def test_health_creation(self):
        """测试健康状态创建"""
        health = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.AVAILABLE,
            message="服务正常",
            last_check=1234567890.0,
            latency_ms=50.5,
        )

        assert health.provider == VoiceProvider.SHERPA
        assert health.status == VoiceProviderStatus.AVAILABLE
        assert health.message == "服务正常"
        assert health.latency_ms == 50.5


class TestVoiceManager:
    """测试语音管理器"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = VoiceManager()

    def test_init(self):
        """测试初始化"""
        assert self.manager._health_checks == {}
        assert self.manager._check_interval == 300.0
        assert self.manager._check_task is None

    def test_get_provider_health_empty(self):
        """测试空健康状态查询"""
        result = self.manager.get_provider_health(VoiceProvider.SHERPA)
        assert result is None

    def test_get_all_health_empty(self):
        """测试空全部健康状态"""
        result = self.manager.get_all_health()
        assert result == {}

    def test_get_available_providers_empty(self):
        """测试无可用提供商"""
        result = self.manager.get_available_providers()
        assert result == []

    def test_get_best_provider_no_available(self):
        """测试无提供商时的最佳选择"""
        result = self.manager.get_best_provider()
        assert result == VoiceProvider.OPENAI  # 默认回退

    def test_get_best_provider_with_preferred(self):
        """测试首选提供商优先级"""
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )

        result = self.manager.get_best_provider(preferred=VoiceProvider.SHERPA)
        assert result == VoiceProvider.SHERPA

    def test_get_best_provider_sherpa_priority(self):
        """测试Sherpa优先级最高"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )

        result = self.manager.get_best_provider()
        assert result == VoiceProvider.SHERPA

    def test_get_best_provider_only_openai(self):
        """测试只有OpenAI可用"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )

        result = self.manager.get_best_provider()
        assert result == VoiceProvider.OPENAI

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """测试启动和停止"""
        await self.manager.start()
        assert self.manager._check_task is not None

        await self.manager.stop()
        assert self.manager._check_task.done() or self.manager._check_task.cancelled()

    @pytest.mark.asyncio
    async def test_check_openai_with_key(self):
        """测试OpenAI密钥配置检查（有密钥）"""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"

        health = await self.manager._check_openai(mock_settings)

        assert health.provider == VoiceProvider.OPENAI
        assert health.status == VoiceProviderStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_check_openai_without_key(self):
        """测试OpenAI密钥配置检查（无密钥）"""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = ""

        health = await self.manager._check_openai(mock_settings)

        assert health.provider == VoiceProvider.OPENAI
        assert health.status == VoiceProviderStatus.UNAVAILABLE


class TestGetVoiceManager:
    """测试全局语音管理器获取"""

    def test_get_voice_manager_singleton(self):
        """测试单例模式"""
        manager1 = get_voice_manager()
        manager2 = get_voice_manager()
        assert manager1 is manager2

    def test_get_voice_manager_initial(self):
        """测试初始获取"""
        global _voice_manager
        _voice_manager = None

        manager = get_voice_manager()
        assert manager is not None
        assert isinstance(manager, VoiceManager)


class TestVoiceManagerHealthCheck:
    """测试语音管理器健康检查"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = VoiceManager()

    def test_get_provider_health_with_data(self):
        """测试有数据时的健康状态查询"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=100.5,
        )

        result = self.manager.get_provider_health(VoiceProvider.OPENAI)
        assert result is not None
        assert result.provider == VoiceProvider.OPENAI
        assert result.status == VoiceProviderStatus.AVAILABLE

    def test_get_all_health_with_data(self):
        """测试有数据时的全部健康状态"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.DEGRADED,
            message="连接超时",
            last_check=1234567890.0,
        )

        result = self.manager.get_all_health()
        assert len(result) == 2
        assert VoiceProvider.OPENAI in result
        assert VoiceProvider.SHERPA in result

    def test_get_available_providers_with_data(self):
        """测试有可用提供商时的返回"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.UNAVAILABLE,
            message="服务不可用",
            last_check=1234567890.0,
        )

        result = self.manager.get_available_providers()
        assert len(result) == 1
        assert VoiceProvider.OPENAI in result

    def test_get_best_provider_all_unavailable(self):
        """测试所有提供商都不可用"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.UNAVAILABLE,
            message="服务不可用",
            last_check=1234567890.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.UNAVAILABLE,
            message="服务不可用",
            last_check=1234567890.0,
        )

        result = self.manager.get_best_provider()
        assert result == VoiceProvider.OPENAI

    def test_get_best_provider_with_latency(self):
        """测试基于延迟的最佳提供商选择"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=200.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=50.0,
        )

        result = self.manager.get_best_provider()
        assert result == VoiceProvider.SHERPA


class TestVoiceProviderHealthDetail:
    """测试语音提供商健康状态详情"""

    def test_health_with_none_latency(self):
        """测试健康状态创建（无延迟）"""
        health = VoiceProviderHealth(
            provider=VoiceProvider.AUTO,
            status=VoiceProviderStatus.DEGRADED,
            message="部分功能不可用",
            last_check=9876543210.0,
            latency_ms=None,
        )

        assert health.provider == VoiceProvider.AUTO
        assert health.status == VoiceProviderStatus.DEGRADED
        assert health.latency_ms is None

    def test_health_equality(self):
        """测试健康状态相等性"""
        health1 = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=100.0,
        )
        health2 = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=100.0,
        )

        assert health1.provider == health2.provider
        assert health1.status == health2.status
        assert health1.message == health2.message


class TestVoiceManagerEdgeCases:
    """测试语音管理器边界情况"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = VoiceManager()

    def test_get_best_provider_preferred_unavailable(self):
        """测试首选提供商不可用时的回退"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )

        result = self.manager.get_best_provider(preferred=VoiceProvider.SHERPA)
        assert result == VoiceProvider.OPENAI

    def test_get_best_provider_preferred_available(self):
        """测试首选提供商可用时的优先级"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )

        result = self.manager.get_best_provider(preferred=VoiceProvider.SHERPA)
        assert result == VoiceProvider.SHERPA

    def test_get_provider_health_unknown_provider(self):
        """测试未知提供商的健康状态查询"""
        result = self.manager.get_provider_health(VoiceProvider.AUTO)
        assert result is None


class TestVoiceManagerAsyncMethods:
    """测试语音管理器异步方法"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = VoiceManager()

    @pytest.mark.asyncio
    async def test_check_sherpa_ready(self):
        """测试Sherpa服务就绪检查"""
        mock_settings = MagicMock()
        with patch("app.services.voice_manager.sherpa_is_ready", return_value=True):
            health = await self.manager._check_sherpa(mock_settings)
            assert health.provider == VoiceProvider.SHERPA
            assert health.status == VoiceProviderStatus.AVAILABLE
            assert "正常" in health.message

    @pytest.mark.asyncio
    async def test_check_sherpa_not_ready(self):
        """测试Sherpa服务未就绪检查"""
        mock_settings = MagicMock()
        with patch("app.services.voice_manager.sherpa_is_ready", return_value=False):
            health = await self.manager._check_sherpa(mock_settings)
            assert health.provider == VoiceProvider.SHERPA
            assert health.status == VoiceProviderStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_check_sherpa_exception(self):
        """测试Sherpa服务检查异常处理"""
        mock_settings = MagicMock()
        with patch("app.services.voice_manager.sherpa_is_ready", side_effect=Exception("Connection error")):
            health = await self.manager._check_sherpa(mock_settings)
            assert health.provider == VoiceProvider.SHERPA
            assert health.status == VoiceProviderStatus.UNAVAILABLE
            assert "失败" in health.message

    @pytest.mark.asyncio
    async def test_check_openai_with_whitespace_key(self):
        """测试OpenAI密钥配置检查（带空格密钥）"""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "  test-key  "
        health = await self.manager._check_openai(mock_settings)
        assert health.provider == VoiceProvider.OPENAI
        assert health.status == VoiceProviderStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_check_openai_with_none_key(self):
        """测试OpenAI密钥配置检查（None密钥）"""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        health = await self.manager._check_openai(mock_settings)
        assert health.provider == VoiceProvider.OPENAI
        assert health.status == VoiceProviderStatus.UNAVAILABLE


class TestVoiceManagerProviderSelection:
    """测试语音提供商选择逻辑"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = VoiceManager()

    def test_get_best_provider_all_available(self):
        """测试所有提供商都可用时选择最佳"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=100.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=50.0,
        )

        result = self.manager.get_best_provider()
        # Sherpa有更低的延迟，应该被选中
        assert result == VoiceProvider.SHERPA

    def test_get_best_provider_with_preferred_degraded(self):
        """测试首选提供商降级时的回退"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.DEGRADED,
            message="部分功能不可用",
            last_check=1234567890.0,
        )

        result = self.manager.get_best_provider(preferred=VoiceProvider.SHERPA)
        # Sherpa降级了，应该回退到OpenAI
        assert result == VoiceProvider.OPENAI

    def test_get_best_provider_only_sherpa(self):
        """测试只有Sherpa可用"""
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )

        result = self.manager.get_best_provider()
        assert result == VoiceProvider.SHERPA


class TestVoiceManagerInitialization:
    """测试语音管理器初始化"""

    def test_default_check_interval(self):
        """测试默认检查间隔"""
        manager = VoiceManager()
        assert manager._check_interval == 300.0  # 5分钟

    def test_initial_health_checks_empty(self):
        """测试初始健康检查为空"""
        manager = VoiceManager()
        assert manager._health_checks == {}
        assert manager._check_task is None

    def test_lock_initialized(self):
        """测试锁已初始化"""
        manager = VoiceManager()
        assert manager._lock is not None


class TestVoiceManagerProviderHealth:
    """测试语音提供商健康状态"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = VoiceManager()

    def test_get_provider_health_returns_correct_type(self):
        """测试获取提供商健康状态返回正确类型"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=100.0,
        )

        result = self.manager.get_provider_health(VoiceProvider.OPENAI)
        assert result is not None
        assert isinstance(result, VoiceProviderHealth)
        assert result.provider == VoiceProvider.OPENAI
        assert result.status == VoiceProviderStatus.AVAILABLE

    def test_get_all_health_returns_copy(self):
        """测试获取所有健康状态返回副本"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )

        result = self.manager.get_all_health()
        assert isinstance(result, dict)
        assert VoiceProvider.OPENAI in result

    def test_get_available_providers_with_mixed_status(self):
        """测试混合状态时获取可用提供商"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.UNAVAILABLE,
            message="不可用",
            last_check=1234567890.0,
        )

        result = self.manager.get_available_providers()
        assert len(result) == 1
        assert VoiceProvider.OPENAI in result
        assert VoiceProvider.SHERPA not in result

    def test_get_best_provider_with_latency_preference(self):
        """测试基于延迟的首选提供商"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=50.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=100.0,
        )

        result = self.manager.get_best_provider()
        # Sherpa优先级最高（本地服务更快），应该被选中
        assert result == VoiceProvider.SHERPA


class TestVoiceManagerProviderStatus:
    """测试语音提供商状态"""

    def test_status_enum_values(self):
        """测试状态枚举值"""
        assert VoiceProviderStatus.AVAILABLE.value == "available"
        assert VoiceProviderStatus.UNAVAILABLE.value == "unavailable"
        assert VoiceProviderStatus.DEGRADED.value == "degraded"

    def test_status_comparison(self):
        """测试状态比较"""
        assert VoiceProviderStatus.AVAILABLE == VoiceProviderStatus.AVAILABLE
        assert VoiceProviderStatus.AVAILABLE != VoiceProviderStatus.UNAVAILABLE


class TestVoiceManagerEdgeCases:
    """测试语音管理器边界情况"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = VoiceManager()

    def test_get_best_provider_with_empty_preferred(self):
        """测试首选为空时的最佳选择"""
        result = self.manager.get_best_provider(preferred=VoiceProvider.AUTO)
        # 没有可用提供商时，应该返回默认的OPENAI
        assert result == VoiceProvider.OPENAI

    def test_get_best_provider_with_degraded_only(self):
        """测试只有降级提供商时"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.DEGRADED,
            message="部分功能不可用",
            last_check=1234567890.0,
        )

        result = self.manager.get_best_provider()
        # 即使降级也应该返回
        assert result == VoiceProvider.OPENAI

    def test_get_provider_health_after_multiple_checks(self):
        """测试多次检查后的健康状态"""
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
            latency_ms=100.0,
        )
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.UNAVAILABLE,
            message="不可用",
            last_check=1234567890.1,
            latency_ms=None,
        )

        openai_health = self.manager.get_provider_health(VoiceProvider.OPENAI)
        sherpa_health = self.manager.get_provider_health(VoiceProvider.SHERPA)

        assert openai_health is not None
        assert openai_health.latency_ms == 100.0
        assert sherpa_health is not None
        assert sherpa_health.latency_ms is None


class TestVoiceManagerHealthCheckLoop:
    """测试语音管理器健康检查循环"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = VoiceManager()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_health_check_loop_normal(self):
        """测试健康检查循环正常执行"""
        # 由于 _health_check_loop 是无限循环，我们只测试它会被取消
        task = asyncio.create_task(self.manager._health_check_loop())
        
        # 等待一小段时间让它执行一次检查
        await asyncio.sleep(0.1)
        
        # 取消任务
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass  # 预期的行为

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_health_check_loop_exception(self):
        """测试健康检查循环异常处理"""
        mock_settings = MagicMock()
        
        with patch.object(self.manager, '_check_all_providers', side_effect=Exception("Test error")):
            # 创建任务并等待一小段时间
            task = asyncio.create_task(self.manager._health_check_loop())
            await asyncio.sleep(0.1)
            
            # 取消任务
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass  # 预期的行为

    @pytest.mark.asyncio
    async def test_check_all_providers(self):
        """测试检查所有提供商"""
        with patch.object(self.manager, '_check_sherpa', new_callable=AsyncMock) as mock_sherpa, \
             patch.object(self.manager, '_check_openai', new_callable=AsyncMock) as mock_openai:
            mock_sherpa.return_value = VoiceProviderHealth(
                provider=VoiceProvider.SHERPA,
                status=VoiceProviderStatus.AVAILABLE,
                message="正常",
                last_check=1234567890.0,
            )
            mock_openai.return_value = VoiceProviderHealth(
                provider=VoiceProvider.OPENAI,
                status=VoiceProviderStatus.AVAILABLE,
                message="正常",
                last_check=1234567890.0,
            )
            
            await self.manager._check_all_providers()
            
            assert VoiceProvider.SHERPA in self.manager._health_checks
            assert VoiceProvider.OPENAI in self.manager._health_checks


class TestVoiceManagerTranscribeFallback:
    """测试语音转写回退机制"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = VoiceManager()

    @pytest.mark.asyncio
    async def test_transcribe_with_fallback_sherpa_success(self):
        """测试Sherpa转写成功"""
        mock_settings = MagicMock()
        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock(scalar=MagicMock(return_value={"voice_transcribe_provider": "sherpa"}))
        
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )
        
        with patch("app.services.voice_manager.sherpa_transcribe", new_callable=AsyncMock) as mock_transcribe, \
             patch("app.services.voice_config_service.get_effective_voice_settings", new_callable=AsyncMock) as mock_settings_func:
            mock_transcribe.return_value = ("test text", None, None)
            mock_settings_func.return_value = (mock_settings, None, None)
            
            text, provider = await self.manager.transcribe_with_fallback(
                content=b"test",
                filename="test.wav",
                settings=mock_settings,
                db=mock_db,
            )
            
            assert text == "test text"
            assert provider == VoiceProvider.SHERPA

    @pytest.mark.asyncio
    async def test_transcribe_with_fallback_sherpa_fallback_openai(self):
        """测试Sherpa失败回退到OpenAI"""
        mock_settings = MagicMock()
        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock(scalar=MagicMock(return_value={"voice_transcribe_provider": "auto"}))
        
        self.manager._health_checks[VoiceProvider.SHERPA] = VoiceProviderHealth(
            provider=VoiceProvider.SHERPA,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )
        self.manager._health_checks[VoiceProvider.OPENAI] = VoiceProviderHealth(
            provider=VoiceProvider.OPENAI,
            status=VoiceProviderStatus.AVAILABLE,
            message="正常",
            last_check=1234567890.0,
        )
        
        with patch("app.services.voice_manager.sherpa_transcribe", side_effect=Exception("Sherpa failed")), \
             patch.object(self.manager, '_transcribe_with_openai', new_callable=AsyncMock) as mock_openai, \
             patch("app.services.voice_config_service.get_effective_voice_settings", new_callable=AsyncMock) as mock_settings_func:
            mock_openai.return_value = "test text from openai"
            mock_settings_func.return_value = (mock_settings, None, None)
            
            text, provider = await self.manager.transcribe_with_fallback(
                content=b"test",
                filename="test.wav",
                settings=mock_settings,
                db=mock_db,
            )
            
            assert text == "test text from openai"
            assert provider == VoiceProvider.OPENAI
