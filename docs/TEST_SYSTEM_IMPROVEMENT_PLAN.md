# 测试系统完善计划

## 项目测试现状分析

### 后端测试 (Python/FastAPI)

| 项目 | 现状 |
|------|------|
| 测试框架 | pytest + pytest-asyncio |
| 测试数量 | 3840 个测试用例 |
| 测试覆盖率 | 55-60% |
| 配置文件 | `pytest.ini`, `conftest.py` |
| 测试类型 | 单元测试、集成测试、E2E测试 |

**优点:**
- 完善的 pytest 配置，支持异步测试
- 丰富的 fixtures (数据库、认证、Mock)
- 测试标记系统 (slow, unit, integration, e2e, database, redis)
- 测试辅助工具 (helpers 目录)

**待改进:**
- 部分测试文件在 backend 根目录而非 tests 目录
- 缺少测试覆盖率阈值强制
- E2E 测试需要单独的运行环境

### 前端测试 (React/Vite)

| 项目 | 现状 |
|------|------|
| 测试框架 | Vitest + React Testing Library |
| 测试数量 | ~12 个测试文件 |
| 配置文件 | `vitest.config.ts`, `src/test/setup.ts` |
| 测试覆盖 | points, promotion, 部分 UI 组件 |

**优点:**
- Vitest 配置完善，支持 TypeScript
- React Testing Library 集成
- 测试工具函数封装良好

**待改进:**
- 测试覆盖率较低，大量 features 缺少测试
- 缺少组件测试
- 缺少 Hook 测试
- 缺少集成测试

---

## 已完成的改进

### ✅ 第一阶段: 基础设施完善

#### 1.1 后端测试命令 (Makefile)
- 创建了 [`backend/Makefile`](../backend/Makefile)
- 包含常用测试命令: `make test`, `make test-cov`, `make test-unit`, `make test-fast`

#### 1.2 前端测试配置增强
- 更新了 [`frontend-v2/vitest.config.ts`](../frontend-v2/vitest.config.ts)
- 添加了覆盖率配置和阈值
- 配置了并行测试执行

#### 1.3 测试数据工厂
- 创建了 [`frontend-v2/src/test/mocks/data.ts`](../frontend-v2/src/test/mocks/data.ts)
- 提供统一的测试数据生成工具

### ✅ 第二阶段: CI/CD 集成

#### 2.1 GitHub Actions 工作流
- 创建了 [`.github/workflows/test.yml`](../.github/workflows/test.yml)
- 后端和前端测试并行运行
- 覆盖率上传到 Codecov

#### 2.2 Pre-commit Hooks
- 创建了 [`.pre-commit-config.yaml`](../.pre-commit-config.yaml)
- 代码检查: ruff (Python), eslint (前端)
- 测试运行: 后端快速测试、前端测试

### ✅ 第三阶段: 测试覆盖扩展

#### 3.1 前端测试文件

| 功能模块 | 测试文件 | 状态 |
|---------|---------|------|
| Points Balance | `features/points/__tests__/PointsBalance.test.tsx` | ✅ 11 个测试 |
| CheckIn Button | `features/points/__tests__/CheckInButton.test.tsx` | ✅ 7 个测试 |
| Points History | `features/points/__tests__/PointsHistory.test.tsx` | ✅ 12 个测试 |
| Promotion Hook | `features/promotion/__tests__/usePromotion.test.tsx` | ✅ 17 个测试 |
| Payment Hooks | `features/payment/__tests__/usePayments.test.tsx` | ✅ 17 个测试 |
| User Profile | `features/user/__tests__/useUserProfile.test.tsx` | ✅ 9 个测试 |
| UI Components | `components/ui/__tests__/*.test.tsx` | ✅ 101 个测试 |
| Utils | `shared/utils/index.test.ts` | ✅ 6 个测试 |

**总计: 11 个测试文件, 180 个测试用例全部通过**

### ✅ 第四阶段: E2E 测试配置

#### 4.1 Playwright 配置
- 创建了 [`frontend-v2/playwright.config.ts`](../frontend-v2/playwright.config.ts)
- 支持多浏览器测试 (Chromium, Firefox, WebKit)
- 支持移动端测试 (Pixel 5, iPhone 12)

#### 4.2 E2E 测试文件
- [`frontend-v2/e2e/auth.spec.ts`](../frontend-v2/e2e/auth.spec.ts) - 认证流程测试
- [`frontend-v2/e2e/home.spec.ts`](../frontend-v2/e2e/home.spec.ts) - 首页测试

### ✅ 第五阶段: 文档更新

- 更新了 [`backend/tests/README.md`](../backend/tests/README.md)
- 创建了本文档

---

## 快速开始

### 后端测试

```bash
cd backend

# 运行所有测试
make test

# 运行测试并生成覆盖率报告
make test-cov

# 只运行单元测试
make test-unit

# 运行快速测试（排除慢速测试）
make test-fast

# 生成HTML覆盖率报告
make test-coverage-html
```

### 前端测试

```bash
cd frontend-v2

# 运行所有单元测试
npm run test

# 监视模式
npm run test:watch

# 生成覆盖率报告
npm run test:coverage

# 运行 E2E 测试
npm run test:e2e

# E2E 测试 UI 模式
npm run test:e2e:ui

# 安装 Playwright 浏览器
npm run playwright:install
```

### Pre-commit Hooks 安装

```bash
# 安装 pre-commit
pip install pre-commit

# 安装 hooks
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

---

## 测试模板

### API 测试模板

```typescript
// features/[feature]/__tests__/api.test.ts
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('@/shared/lib/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { apiClient } from '@/shared/lib/api/client';
const mockGet = vi.mocked(apiClient.get);

describe('[Feature] API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功获取数据', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: '1' } });
    // ... 测试逻辑
  });
});
```

---

## 下一步计划

1. **提高前端测试覆盖率** - 为更多功能添加测试
2. **添加组件测试** - 使用 React Testing Library
3. **添加 E2E 测试** - 使用 Playwright
4. **性能测试** - 添加性能基准测试

---

## 成功指标

| 指标 | 当前 | 目标 |
|------|------|------|
| 后端测试覆盖率 | 55-60% | 70%+ |
| 前端测试覆盖率 | ~10% | 50%+ |
| CI/CD 通过率 | - | 95%+ |
| 测试执行时间 | - | 后端 < 5分钟, 前端 < 1分钟 |

---

*创建日期: 2026-02-10*
*最后更新: 2026-02-10*
