# 测试指南

本文档提供百姓助手项目的测试规范和最佳实践。

## 运行测试

### 运行所有测试
```bash
py -m pytest tests/ -v
```

### 运行特定测试文件
```bash
py -m pytest tests/test_forum_service.py -v
```

### 运行特定测试
```bash
py -m pytest tests/test_forum_service.py::TestForumPostService::test_get_posts_empty -v
```

### 运行集成测试
```bash
py -m pytest tests/test_orders_pay_integration.py -v
```

### 运行负载测试
```bash
py -m pytest tests/test_load.py -v
```

### 运行安全测试
```bash
py -m pytest tests/test_security.py -v
```

## 测试分类

### 单元测试
- 位于 `tests/` 目录下
- 测试单个函数或类的行为
- 使用 mock 隔离外部依赖

### 集成测试
- 测试多个模块协作
- 位于 `tests/test_*_integration.py`
- 使用真实数据库连接

### 负载测试
- 测试 API 性能
- 位于 `tests/test_load.py`
- 验证响应时间和吞吐量

### 安全测试
- 测试安全漏洞
- 位于 `tests/test_security.py`
- 包括 SQL 注入、XSS、权限控制等

## 测试 Fixtures

### 常用 Fixtures

| Fixture | 用途 |
|---------|------|
| `client` | HTTP 测试客户端 |
| `test_session` | 数据库会话 |
| `test_user` | 测试用户 |
| `test_admin_user` | 测试管理员 |
| `test_lawyer` | 测试律师 |
| `test_data_factory` | 测试数据工厂 |

### 使用示例

```python
@pytest.mark.asyncio
async def test_example(client: AsyncClient, test_user: User) -> None:
    """测试示例"""
    # 使用预创建的用户
    res = await client.get(f"/api/user/{test_user.id}")
    assert res.status_code == 200
```

## 测试数据工厂

使用 `test_data_factory` 创建测试数据：

```python
@pytest.mark.asyncio
async def test_with_factory(test_data_factory: TestDataFactory) -> None:
    """使用工厂创建测试数据"""
    # 创建用户
    user = await test_data_factory.create_user(
        username="custom_user",
        email="custom@example.com",
        role="user",
    )
    
    # 创建律师
    lawyer = await test_data_factory.create_lawyer(
        user=user,
        name="张律师",
        specialties="劳动法",
    )
    
    # 测试完成后自动清理
```

## 测试最佳实践

### 1. 测试命名
- 使用描述性测试名称
- 遵循 `test_<功能>_<场景>` 格式
- 示例：`test_forum_posts_pagination`

### 2. 测试隔离
- 每个测试独立运行
- 使用 fixture 清理数据
- 避免测试间共享状态

### 3. Mock 使用
- Mock 外部服务调用
- Mock 时间相关函数
- Mock 随机数生成

### 4. 断言清晰
- 使用有意义的断言消息
- 避免过度断言
- 验证关键行为

### 5. 测试覆盖率
- 目标覆盖率 >= 70%
- 关键路径 100% 覆盖
- 边界条件必须测试

## CI/CD 集成

### GitHub Actions
测试在以下情况自动运行：
- 提交到主分支
- 创建 Pull Request
- 定时任务（每日）

### 门禁规则
- 所有测试必须通过
- 覆盖率下降 > 5% 需审查
- 新代码必须有测试覆盖

## 常见问题

### Q: 测试运行太慢？
A: 检查是否有网络调用未 mock，使用内存数据库。

### Q: 测试不稳定？
A: 检查测试间隔离，确保每次测试独立清理状态。

### Q: 如何调试测试？
A: 使用 `--tb=short` 查看错误详情，使用 `print()` 输出调试信息。

## 相关文档
- [测试覆盖率报告](../TEST_COVERAGE_ANALYSIS_REPORT.json)
- [测试验收标准](../TASKS_NEXT.md)
