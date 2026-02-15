# 测试辅助工具使用指南

本文档详细说明测试辅助工具的使用方法和最佳实践。

## 目录
- [快速开始](#快速开始)
- [数据工厂](#数据工厂)
- [Mock工具](#mock工具)
- [断言助手](#断言助手)
- [最佳实践](#最佳实践)
- [示例](#示例)

---

## 快速开始

### 安装导入

```python
from tests.helpers import (
    TestDataFactory,
    UserFactory,
    MockCacheService,
    MockOpenAIClient,
    assert_response_success,
    assert_not_empty,
)
```

### 基础示例

```python
import pytest
from tests.helpers import UserFactory, assert_response_success

@pytest.mark.asyncio
async def test_create_user():
    """创建用户的简单测试"""
    user_data = UserFactory.create_user_data()
    
    # 执行测试逻辑
    # result = await create_user(user_data)
    
    # 使用断言助手
    assert_not_empty(user_data["username"])
    # assert_response_success(result)
```

---

## 数据工厂

### TestDataFactory

统一的数据工厂类，提供便捷的数据创建方法。

#### 使用示例

```python
from tests.helpers import TestDataFactory

@pytest.mark.asyncio
async def test_with_data_factory(db_session):
    """使用数据工厂创建测试数据"""
    factory = TestDataFactory(db_session)
    
    # 创建用户
    user = await factory.create_user(username="testuser")
    
    # 创建订单
    order = await factory.create_order(user_id=user.id)
    
    # 创建咨询
    consultation = await factory.create_consultation(
        user_id=user.id,
        lawyer_id=1
    )
    
    # 测试完成后自动清理
    await factory.cleanup()
```

### 专用工厂类

#### UserFactory - 用户数据工厂

```python
from tests.helpers import UserFactory

# 创建用户数据字典
user_data = UserFactory.create_user_data(
    username="testuser",
    email="test@example.com",
    role="user"
)

# 创建数据库用户实例
user = await UserFactory.create_user(
    db=async_session,
    username="admin",
    role="admin"
)

# 创建管理员数据
admin_data = UserFactory.create_admin_data()
```

#### OrderFactory - 订单数据工厂

```python
from tests.helpers import OrderFactory

# 创建订单数据
order_data = OrderFactory.create_order_data(
    user_id=1,
    amount=Decimal("100.00"),
    provider="alipay",
    status="pending"
)

# 创建数据库订单
order = await OrderFactory.create_order(
    db=async_session,
    user_id=1,
    amount=Decimal("200.00")
)
```

#### PaymentFactory - 支付数据工厂

```python
from tests.helpers import PaymentFactory

# 创建支付宝回调数据
alipay_callback = PaymentFactory.create_callback_data(
    order_no="ORDER001",
    amount="100.00",
    status="success"
)

# 创建微信回调数据
wechat_callback = PaymentFactory.create_wechat_callback(
    order_no="ORDER002",
    total_fee="10000",
    code="SUCCESS"
)
```

#### ConsultationFactory - 咨询数据工厂

```python
from tests.helpers import ConsultationFactory

# 创建咨询数据
consultation_data = ConsultationFactory.create_consultation_data(
    user_id=1,
    lawyer_id=1,
    title="咨询标题",
    description="咨询内容"
)

# 创建数据库咨询实例
consultation = await ConsultationFactory.create_consultation(
    db=async_session,
    user_id=1,
    lawyer_id=1
)
```

#### ForumPostFactory - 论坛帖子工厂

```python
from tests.helpers import ForumPostFactory

# 创建帖子数据
post_data = ForumPostFactory.create_post_data(
    user_id=1,
    title="测试帖子",
    content="帖子内容",
    category="general"
)

# 创建数据库帖子实例
post = await ForumPostFactory.create_forum_post(
    db=async_session,
    user_id=1,
    title="测试帖子"
)
```

#### NewsFactory - 新闻数据工厂

```python
from tests.helpers import NewsFactory

# 创建新闻数据
news_data = NewsFactory.create_news_data(
    author_id=1,
    title="测试新闻",
    content="新闻内容",
    status="published"
)

# 创建数据库新闻文章
article = await NewsFactory.create_news_article(
    db=async_session,
    author_id=1,
    title="测试新闻"
)

# 创建新闻草稿
draft = await NewsFactory.create_news_draft(
    db=async_session,
    author_id=1
)
```

---

## Mock工具

### MockCacheService - Mock缓存服务

```python
from tests.helpers import MockCacheService

@pytest.fixture
def mock_cache():
    return MockCacheService()

@pytest.mark.asyncio
async def test_cache_operations(mock_cache):
    """测试缓存操作"""
    # 设置值
    await mock_cache.set("key1", "value1", expire=3600)
    
    # 获取值
    value = await mock_cache.get("key1")
    assert value == "value1"
    
    # 检查统计
    assert mock_cache.hits == 1
    
    # 检查不存在
    assert await mock_cache.get("nonexistent") is None
```

### MockRedisClient - Mock Redis客户端

```python
from tests.helpers import MockRedisClient

@pytest.fixture
def mock_redis():
    return MockRedisClient()

@pytest.mark.asyncio
async def test_redis_l(mock_redis: MockRedisClient):
    """测试Redis分布式锁"""
    # 获取锁
    acquired = await mock_redis.acquire_lock("lock_key", "value1", expire=60)
    assert acquired is True
    
    # 不能重复获取
    acquired_again = await mock_redis.acquire_lock("lock_key", "value2", expire=60)
    assert acquired_again is False
    
    # 释放锁
    await mock_redis.release_lock("lock_key", "value1")
    
    # 可以重新获取
    acquired = await mock_redis.acquire_lock("lock_key", "value3", expire=60)
    assert acquired is True
```

### MockOpenAIClient - Mock OpenAI客户端

```python
from tests.helpers import MockOpenAIClient

@pytest.fixture
def mock_openai():
    return MockOpenAIClient(mock_response="模拟AI回复")

@pytest.mark.asyncio
async def test_openai_chat(mock_openai: MockOpenAIClient):
    """测试OpenAI聊天"""
    messages = [
        {"role": "user", "content": "你好"}
    ]
    
    response = await mock_openai.chat(messages)
    
    assert response.content == "模拟AI回复"
    assert response.usage.prompt_tokens == 100
    assert response.usage.completion_tokens == 200
```

### MockAsyncClient - Mock HTTP客户端

```python
from tests.helpers import MockAsyncClient

@pytest.fixture
def mock_http():
    client = MockAsyncClient()
    client.responses = {
        "https://api.example.com/users": {"id": 1, "name": "Test User"},
        "https://api.example.com/orders": {"id": 1, "total": 100}
    }
    return client

@pytest.mark.asyncio
async def test_http_get(mock_http: MockAsyncClient):
    """测试HTTP GET"""
    response = await mock_http.get("https://api.example.com/users")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test User"
```

### create_mock_service - 创建Mock服务

```python
from tests.helpers import create_mock_service

# 创建缓存Mock
cache_mock = create_mock_service("cache")

# 创建Redis Mock
redis_mock = create_mock_service("redis")

# 创建OpenAI Mock
openai_mock = create_mock_service("openai", mock_response="回复")

# 创建HTTP Mock
http_mock = create_mock_service("http")
```

### patch_import - 导入补丁

```python
from tests.helpers import patch_import, MockCacheService

def test_with_import_patch():
    """使用导入补丁"""
    mock_cache = MockCacheService()
    
    with patch_import("app.services.cache_service", "get_cache_service", mock_cache):
        # 测试代码，get_cache_service将返回mock_cache
        pass
```

---

## 断言助手

### 通用断言

#### assert_not_empty - 非空断言

```python
from tests.helpers import assert_not_empty

def test_not_empty():
    data = "test_data"
    assert_not_empty(data)
    
    data = []
    # assert_not_empty(data)  # 会失败
```

#### assert_not_none - 非None断言

```python
from tests.helpers import assert_not_none

def test_not_none():
    data = {"key": "value"}
    assert_not_none(data)
    
    data = None
    # assert_not_none(data)  # 会失败
```

#### assert_equals - 相等断言

```python
from tests.helpers import assert_equals

def test_equals():
    actual = 100
    expected = 100
    assert_equals(actual, expected, "数量应该相等")
```

#### assert_dict_contains - 字典包含断言

```python
from tests.helpers import assert_dict_contains

def test_dict_contains():
    data = {"id": 1, "name": "test", "email": "test@example.com"}
    
    required_keys = ["id", "name", "email"]
    assert_dict_contains(data, required_keys, "响应应包含所有必需字段")
```

### HTTP响应断言

#### assert_response_success - 成功响应断言

```python
from tests.helpers import assert_response_success

def test_response_success():
    response_data = {
        "success": True,
        "message": "操作成功",
        "data": {"id": 1}
    }
    
    assert_response_success(
        response_data,
        message="操作成功",
        data_key="data"
    )
```

#### assert_response_error - 错误响应断言

```python
from tests.helpers import assert_response_error

def test_response_error():
    response_data = {
        "success": False,
        "message": "参数错误：用户名不能为空",
        "error_code": "INVALID_USERNAME"
    }
    
    assert_response_error(
        response_data,
        status_code=400,
        message_contains="参数错误",
        error_code="INVALID_USERNAME"
    )
```

#### assert_validation_error - 验证错误断言

```python
from tests.helpers import assert_validation_error

def test_validation_error():
    response_data = {
        "success": False,
        "message": "验证失败",
        "errors": ["email: 邮箱格式错误", "phone: 电话号码格式错误"]
    }
    
    assert_validation_error(
        response_data,
        field_names=["email", "phone"],
        message="字段验证应该失败"
    )
```

### 数据验证断言

#### assert_string_length - 字符串长度断言

```python
from tests.helpers import assert_string_length

def test_string_length():
    username = "testuser"
    
    assert_string_length(
        username,
        min_length=3,
        max_length=20,
        message="用户名长度应在3-20之间"
    )
```

#### assert_email_format - 邮箱格式断言

```python
from tests.helpers import assert_email_format

def test_email_format():
    assert_email_format("user@example.com")
    # assert_email_format("invalid-email")  # 会失败
```

#### assert_phone_format - 电话号码格式断言

```python
from tests.helpers import assert_phone_format

def test_phone_format():
    assert_phone_format("13800138000")
    # assert_phone_format("123")  # 会失败
```

### 状态码断言

#### assert_status_code - 状态码断言

```python
from tests.helpers import assert_status_code

def test_status_code():
    assert_status_code(200, [200, 201])  # 在范围内
    assert_status_code(200, 200)  # 等于
    # assert_status_code(200, 404)  # 会失败
```

#### assert_not_contains - 不包含断言

```python
from tests.helpers import assert_not_contains

def test_not_contains():
    data = ["item1", "item2", "item3"]
    assert_not_contains(data, "item4", "不应包含item4")
    
    string_data = "hello world"
    assert_not_contains(string_data, "python", "字符串不应包含python")
```

### 数据类型断言

#### assert_data_type - 数据类型断言

```python
from tests.helpers import assert_data_type

def test_data_type():
    assert_data_type(123, int, "数字应该是整数类型")
    assert_data_type("test", str, "字符串应该是字符串类型")
    assert_data_type([1, 2, 3], list, "应该是列表类型")
```

### 列表断言

#### assert_list_length - 列表长度断言

```python
from tests.helpers import assert_list_length

def test_list_length():
    items = [1, 2, 3, 4, 5]
    assert_list_length(items, 5, "列表应该有5个元素")
```

#### assert_list_sorted - 列表已排序断言

```python
from tests.helpers import assert_list_sorted

def test_list_sorted():
    numbers = [1, 2, 3, 4, 5]
    assert_list_sorted(numbers, reverse=False, message="列表应该是升序排列")
    
    data = [
        {"name": "A", "id": 1},
        {"name": "B", "id": 2},
        {"name": "C", "id": 3}
    ]
    assert_list_sorted(data, key="id", reverse=False)
```

### 分页断言

#### assert_pagination - 分页断言

```python
from tests.helpers import assert_pagination

def test_pagination():
    page = 2
    page_size = 10
    total = 25
    
    # 第2页最多10条数据
    data = [f"item_{i}" for i in range(11, 20)]
    
    assert_pagination(
        page=page,
        page_size=page_size,
        total=total,
        data=data,
        message="分页数据应该正确"
    )
```

### 日期断言

#### assert_timestamp_recent - 最近时间戳断言

```python
from tests.helpers import assert_timestamp_recent
from datetime import datetime, timedelta

def test_timestamp_recent():
    # 1分钟前的时间
    timestamp = datetime.now() - timedelta(minutes=1)
    
    assert_timestamp_recent(
        timestamp,
        max_age_seconds=3600,  # 1小时内
        message="时间戳应该是最近的"
    )
```

#### assert_datetime_between - 日期范围断言

```python
from tests.helpers import assert_datetime_between
from datetime import datetime

def test_datetime_between():
    dt = datetime(2024, 1, 15)
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31)
    
    assert_datetime_between(
        dt=dt,
        start=start,
        end=end,
        message="日期应该在指定范围内"
    )
```

### Mock调用断言

#### assert_async_called_with - Mock调用次数断言

```python
from tests.helpers import assert_async_called_with
from unittest.mock import AsyncMock

def test_mock_called():
    mock_func = AsyncMock()
    
    # 调用3次
    mock_func()
    mock_func()
    mock_func()
    
    assert_async_called_with(mock_func, call_count=3)
```

#### assert_mock_not_called - Mock未调用断言

```python
from tests.helpers import assert_mock_not_called
from unittest.mock import AsyncMock

def test_mock_not_called():
    mock_func = AsyncMock()
    
    # 未调用
    assert_mock_not_called(mock_func)
```

### 高级断言

#### assert_dicts_equal - 字典相等断言（可忽略某些键）

```python
from tests.helpers import assert_dicts_equal

def test_dicts_equal():
    dict1 = {"id": 1, "name": "test", "created_at": "2024-01-01"}
    dict2 = {"id": 1, "name": "test", "created_at": "2024-01-02"}
    
    # 忽略created_at字段
    assert_dicts_equal(
        dict1,
        dict2,
        ignore_keys=["created_at"],
        message="除时间戳外字典应该相等"
    )
```

#### assert_all_items_match - 所有项匹配谓词断言

```python
from tests.helpers import assert_all_items_match

def test_all_items_match():
    numbers = [10, 20, 30, 40]
    
    # 所有数字都大于5
    assert_all_items_match(
        numbers,
        lambda x: x > 5,
        message="所有数字都应该大于5"
    )
```

### 幂等性断言

#### assert_idempotency - 幂等性断言

```python
from tests.helpers import assert_idempotency

def test_idempotency():
    response1 = {
        "success": True,
        "data": {"id": 1, "status": "processed"}
    }
    response2 = {
        "success": True,
        "data": {"id": 1, "status": "processed"}
    }
    
    assert_idempotency(
        response1,
        response2,
        check_fields=["success", "data", "status"],
        message="两次请求应该返回相同结果（幂等性）"
    )
```

### AssertionHelper - 断言助手类

```python
from tests.helpers import AssertionHelper

@pytest.fixture
def assertions():
    return AssertionHelper(prefix="测试")

def test_with_helper(assertions: AssertionHelper):
    """使用助手类"""
    # 成功断言
    data = {"id": 1, "name": "test"}
    assertions.equals(data.get("id"), 1)
    
    # 非空断言
    assertions.not_empty(data["name"])
    
    # 字典包含断言
    assertions.dict_contains(data, ["id", "name"])
```

---

## 最佳实践

### 1. 使用工厂创建数据

✅ **推荐**:
```python
async def test_create_order(db_session):
    factory = TestDataFactory(db_session)
    user = await factory.create_user()
    order = await factory.create_order(user_id=user.id)
    await factory.cleanup()
```

❌ **避免**:
```python
async def test_create_order(db_session):
    # 手动创建数据，容易遗漏必需字段
    user = User(
        username="test",
        email="test@example.com",
        # 可能缺少某些必需的初始化
    )
    db_session.add(user)
    await db_session.commit()
```

### 2. 使用断言助手简化测试

✅ **推荐**:
```python
def test_response():
    response = api_call()
    assert_response_success(response, data_key="data")
    assert_not_empty(response["data"])
```

❌ **避免**:
```python
def test_response():
    response = api_call()
    # 复杂的断言，难以阅读
    assert response is not None
    assert "success" in response
    assert response["success"] is True
    assert "data" in response
    assert response["data"] is not None
```

### 3. 在setup中创建Mock

✅ **推荐**:
```python
@pytest.fixture
def mock_cache():
    cache = MockCacheService()
    cache.set("test_key", "test_value")
    return cache

def test_with_mock(mock_cache):
    value = await mock_cache.get("test_key")
    assert value == "test_value"
```

❌ **避免**:
```python
def test_with_mock():
    # 在测试中创建Mock，难以重用
    cache = MockCacheService()
    cache.set("test_key", "test_value")
    value = await cache.get("test_key")
    assert value == "test_value"
```

### 4. 使用自定义消息提高可读性

✅ **推荐**:
```python
def test_validation():
    assert_email_format("test@example.com", "邮箱格式应该正确")
    assert_phone_format("13800138000", "电话号码应该是11位")
```

❌ **避免**:
```python
def test_validation():
    # 默认消息不够清晰
    assert "@" in "test@example.com"
    assert len("13800138000") == 11
```

### 5. 清理测试数据

✅ **推荐**:
```python
@pytest.mark.asyncio
async def test_with_cleanup(db_session):
    factory = TestDataFactory(db_session)
    
    user = await factory.create_user()
    # ... 测试逻辑 ...
    
    # 测试结束前清理
    await factory.cleanup()
```

❌ **避免**:
```python
@pytest.mark.asyncio
async def test_without_cleanup(db_session):
    user = await UserFactory.create_user(db_session)
    # ... 测试逻辑 ...
    # 忘记清理，可能导致数据污染
```

---

## 示例

### 完整的用户注册测试示例

```python
import pytest
from tests.helpers import UserFactory, assert_response_success, assert_not_empty
from tests.helpers.mock_utils import MockAsyncClient
from tests.helpers.assertion_helpers import assert_email_format, assert_status_code

@pytest.mark.asyncio
async def test_user_registration_success(db_session, mock_http):
    """测试用户注册成功"""
    # 使用数据工厂创建测试数据
    user_data = UserFactory.create_user_data(
        username="newuser",
        email="newuser@example.com",
        role="user"
    )
    
    # 设置Mock响应
    mock_http.responses = {
        "https://api.example.com/users/register": {
            "success": True,
            "message": "注册成功",
            "data": {
                "id": 1,
                "username": "newuser",
                "email": "newuser@example.com"
            }
        }
    }
    
    # 执行注册请求
    response = await mock_http.post(
        "https://api.example.com/users/register",
        data=user_data
    )
    
    # 使用断言助手验证
    assert_status_code(response.status_code, 200)
    assert_response_success(response.json(), data_key="data")
    assert_email_format(user_data["email"])
    assert_not_empty(response.json()["data"])
```

### 支付回调测试示例

```python
import pytest
from decimal import Decimal
from tests.helpers import (
    PaymentFactory,
    MockRedisClient,
    assert_response_success,
    assert_idempotency,
)

@pytest.mark.asyncio
async def test_payment_callback_success(mock_redis):
    """测试支付回调成功"""
    # 创建支付回调数据
    callback_data = PaymentFactory.create_callback_data(
        order_no="ORDER123",
        amount="100.00",
        status="success"
    )
    
    # 模拟Redis存储（幂等性检查）
    await mock_redis.set(
        "payment:callback:ORDER123",
        json.dumps(callback_data),
        expire=3600
    )
    
    # 第一次回调
    response1 = process_payment_callback(callback_data)
    assert_response_success(response1)
    
    # 第二次回调（相同数据）
    response2 = process_payment_callback(callback_data)
    assert_idempotency(
        response1,
        response2,
        check_fields=["success", "data"],
        message="回调应该幂等"
    )
```

### AI聊天测试示例

```python
import pytest
from tests.helpers import MockOpenAIClient, assert_not_empty
from tests.helpers.assertion_helpers import assert_timestamp_recent

@pytest.mark.asyncio
async def test_ai_chat(mock_openai):
    """测试AI聊天功能"""
    # 设置Mock响应
    mock_openai.mock_response = "这是AI的回复内容"
    
    # 发送消息
    messages = [
        {"role": "system", "content": "你是一个法律助手"},
        {"role": "user", "content": "什么是劳动合同？"}
    ]
    
    response = await mock_openai.chat(messages)
    
    # 验证响应
    assert_not_empty(response.content)
    assert_not_empty(response.content.strip())
    assert response.usage.total_tokens > 0
```

### 分页测试示例

```python
import pytest
from tests.helpers import UserFactory, assert_pagination
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_pagination(db_session):
    """测试分页功能"""
    from tests.helpers import UserFactory
    from tests.helpers.assertion_helpers import assert_list_sorted, assert_list_length
    
    user = await UserFactory.create_user(db_session)
    
    # 创建一些测试数据
    items = await create_test_items(user.id, 25)
    
    # 测试第2页（每页10条）
    page = 2
    page_size = 10
    total = len(items)
    
    data = items[(page - 1) * page_size: page * page_size]
    
    # 使用分页断言
    assert_pagination(
        page=page,
        page_size=page_size,
        total=total,
        data=data
    )
    
    assert_list_length(data, min(page_size, total - (page - 1) * page_size))
```

---

## 模块索引

- [`test_data_factory.py`](./test_data_factory.py:1) - 数据工厂
  - `UserFactory` - 用户数据工厂
  - `OrderFactory` - 订单数据工厂
  - `PaymentFactory` - 支付数据工厂
  - `ConsultationFactory` - 咨询数据工厂
  - `ForumPostFactory` - 论坛帖子工厂
  - `NewsFactory` - 新闻数据工厂
  - `TestDataFactory` - 统一数据工厂

- [`mock_utils.py`](./mock_utils.py:1) - Mock工具
  - `MockAsyncClient` - HTTP客户端Mock
  - `MockCacheService` - 缓存服务Mock
  - `MockOpenAIClient` - OpenAI客户端Mock
  - `MockRedisClient` - Redis客户端Mock
  - `MockDatabaseSession` - 数据库会话Mock
  - `create_mock_service` - Mock服务创建函数
  - `patch_import` - 导入补丁函数

- [`assertion_helpers.py`](./assertion_helpers.py:1) - 断言助手
  - `assert_response_success` - 成功响应断言
  - `assert_response_error` - 错误响应断言
  - `assert_not_empty` - 非空断言
  - `assert_not_none` - 非None断言
  - `assert_equals` - 相等断言
  - `assert_dict_contains` - 字典包含断言
  - `assert_pagination` - 分页断言
  - `assert_validation_error` - 验证错误断言
  - `assert_idempotency` - 幂等性断言
  - `assert_coverage_increased` - 覆盖率增加断言
  - `AssertionHelper` - 断言助手类

---

## 问题排查

### 常见问题

#### 1. 数据工厂创建失败

**问题**: 创建数据时出现外键约束错误

**解决方案**:
```python
# 先创建依赖对象
user = await factory.create_user()
lawyer = await factory.create_lawyer()

# 再创建依赖这些对象的数据
consultation = await factory.create_consultation(
    user_id=user.id,
    lawyer_id=lawyer.id
)
```

#### 2. Mock不生效

**问题**: Mock对象未被正确应用

**解决方案**:
```python
from tests.helpers import patch_import

# 使用patch_import而不是直接patch
with patch_import("app.services.cache_service", "get_cache_service", mock_cache):
    # 测试代码
    pass
```

#### 3. 断言消息不清晰

**问题**: 测试失败时不知道具体原因

**解决方案**:
```python
# 提供清晰的消息
assert_equals(actual, expected, "价格应该是100.00，而不是99.99")
# 而不是
assert_equals(actual, expected)
```

---

## 维护指南

### 添加新的数据工厂

1. 在`test_data_factory.py`中创建新的Factory类
2. 实现`create_xxx_data`静态方法（仅创建字典）
3. 实现`create_xxx`异步方法（创建数据库实例）
4. 在`TestDataFactory`中添加相应方法
5. 更新`__init__.py`导出新Factory

### 添加新的断言助手

1. 在`assertion_helpers.py`中添加新的断言函数
2. 函数命名使用`assert_xxx`格式
3. 添加清晰的docstring文档
4. 在`AssertionHelper`类中添加对应方法（可选）
5. 更新`__init__.py`导出新函数

### 添加新的Mock工具

1. 在`mock_utils.py`中创建新的Mock类
2. 实现必要的Mock方法
3. 添加`_calls`、`_store`等属性用于测试验证
4. 更新`create_mock_service`函数支持新类型
5. 更新`__init__.py`导出新Mock类

---

**最后更新**: 2026-01-29  
**维护者**: CoStrict
<!-- 文档结束 -->