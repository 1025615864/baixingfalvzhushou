# 百姓助手 - E2E测试套件

## 概述

此目录包含使用Playwright进行端到端(E2E)测试的完整测试套件。

## 目录结构

```
e2e/
├── playwright.config.ts    # Playwright主配置文件
├── package.json           # NPM依赖和脚本
├── README.md             # 本文档
├── specs/                # 测试用例文件
│   └── example.spec.ts   # 示例测试用例
├── pages/                # 页面对象模型（POM）
├── helpers/              # 测试辅助函数
│   └── test-helper.ts    # 通用测试辅助类
├── fixtures/             # 测试数据
│   └── test-data.ts      # Mock数据和测试数据
├── reports/              # 测试报告目录（自动生成）
└── test-results/         # 测试结果目录（自动生成）
```

## 快速开始

### 1. 安装依赖

```bash
cd backend/tests/e2e
npm install
```

### 2. 安装Playwright浏览器

```bash
npm run test:install
```

### 3. 运行测试

```bash
# 运行所有测试
npm test

# 带UI模式运行测试
npm run test:ui

# 带head模式运行测试
npm run test:headed

# 调试模式
npm run test:debug

# 只运行特定浏览器
npm run test:chromium
npm run test:firefox
npm run test:webkit
```

### 4. 查看测试报告

```bash
npm run test:report
```

## 配置说明

### playwright.config.ts

主配置文件包含：

- **testDir**: 测试文件位置（specs/）
- **timeout**: 测试超时时间（30秒）
- **projects**: 多浏览器配置（Chromium、Firefox、WebKit）
- **webServer**: 本地开发服务器配置
- **reporter**: 报告配置（HTML、JSON、JUnit）

### BASE_URL

默认使用 `http://localhost:5173`（Vite开发服务器）。可通过环境变量修改：

```bash
set BASE_URL=http://localhost:8000
npm test
```

## 编写测试

### 基本测试结构

```typescript
import { test, expect } from '@playwright/test';
import { createTestHelper } from '../helpers/test-helper';

test.describe('功能模块测试', () => {
    test('测试用例描述', async ({ page }) => {
        const helper = createTestHelper(page);
        
        // 测试步骤
        await page.goto('/some-page');
        await expect(page).toHaveTitle('页面标题');
        
        // 使用辅助方法
        await helper.waitForVisible('[data-testid="element"]');
        await helper.screenshot('test-case-name');
    });
});
```

### 测试辅助方法

使用 `test-helper.ts` 中的辅助类：

```typescript
const helper = createTestHelper(page);

// 等待元素
await helper.waitForVisible(selector);

// 安全点击
await helper.safeClick(selector);

// 安全填充
await helper.safeFill(selector, value);

// 截图
await helper.screenshot('test-name');

// 等待API响应
await helper.waitForResponse('/api/endpoint');

// 登录
await helper.login(email, password);
```

### 测试数据

使用 `test-data.ts` 中的预定义数据：

```typescript
import { testUsers, testConsultations } from '../fixtures/test-data';

const user = testUsers.defaultUser;
const consultation = testConsultations[0];
```

## 测试用例命名规范

- 使用 `.spec.ts` 扩展名
- 文件名使用kebab-case：`user-login.spec.ts`
- 测试描述使用中文，清晰说明测试目的
- 使用 `test.describe` 组织相关测试

## data-testid 属性

测试选择器应优先使用 `data-testid` 属性：

```html
<button data-testid="login-button">登录</button>
<input data-testid="email-input" type="email" />
```

## CI/CD集成

在CI环境中运行：

```yaml
- name: Run E2E Tests
  run: |
    cd backend/tests/e2e
    npm ci
    npm run test:install
    npm test
```

## 常见问题

### 1. 测试超时

增加超时时间：

```typescript
test.setTimeout(60000); // 60秒
```

### 2. 元素未找到

使用 `waitForVisible` 而不是直接选择：

```typescript
await helper.waitForVisible('[data-testid="element"]');
```

### 3. 网络请求失败

确保测试时后端服务正在运行，或使用Mock：

```typescript
await helper.mockAPI('/api/endpoint', mockData);
```

## MCP工具集成

此E2E测试套件已集成到MCP工具系统。可通过后端API调用：

```python
from app.services.mcp.tools.e2e_test_tool import E2ETestTool

tool = E2ETestTool()
result = await tool.arun({
    "action": "run",
    "browser": "chromium",
    "headless": True
})
```

## 最佳实践

1. **独立测试**: 每个测试应该独立运行，不依赖其他测试
2. **清理状态**: 使用 `afterEach` 清理测试数据
3. **等待策略**: 优先使用明确的等待条件（如 `waitForVisible`）
4. **截图**: 重要步骤和失败时自动截图
5. **复用代码**: 使用辅助函数和页面对象模型
6. **错误处理**: 添加适当的错误消息和断言

## 贡献指南

添加新测试时：

1. 在 `specs/` 目录创建新的 `.spec.ts` 文件
2. 使用现有的辅助函数和数据fixtures
3. 遵循命名规范和代码风格
4. 确保测试可以独立运行
5. 提交前运行完整测试套件

## 相关文档

- [Playwright文档](https://playwright.dev/)
- [项目编码规范](../../.roo/rules-code/coding-standards.md)
- [MCP工具文档](../../app/services/mcp/README.md)

## 联系方式

如有问题，请联系开发团队。