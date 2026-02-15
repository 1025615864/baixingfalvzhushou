# 测试系统文档

## 测试结构概览

百姓助手项目的测试系统采用分层架构，确保代码质量和功能稳定性。

### 测试目录结构

```
backend/
├── tests/              # 测试目录
│   ├── e2e/            # 端到端测试
│   │   ├── fixtures/   # 测试数据夹具
│   │   ├── helpers/    # 测试辅助工具
│   │   ├── pages/      # 页面对象模型
│   │   ├── reports/    # 测试报告
│   │   ├── specs/      # 测试规范
│   │   └── playwright.config.ts
│   ├── helpers/        # 测试辅助工具
│   │   ├── assertion_helpers.py
│   │   ├── mock_utils.py
│   │   └── test_data_factory.py
│   ├── conftest.py     # 主测试配置
│   └── conftest_income.py # 收入相关测试配置
├── pytest.ini          # Pytest配置
└── Makefile            # 测试命令快捷方式

frontend-v2/
├── src/
│   ├── test/           # 测试配置
│   │   ├── setup.ts    # 测试环境设置
│   │   ├── test-utils.tsx # 测试工具函数
│   │   └── mocks/      # Mock数据
│   │       └── data.ts # 测试数据工厂
│   └── features/       # 功能测试
│       └── [feature]/
│           └── __tests__/
│               ├── api.test.ts
│               ├── hooks.test.ts
│               └── components.test.tsx
└── vitest.config.ts    # Vitest配置
```

## 测试配置

### 后端配置文件

| 文件 | 说明 |
|------|------|
| `pytest.ini` | Pytest主配置文件 |
| `conftest.py` | 测试夹具和配置 |
| `Makefile` | 测试命令快捷方式 |

### 前端配置文件

| 文件 | 说明 |
|------|------|
| `vitest.config.ts` | Vitest配置 |
| `src/test/setup.ts` | 测试环境设置 |
| `src/test/test-utils.tsx` | 测试工具函数 |

### 测试覆盖率

| 项目 | 当前覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| 后端 | 55-60% | 70%+ |
| 前端 | ~10% | 50%+ |

## 运行测试

### 后端测试

```bash
# 进入后端目录
cd backend

# 运行所有测试
make test
# 或
python -m pytest -v

# 运行测试并生成覆盖率报告
make test-cov
# 或
python -m pytest --cov=app --cov-report=term-missing

# 只运行单元测试
make test-unit
# 或
python -m pytest -m unit -v

# 只运行集成测试
make test-integration
# 或
python -m pytest -m integration -v

# 运行快速测试（排除慢速测试）
make test-fast
# 或
python -m pytest -m "not slow" -v

# 生成HTML覆盖率报告
make test-coverage-html
# 或
python -m pytest --cov=app --cov-report=html

# 清理测试缓存
make clean

# CI/CD 环境运行
make test-ci
```

### 前端测试

```bash
# 进入前端目录
cd frontend-v2

# 运行所有测试
npm run test
# 或
npx vitest run

# 监视模式
npm run test:watch
# 或
npx vitest

# 生成覆盖率报告
npm run test:coverage
# 或
npx vitest run --coverage

# 运行特定测试文件
npx vitest run src/features/points/__tests__/api.test.ts

# 使用 UI 界面运行测试（需要安装 @vitest/ui）
npm run test:ui
```

### E2E 测试

```bash
# 进入后端目录
cd backend

# 运行 E2E 测试
make test-e2e
# 或
python -m pytest tests/e2e/ -v -m e2e

# 使用 Playwright 直接运行
cd tests/e2e
npx playwright test
```

## 测试标记

后端测试支持以下标记：

| 标记 | 说明 | 使用示例 |
|------|------|---------|
| `unit` | 单元测试 | `@pytest.mark.unit` |
| `integration` | 集成测试 | `@pytest.mark.integration` |
| `e2e` | 端到端测试 | `@pytest.mark.e2e` |
| `slow` | 慢速测试 | `@pytest.mark.slow` |
| `database` | 需要数据库 | `@pytest.mark.database` |
| `redis` | 需要 Redis | `@pytest.mark.redis` |
| `external` | 调用外部 API | `@pytest.mark.external` |
| `performance` | 性能测试 | `@pytest.mark.performance` |

## 测试最佳实践

### 1. 测试命名规范

**后端:**
- 单元测试：`test_<模块>_<功能>_<场景>`
- 集成测试：`test_integration_<服务>_<场景>`
- E2E测试：`test_e2e_<功能流程>`

**前端:**
- API 测试：`[feature].test.ts`
- Hook 测试：`hooks.test.ts`
- 组件测试：`Component.test.tsx`

### 2. 测试数据管理

- 使用夹具(fixtures)管理测试数据
- 使用测试数据工厂生成测试数据
- 避免在测试中硬编码数据
- 每个测试后清理测试数据

### 3. 测试隔离

- 每个测试应该独立运行
- 使用数据库事务回滚
- 避免测试间的依赖关系

### 4. 测试结构 (AAA 模式)

```python
def test_feature():
    # Arrange - 准备测试数据
    data = create_test_data()
    
    # Act - 执行被测试的操作
    result = function_under_test(data)
    
    # Assert - 验证结果
    assert result == expected_value
```

## 测试工具链

### 后端工具

| 工具 | 说明 |
|------|------|
| **pytest** | 测试框架 |
| **pytest-asyncio** | 异步测试支持 |
| **pytest-cov** | 覆盖率报告 |
| **pytest-xdist** | 并行测试 |
| **schemathesis** | API 测试 |
| **Playwright** | E2E 测试 |

### 前端工具

| 工具 | 说明 |
|------|------|
| **Vitest** | 测试框架 |
| **React Testing Library** | React 组件测试 |
| **@testing-library/user-event** | 用户交互模拟 |
| **@vitest/coverage-v8** | 覆盖率报告 |

## CI/CD 集成

测试系统已集成到 GitHub Actions CI/CD 流水线中：

- 配置文件：`.github/workflows/test.yml`
- 触发条件：push/PR 到 main/develop 分支
- 测试类型：后端测试、前端测试
- 覆盖率上传：Codecov

## 常见问题解决

### 测试失败排查

1. 检查测试环境配置
2. 验证测试数据准备
3. 检查外部服务连接
4. 查看详细错误日志

### 调试测试

```bash
# 后端 - 详细输出
python -m pytest -v --tb=long

# 后端 - 进入调试模式
python -m pytest --pdb

# 前端 - 详细输出
npx vitest run --reporter=verbose
```

### 性能问题

1. 优化数据库查询
2. 减少网络请求
3. 使用缓存策略
4. 并行化测试执行

```bash
# 后端 - 并行测试
python -m pytest -n auto

# 前端 - 并行测试（默认开启）
npx vitest run
```

## 扩展阅读

- [测试系统完善计划](./TEST_SYSTEM_IMPROVEMENT_PLAN.md)
- [API 测试指南](./guides/API_QUICK_REFERENCE.md)
- [项目结构审查](./PROJECT_STRUCTURE_REVIEW.md)

---

*最后更新：2026-02-10*