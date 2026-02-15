"""支付幂等性测试

测试支付回调幂等性保护功能。
"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock


class TestPaymentIdempotencyService:
    """测试支付幂等性服务"""

    @pytest.fixture
    def mock_cache(self):
        """模拟缓存服务"""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        cache.acquire_lock = AsyncMock(return_value=True)
        cache.release_lock = AsyncMock(return_value=True)
        return cache

    def test_service_initialization(self, mock_cache):
        """测试服务初始化"""
        from app.core.middleware.payment_idempotency import PaymentIdempotencyService

        service = PaymentIdempotencyService(cache=mock_cache)
        assert service.lock_timeout == 60
        assert service.processed_ttl == 86400 * 7

    @pytest.mark.asyncio
    async def test_is_processed_false(self, mock_cache):
        """测试未处理的回调"""
        from app.core.middleware.payment_idempotency import PaymentIdempotencyService

        service = PaymentIdempotencyService(cache=mock_cache)
        result = await service.is_processed("alipay", "ORDER123", {"amount": 100})
        assert result is False

    @pytest.mark.asyncio
    async def test_is_processed_true(self, mock_cache):
        """测试已处理的回调"""
        from app.core.middleware.payment_idempotency import PaymentIdempotencyService

        mock_cache.get = AsyncMock(return_value='{"hash": "abc123"}')

        service = PaymentIdempotencyService(cache=mock_cache)
        result = await service.is_processed("alipay", "ORDER123", {"amount": 100})
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, mock_cache):
        """测试获取锁成功"""
        from app.core.middleware.payment_idempotency import PaymentIdempotencyService

        mock_cache.acquire_lock = AsyncMock(return_value=True)

        service = PaymentIdempotencyService(cache=mock_cache)
        result = await service.acquire_lock("alipay", "ORDER123")
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_lock_fail(self, mock_cache):
        """测试获取锁失败"""
        from app.core.middleware.payment_idempotency import PaymentIdempotencyService

        mock_cache.acquire_lock = AsyncMock(return_value=False)

        service = PaymentIdempotencyService(cache=mock_cache)
        result = await service.acquire_lock("alipay", "ORDER123")
        assert result is False

    @pytest.mark.asyncio
    async def test_mark_processed(self, mock_cache):
        """测试标记已处理"""
        from app.core.middleware.payment_idempotency import PaymentIdempotencyService

        service = PaymentIdempotencyService(cache=mock_cache)
        await service.mark_processed("alipay", "ORDER123", {"amount": 100}, {"status": "success"})

        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_callback_success(self, mock_cache):
        """测试成功处理回调"""
        from app.core.middleware.payment_idempotency import (
            PaymentIdempotencyService,
            IdempotencyStatus,
        )

        service = PaymentIdempotencyService(cache=mock_cache)

        async def mock_handler(provider, order_no, payload):
            return {"status": "success"}

        result = await service.process_callback(
            "alipay", "ORDER123", {"amount": 100}, mock_handler
        )

        assert result.status == IdempotencyStatus.PROCESSED
        assert result.is_duplicate is False
        assert result.lock_acquired is True
        assert result.result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_process_callback_duplicate(self, mock_cache):
        """测试重复回调"""
        from app.core.middleware.payment_idempotency import (
            PaymentIdempotencyService,
            IdempotencyStatus,
        )

        mock_cache.get = AsyncMock(return_value='{"hash": "abc123"}')

        service = PaymentIdempotencyService(cache=mock_cache)

        async def mock_handler(provider, order_no, payload):
            return {"status": "success"}

        result = await service.process_callback(
            "alipay", "ORDER123", {"amount": 100}, mock_handler
        )

        assert result.status == IdempotencyStatus.SKIPPED
        assert result.is_duplicate is True

    @pytest.mark.asyncio
    async def test_process_callback_lock_failed(self, mock_cache):
        """测试获取锁失败"""
        from app.core.middleware.payment_idempotency import (
            PaymentIdempotencyService,
            IdempotencyStatus,
        )

        mock_cache.acquire_lock = AsyncMock(return_value=False)

        service = PaymentIdempotencyService(cache=mock_cache)

        async def mock_handler(provider, order_no, payload):
            return {"status": "success"}

        result = await service.process_callback(
            "alipay", "ORDER123", {"amount": 100}, mock_handler
        )

        assert result.status == IdempotencyStatus.PROCESSING
        assert result.lock_acquired is False

    def test_get_stats(self, mock_cache):
        """测试获取统计信息"""
        from app.core.middleware.payment_idempotency import PaymentIdempotencyService

        service = PaymentIdempotencyService(cache=mock_cache)
        stats = service.get_stats()

        assert "lock_timeout" in stats
        assert "processed_ttl" in stats
        assert stats["lock_timeout"] == 60


class TestPaymentProvider:
    """测试支付提供商枚举"""

    def test_provider_values(self):
        """测试提供商枚举值"""
        from app.core.middleware.payment_idempotency import PaymentProvider

        assert PaymentProvider.ALIPAY.value == "alipay"
        assert PaymentProvider.WECHAT.value == "wechat"
        assert PaymentProvider.IKUN.value == "ikun"


class TestIdempotencyStatus:
    """测试幂等性状态枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        from app.core.middleware.payment_idempotency import IdempotencyStatus

        assert IdempotencyStatus.PROCESSED.value == "processed"
        assert IdempotencyStatus.PROCESSING.value == "processing"
        assert IdempotencyStatus.FAILED.value == "failed"
        assert IdempotencyStatus.SKIPPED.value == "skipped"
