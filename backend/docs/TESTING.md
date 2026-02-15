# 后端测试指南

## 测试框架

- **测试运行器**: pytest
- **异步测试**: pytest-asyncio
- **覆盖率**: pytest-cov

## 快速开始

```bash
# 运行所有测试
py -m pytest tests/ -v

# 运行指定文件
py -m pytest tests/test_user.py -v

# 运行指定测试
py -m pytest tests/test_user.py::test_login -v

# 生成覆盖率报告
py -m pytest --cov=app --cov-report=term-missing

# 覆盖率检查（失败阈值 62%）
py -m pytest --cov=app --cov-fail-under=62
```

## 测试规范

### 单元测试

```python
# tests/test_user.py
import pytest
from app.services.user import UserService

@pytest.fixture
def user_service():
    return UserService()

@pytest.mark.asyncio
async def test_create_user(user_service):
    user = await user_service.create_user(
        username="test",
        email="test@example.com"
    )
    assert user.username == "test"
```

### API 测试

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Mock 测试

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    with patch("app.services.cache.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        # 测试逻辑
```

## 测试覆盖率要求

- **整体覆盖率**: >= 62%
- **关键路径**: 100%
- **异常处理**: 必须覆盖
