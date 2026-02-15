"""
测试辅助工具模块

提供测试数据工厂、Mock工具和断言辅助函数。
"""
from .test_data_factory import (
    TestDataFactory,
    UserFactory,
    OrderFactory,
    PaymentFactory,
    ConsultationFactory,
    PostFactory,
    NewsFactory,
)

from .mock_utils import (
    MockAsyncClient,
    MockCacheService,
    MockOpenAIClient,
    MockRedisClient,
    MockDatabaseSession,
    create_mock_service
)

from .assertion_helpers import (
    assert_response_success,
    assert_response_error,
    assert_coverage_increased,
    assert_pagination,
    assert_validation_error,
    assert_idempotency,
    assert_not_empty
)

__all__ = [
    # 数据工厂
    'TestDataFactory',
    'UserFactory',
    'OrderFactory',
    'PaymentFactory',
    'ConsultationFactory',
    'PostFactory',
    'NewsFactory',
    # Mock工具
    'MockAsyncClient',
    'MockCacheService',
    'MockOpenAIClient',
    'MockRedisClient',
    'MockDatabaseSession',
    'create_mock_service',
    # 断言助手
    'assert_response_success',
    'assert_response_error',
    'assert_coverage_increased',
    'assert_pagination',
    'assert_validation_error',
    'assert_idempotency',
    'assert_not_empty'
]