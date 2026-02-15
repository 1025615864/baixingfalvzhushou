"""支付幂等性中间件测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.core.middleware.payment_idempotency import (
    PaymentIdempotencyService,
    PaymentProvider,
    IdempotencyStatus,
    IdempotencyResult,
)


class TestPaymentProvider:
    """支付提供商测试类"""

    def test_provider_values(self):
        """测试支付提供商枚举值"""
        assert PaymentProvider.ALIPAY == "alipay"
        assert PaymentProvider.WECHAT == "wechat"
        assert PaymentProvider.IKUN == "ikun"


class TestIdempotencyStatus:
    """幂等性状态测试类"""

    def test_status_values(self):
        """测试幂等性状态枚举值"""
        assert IdempotencyStatus.PROCESSED == "processed"
        assert IdempotencyStatus.PROCESSING == "processing"
        assert IdempotencyStatus.FAILED == "failed"
        assert IdempotencyStatus.SKIPPED == "skipped"


class TestIdempotencyResult:
    """幂等性结果测试类"""

    def test_result_creation(self):
        """测试创建幂等性结果"""
        result = IdempotencyResult(
            status=IdempotencyStatus.PROCESSED,
            is_duplicate=False,
            lock_acquired=True,
            processing_time_ms=100.5,
            result={"order_id": "123"},
        )

        assert result.status == IdempotencyStatus.PROCESSED
        assert result.is_duplicate is False
        assert result.lock_acquired is True
        assert result.processing_time_ms == 100.5
        assert result.result == {"order_id": "123"}
        assert result.error_message is None

    def test_result_with_error(self):
        """测试创建幂等性结果（带错误）"""
        result = IdempotencyResult(
            status=IdempotencyStatus.FAILED,
            is_duplicate=False,
            lock_acquired=True,
            processing_time_ms=50.0,
            error_message="Processing failed",
        )

        assert result.status == IdempotencyStatus.FAILED
        assert result.error_message == "Processing failed"


class TestPaymentIdempotencyService:
    """支付幂等性服务测试类"""

    @pytest.fixture
    def mock_cache(self):
        """创建模拟缓存服务"""
        cache = AsyncMock()
        return cache

    def test_service_init(self):
        """测试服务初始化"""
        service = PaymentIdempotencyService()

        assert service.cache is not None
        assert service.lock_timeout == 60
        assert service.processed_ttl == 86400 * 7

    def test_service_init_custom_params(self):
        """测试服务初始化（自定义参数）"""
        cache = AsyncMock()
        service = PaymentIdempotencyService(
            cache=cache,
            lock_timeout=120,
            processed_ttl=86400,
        )

        assert service.cache is cache
        assert service.lock_timeout == 120
        assert service.processed_ttl == 86400

    @pytest.mark.asyncio
    async def test_generate_callback_hash(self, mock_cache):
        """测试生成回调哈希"""
        service = PaymentIdempotencyService(cache=mock_cache)

        data = {
            "order_no": "ORDER123",
            "provider": PaymentProvider.ALIPAY,
            "amount": "100.00",
        }

        # _generate_callback_hash 不是异步方法，使用相同的参数应该产生相同的哈希
        hash1 = service._generate_callback_hash("alipay", "ORDER123", data)
        hash2 = service._generate_callback_hash("alipay", "ORDER123", data)

        assert hash1 == hash2  # 相同输入应产生相同哈希

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, mock_cache):
        """测试获取锁（成功）"""
        mock_cache.acquire_lock.return_value = True
        service = PaymentIdempotencyService(cache=mock_cache)

        acquired = await service.acquire_lock("alipay", "ORDER123")

        assert acquired is True
        mock_cache.acquire_lock.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_lock_failure(self, mock_cache):
        """测试获取锁（失败）"""
        mock_cache.acquire_lock.return_value = False
        service = PaymentIdempotencyService(cache=mock_cache)

        acquired = await service.acquire_lock("alipay", "ORDER123")

        assert acquired is False

    @pytest.mark.asyncio
    async def test_release_lock(self, mock_cache):
        """测试释放锁"""
        service = PaymentIdempotencyService(cache=mock_cache)
        mock_cache.release_lock.return_value = True

        await service.release_lock("alipay", "ORDER123")

        mock_cache.release_lock.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_processed(self, mock_cache):
        """测试标记为已处理"""
        service = PaymentIdempotencyService(cache=mock_cache)
        mock_cache.set.return_value = True

        await service.mark_processed("alipay", "ORDER123", {"amount": 100.0})

        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_processed_true(self, mock_cache):
        """测试检查是否已处理（已处理）"""
        mock_cache.get.return_value = '{"test": "data"}'
        service = PaymentIdempotencyService(cache=mock_cache)

        is_processed = await service.is_processed("alipay", "ORDER123", {"amount": 100.0})

        assert is_processed is True

    @pytest.mark.asyncio
    async def test_is_processed_false(self, mock_cache):
        """测试检查是否已处理（未处理）"""
        mock_cache.get.return_value = None
        service = PaymentIdempotencyService(cache=mock_cache)

        is_processed = await service.is_processed("alipay", "ORDER123", {"amount": 100.0})

        assert is_processed is False

    @pytest.mark.asyncio
    async def test_process_callback_first_time(self, mock_cache):
        """测试处理回调（首次）"""
        async def mock_handler(provider: str, order_no: str, data: dict):
            return {"order_id": order_no, "status": "success"}

        mock_cache.acquire_lock.return_value = True
        mock_cache.set.return_value = True
        mock_cache.get.return_value = None  # 未处理
        mock_cache.release_lock.return_value = True
        service = PaymentIdempotencyService(cache=mock_cache)

        result = await service.process_callback(
            provider=PaymentProvider.ALIPAY,
            order_no="ORDER123",
            payload={"amount": "100.00"},
            handler=mock_handler,
        )

        assert result.status == IdempotencyStatus.PROCESSED
        assert result.is_duplicate is False
        assert result.lock_acquired is True
        assert result.result is not None

    @pytest.mark.asyncio
    async def test_process_callback_duplicate(self, mock_cache):
        """测试处理回调（重复）"""
        async def mock_handler(provider: str, order_no: str, data: dict):
            return {"order_id": order_no}

        # 模拟已处理的情况：get返回已处理的标记
        mock_cache.get.return_value = '{"test": "data"}'  # 已处理
        service = PaymentIdempotencyService(cache=mock_cache)

        result = await service.process_callback(
            provider=PaymentProvider.ALIPAY,
            order_no="ORDER123",
            payload={},
            handler=mock_handler,
        )

        assert result.status == IdempotencyStatus.SKIPPED  # 已处理应该返回SKIPPED
        assert result.is_duplicate is True

    @pytest.mark.asyncio
    async def test_process_callback_already_processed(self, mock_cache):
        """测试处理回调（已处理）"""
        async def mock_handler(provider: str, order_no: str, data: dict):
            return {"order_id": order_no}

        mock_cache.get.return_value = '{"test": "data"}'  # 已存在处理标记
        service = PaymentIdempotencyService(cache=mock_cache)

        result = await service.process_callback(
            provider=PaymentProvider.ALIPAY,
            order_no="ORDER123",
            payload={},
            handler=mock_handler,
        )

        assert result.status == IdempotencyStatus.SKIPPED
        assert result.is_duplicate is True

    @pytest.mark.asyncio
    async def test_process_callback_handler_exception(self, mock_cache):
        """测试处理回调（处理函数异常）"""
        async def mock_handler(provider: str, order_no: str, data: dict):
            raise ValueError("Handler error")

        mock_cache.acquire_lock.return_value = True
        mock_cache.get.return_value = None  # 未处理
        mock_cache.release_lock.return_value = True
        service = PaymentIdempotencyService(cache=mock_cache)

        result = await service.process_callback(
            provider=PaymentProvider.ALIPAY,
            order_no="ORDER123",
            payload={},
            handler=mock_handler,
        )

        assert result.status == IdempotencyStatus.FAILED
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_generate_lock_key(self, mock_cache):
        """测试生成锁键"""
        service = PaymentIdempotencyService(cache=mock_cache)

        key1 = service._get_lock_key("alipay", "ORDER123")
        key2 = service._get_lock_key("alipay", "ORDER123")

        assert key1 == key2
        assert "alipay" in key1
        assert "ORDER123" in key1

    @pytest.mark.asyncio
    async def test_generate_processed_key(self, mock_cache):
        """测试生成已处理键"""
        service = PaymentIdempotencyService(cache=mock_cache)

        key1 = service._get_processed_key("alipay", "ORDER123")
        key2 = service._get_processed_key("alipay", "ORDER123")

        assert key1 == key2
        assert "alipay" in key1
        assert "ORDER123" in key1

    @pytest.mark.asyncio
    async def test_cleanup_expired_records(self, mock_cache):
        """测试清理过期记录"""
        service = PaymentIdempotencyService(cache=mock_cache)
        # cleanup_expired_records方法不存在，移除此测试或改为测试get_stats
        stats = service.get_stats()

        assert "lock_timeout" in stats
        assert "processed_ttl" in stats