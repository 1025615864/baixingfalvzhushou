"""熔断器测试"""
import asyncio
import pytest
from app.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitConfig,
    CircuitState,
    get_circuit_breaker,
    circuit_breaker_registry,
)


class TestCircuitBreaker:
    """熔断器测试"""

    @pytest.fixture
    def circuit(self) -> CircuitBreaker:
        """创建测试熔断器"""
        config = CircuitConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=0.1,
        )
        return CircuitBreaker(name="test", config=config)

    @pytest.mark.asyncio
    async def test_closed_state_allows_calls(self, circuit: CircuitBreaker):
        """测试正常状态下允许调用"""
        async def success_func():
            return "success"

        result = await circuit.call(success_func)
        assert result == "success"
        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_opens_after_consecutive_failures(self, circuit: CircuitBreaker):
        """测试连续失败后打开熔断器"""
        async def fail_func():
            raise ValueError("fail")

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail_func)

        assert circuit.state == CircuitState.OPEN
        assert circuit.stats.consecutive_failures == 3

    @pytest.mark.asyncio
    async def test_rejects_calls_when_open(self, circuit: CircuitBreaker):
        """测试熔断器打开时拒绝调用"""
        async def fail_func():
            raise ValueError("fail")

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail_func)

        with pytest.raises(CircuitBreakerOpen):
            await circuit.call(fail_func)

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, circuit: CircuitBreaker):
        """测试超时后进入半开状态"""
        async def fail_func():
            raise ValueError("fail")

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail_func)

        assert circuit.state == CircuitState.OPEN

        await asyncio.sleep(0.15)

        async def dummy_func():
            return "test"

        await circuit.call(dummy_func)
        assert circuit.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_closes_after_success_in_half_open(self, circuit: CircuitBreaker):
        """测试半开状态下成功达到阈值后关闭熔断器"""
        async def fail_func():
            raise ValueError("fail")

        async def success_func():
            return "success"

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail_func)

        assert circuit.state == CircuitState.OPEN

        await asyncio.sleep(0.15)

        await circuit.call(success_func)
        assert circuit.state == CircuitState.HALF_OPEN

        await circuit.call(success_func)
        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_opens_again_on_failure_in_half_open(self, circuit: CircuitBreaker):
        """测试半开状态下失败后重新打开熔断器"""
        async def fail_func():
            raise ValueError("fail")

        async def success_func():
            return "success"

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail_func)

        await asyncio.sleep(0.15)

        async def dummy_func():
            return "test"

        await circuit.call(dummy_func)
        assert circuit.state == CircuitState.HALF_OPEN

        with pytest.raises(ValueError):
            await circuit.call(fail_func)

        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_fallback_called_when_open(self, circuit: CircuitBreaker):
        """测试熔断器打开时调用降级函数"""
        async def fail_func():
            raise ValueError("fail")

        fallback_called = False

        async def fallback(e: Exception | None = None):
            nonlocal fallback_called
            fallback_called = True
            return "fallback"

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail_func)

        await asyncio.sleep(0.15)

        result = await circuit.call_with_fallback(fail_func, fallback)
        assert result == "fallback"
        assert fallback_called

    @pytest.mark.asyncio
    async def test_sync_function_call(self, circuit: CircuitBreaker):
        """测试同步函数调用"""
        def sync_func():
            return "sync success"

        result = await circuit.call(sync_func)
        assert result == "sync success"

    @pytest.mark.asyncio
    async def test_get_stats(self, circuit: CircuitBreaker):
        """测试获取统计信息"""
        async def fail_func():
            raise ValueError("fail")

        async def success_func():
            return "success"

        await circuit.call(success_func)
        try:
            await circuit.call(fail_func)
        except ValueError:
            pass

        stats = circuit.get_stats()
        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["total_calls"] == 2
        assert stats["successful_calls"] == 1
        assert stats["failed_calls"] == 1

    @pytest.mark.asyncio
    async def test_reset(self, circuit: CircuitBreaker):
        """测试重置熔断器"""
        async def fail_func():
            raise ValueError("fail")

        for i in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail_func)

        assert circuit.state == CircuitState.OPEN

        circuit.reset()

        assert circuit.state == CircuitState.CLOSED
        assert circuit.stats.total_calls == 0
        assert circuit.stats.consecutive_failures == 0


class TestCircuitBreakerRegistry:
    """熔断器注册表测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        circuit_breaker_registry._breakers.clear()

    @pytest.mark.asyncio
    async def test_get_or_create(self):
        """测试获取或创建熔断器"""
        cb1 = await get_circuit_breaker("test1")
        cb2 = await get_circuit_breaker("test1")
        cb3 = await get_circuit_breaker("test2")

        assert cb1 is cb2
        assert cb1 is not cb3

    def test_get(self):
        """测试获取熔断器"""
        circuit_breaker_registry._breakers["test"] = CircuitBreaker(name="test")
        cb = circuit_breaker_registry.get("test")
        assert cb is not None
        assert cb.name == "test"

        cb_none = circuit_breaker_registry.get("nonexistent")
        assert cb_none is None

    def test_remove(self):
        """测试移除熔断器"""
        circuit_breaker_registry._breakers["test"] = CircuitBreaker(name="test")
        circuit_breaker_registry.remove("test")
        assert "test" not in circuit_breaker_registry._breakers

    def test_get_all_stats(self):
        """测试获取所有统计信息"""
        circuit_breaker_registry._breakers["test1"] = CircuitBreaker(name="test1")
        circuit_breaker_registry._breakers["test2"] = CircuitBreaker(name="test2")

        stats = circuit_breaker_registry.get_all_stats()
        assert len(stats) == 2


class TestCircuitConfig:
    """熔断器配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = CircuitConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout_seconds == 30.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = CircuitConfig(
            failure_threshold=10,
            success_threshold=3,
            timeout_seconds=60.0,
            expected_exception=IOError,
        )
        assert config.failure_threshold == 10
        assert config.success_threshold == 3
        assert config.timeout_seconds == 60.0
        assert config.expected_exception == IOError
