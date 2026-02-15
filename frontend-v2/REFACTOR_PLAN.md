# 百姓助手前端重构计划

## 📋 概述

**重构目标**: 从零重建前端代码库，解决现有 913 个问题，建立可维护、可扩展的现代化前端架构

**重构策略**: 渐进式重构，按功能模块逐步迁移，确保业务连续性

**预估工期**: 4-6 周（2 名前端工程师）

---

## 一、现有问题分析

### 1.1 致命问题 (91 个错误)

| 问题类型 | 数量 | 影响 |
|---------|------|-----|
| React Hooks 错误 | 91 | 运行时崩溃风险 |
| 文件编码乱码 | 多处 | 维护困难 |
| `any` 类型泛滥 | 800+ | 类型安全丧失 |

### 1.2 架构问题

- **目录结构混乱** - 按类型而非功能组织
- **组件职责不清** - 巨型组件，难以测试
- **状态管理混乱** - 无统一方案
- **API 层不规范** - 类型定义缺失

---

## 二、重构目标

### 2.1 质量目标

| 指标 | 现状 | 目标 |
|-----|------|-----|
| ESLint 错误 | 91 | 0 |
| TypeScript 严格模式错误 | 未知 | 0 |
| `any` 类型使用率 | >60% | 0% |
| 单元测试覆盖率 | <30% | >80% |
| 构建警告 | 多 | 0 |

### 2.2 性能目标

| 指标 | 目标 |
|-----|------|
| FCP | < 1.5s |
| LCP | < 2.5s |
| 包体积 (gzip) | < 200KB |
| Lighthouse | > 90 |

---

## 三、新架构设计

### 3.1 技术栈升级

```
当前                              目标
─────────────────────────────────────────────────
React 18.2                        React 18.2 ✓
React Router 7                    React Router 6.20 (降级至稳定版)
任意状态管理                       Zustand + React Query
Ant Design 5.21                   Ant Design 5.21 ✓
Tailwind CSS 4                    Tailwind CSS 3.4 (稳定版)
TypeScript 5.3                    TypeScript 5.3 (严格模式)
ESLint (混乱配置)                  ESLint 8 + 标准配置
Vite 7                            Vite 5 (稳定版)
```

### 3.2 目录结构 (Feature-Based)

```
frontend/
├── src/
│   ├── app/                    # 应用入口
│   │   ├── App.tsx
│   │   ├── router.tsx          # 路由配置
│   │   └── providers.tsx       # 全局 Provider
│   │
│   ├── features/               # 功能模块
│   │   ├── auth/              # 认证模块
│   │   ├── chat/              # AI 咨询模块
│   │   ├── consultation/      # 律师咨询模块
│   │   ├── document/          # 文档生成模块
│   │   ├── payment/           # 支付模块
│   │   ├── news/              # 新闻模块
│   │   ├── lawyer/            # 律师工作台
│   │   └── settlement/        # 结算模块
│   │
│   ├── shared/                # 共享资源
│   │   ├── components/        # 通用组件
│   │   ├── hooks/             # 通用 hooks
│   │   ├── lib/               # 第三方库封装
│   │   ├── types/             # 全局类型
│   │   └── utils/             # 工具函数
│   │
│   ├── widgets/               # 独立功能组件
│   └── pages/                 # 页面组件 (薄层)
│
├── tests/
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   └── e2e/                   # E2E 测试
│
└── docs/                      # 文档
```

### 3.3 功能模块结构 (每个 feature)

```
features/auth/
├── api/
│   ├── client.ts              # axios 实例
│   ├── types.ts               # API 类型
│   ├── endpoints.ts           # 端点定义
│   ├── queries.ts             # React Query hooks
│   └── mutations.ts           # Mutation hooks
├── components/
│   ├── LoginForm/
│   │   ├── index.tsx
│   │   ├── LoginForm.test.tsx
│   │   └── styles.module.css
│   └── RegisterForm/
├── hooks/
│   ├── useAuth.ts
│   └── usePermissions.ts
├── stores/
│   └── authStore.ts           # Zustand store
├── types/
│   └── index.ts
├── utils/
│   └── tokenManager.ts
└── index.ts                   # Barrel export
```

---

## 四、重构阶段计划

### 阶段 0: 准备工作 (第 1 周)

#### Week 0, Day 1-2: 环境搭建

- [ ] 创建新的前端目录 `frontend-v2/`
- [ ] 初始化 Vite + React + TypeScript 项目
- [ ] 配置 ESLint + Prettier
- [ ] 配置路径别名 `@/*`
- [ ] 安装核心依赖

```bash
# 创建项目
npm create vite@latest frontend-v2 -- --template react-ts

# 安装依赖
cd frontend-v2
npm install react@18.2.0 react-dom@18.2.0 react-router-dom@6.20.0
npm install @tanstack/react-query@5.8.0 zustand@4.4.0
npm install antd@5.21.3 tailwindcss@3.4.0
npm install -D eslint@8 prettier vitest @testing-library/react
```

#### Week 0, Day 3-5: 基础设施

- [ ] 配置 Tailwind CSS
- [ ] 配置 ESLint (零错误策略)
- [ ] 配置 TypeScript (严格模式)
- [ ] 创建目录结构
- [ ] 编写基础工具函数
- [ ] 配置测试环境

#### 产出物

- [ ] 可运行的空白项目
- [ ] CI/CD 流水线配置
- [ ] 代码质量门禁配置

---

### 阶段 1: 核心基础设施 (第 2 周)

#### Week 1, Day 1-2: API 层

- [ ] 创建 API Client 封装
- [ ] 实现请求/响应拦截器
- [ ] 错误处理机制
- [ ] 类型定义系统

```typescript
// shared/lib/api/client.ts
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
});

// 拦截器
apiClient.interceptors.request.use(authInterceptor);
apiClient.interceptors.response.use(
  responseInterceptor,
  errorInterceptor
);
```

#### Week 1, Day 3-4: 状态管理

- [ ] 创建 Zustand store 模板
- [ ] 实现 React Query 配置
- [ ] 创建全局状态 (主题、用户、通知)

```typescript
// shared/stores/userStore.ts
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

interface UserState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useUserStore = create<UserState>()(
  immer((set) => ({
    user: null,
    isAuthenticated: false,
    setUser: (user) => set({ user, isAuthenticated: !!user }),
    logout: () => set({ user: null, isAuthenticated: false }),
  }))
);
```

#### Week 1, Day 5: UI 组件库

- [ ] 封装 Ant Design 组件
- [ ] 创建通用组件
  - [ ] Button
  - [ ] Input
  - [ ] Modal
  - [ ] Card
  - [ ] Loading
  - [ ] ErrorBoundary

#### 产出物

- [ ] 完整的 API 层
- [ ] 状态管理系统
- [ ] 基础 UI 组件库
- [ ] 单元测试覆盖 >80%

---

### 阶段 2: 认证模块重构 (第 3 周)

#### Week 2, Day 1-2: Auth API 层

迁移文件:
- `frontend/src/api/domains/auth.ts` → `features/auth/api/`

- [ ] 迁移登录 API
- [ ] 迁移注册 API
- [ ] 迁移 Token 刷新逻辑
- [ ] 编写完整类型定义

#### Week 2, Day 3-4: Auth 组件

迁移文件:
- `frontend/src/components/LoginPage/` → `features/auth/components/LoginForm/`

- [ ] 重构 LoginForm
- [ ] 重构 RegisterForm
- [ ] 重构 ForgotPasswordForm
- [ ] 添加表单验证

#### Week 2, Day 5: Auth 集成

- [ ] 创建 AuthGuard 组件
- [ ] 集成路由守卫
- [ ] 编写单元测试

#### 产出物

- [ ] 完整的认证模块
- [ ] 100% 类型覆盖
- [ ] 单元测试 >80%
- [ ] 可与旧系统并存

---

### 阶段 3: 核心功能模块 (第 4-5 周)

#### Week 3: AI 咨询模块 (Chat)

迁移优先级: **高** (核心功能)

- [ ] Chat API 层
  - 迁移 `frontend/src/api/domains/ai.ts`
  - 迁移 `frontend/src/api/domains/chat.ts`
- [ ] Chat 组件
  - 迁移 `frontend/src/components/chat/`
  - 迁移 `frontend/src/features/ai-consultation/`
- [ ] 重构 Chat 状态管理
- [ ] 重构 WebSocket 连接

#### Week 4: 律师咨询模块

- [ ] Consultation API 层
- [ ] Consultation 列表/详情
- [ ] 预约功能
- [ ] 支付集成

### 阶段 4: 其他功能模块 (第 6-7 周)

按优先级依次重构:

| 优先级 | 模块 | 说明 |
|-------|------|------|
| P0 | Payment | 支付系统 |
| P0 | Document | 文档生成 |
| P1 | News | 新闻资讯 |
| P1 | Lawyer | 律师工作台 |
| P2 | Settlement | 结算系统 |
| P2 | Forum | 社区论坛 |

---

### 阶段 5: 测试与优化 (第 8 周)

- [ ] E2E 测试覆盖核心流程
- [ ] 性能优化
- [ ] 代码审查
- [ ] 文档完善

---

## 五、迁移策略

### 5.1 蓝绿部署

```
阶段 1: 并行运行 (4周)
├── 旧系统: / (继续服务)
└── 新系统: /v2 (逐步开放)

阶段 2: 流量切换 (1周)
├── 新系统: / (主要流量)
└── 旧系统: /legacy (备用)

阶段 3: 下线旧系统 (1周)
└── 完全切换到新系统
```

### 5.2 数据迁移

- [ ] API 接口保持不变
- [ ] LocalStorage 数据兼容
- [ ] 用户会话无缝切换

### 5.3 回滚计划

- [ ] 保留旧系统代码
- [ ] 数据库回滚脚本
- [ ] 快速切换 DNS 配置

---

## 六、代码质量门禁

### 6.1 提交前检查 (Pre-commit)

```bash
#!/bin/sh
# .husky/pre-commit

# 1. 类型检查
npx tsc --noEmit

# 2. ESLint
npx eslint src --max-warnings 0

# 3. 单元测试
npx vitest run --coverage --coverage.threshold=80

# 4. 构建检查
npm run build
```

### 6.2 CI/CD 流水线

```yaml
# .github/workflows/frontend.yml
name: Frontend CI

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Type check
        run: npx tsc --noEmit
        
      - name: Lint
        run: npx eslint src --max-warnings 0
        
      - name: Test
        run: npx vitest run --coverage
        
      - name: Build
        run: npm run build
```

---

## 七、风险与应对

| 风险 | 可能性 | 影响 | 应对措施 |
|-----|--------|------|---------|
| 工期延误 | 中 | 高 | 分阶段交付，核心功能优先 |
| 功能遗漏 | 低 | 高 | 详细的需求对照表，QA 全程参与 |
| 性能退化 | 低 | 中 | 性能基准测试，每阶段对比 |
| 团队适应 | 中 | 低 | 代码规范培训，Code Review |

---

## 八、验收标准

### 8.1 功能验收

- [ ] 所有现有功能正常可用
- [ ] 无回归 Bug
- [ ] 移动端适配正常

### 8.2 质量验收

- [ ] ESLint 零错误
- [ ] TypeScript 严格模式零错误
- [ ] 单元测试覆盖率 >80%
- [ ] E2E 测试通过率 100%

### 8.3 性能验收

- [ ] Lighthouse 评分 >90
- [ ] 首屏加载 <2s
- [ ] 内存泄漏检测通过

---

## 九、参考文档

- [CONTRIBUTING.md](./CONTRIBUTING.md) - 开发规范
- [API 文档](../docs/API.md) - 后端接口
- [设计稿](../docs/Design.md) - UI 设计

---

## 十、任务清单

### 准备工作

- [ ] 创建 `frontend-v2/` 目录
- [ ] 初始化项目
- [ ] 配置开发环境
- [ ] 编写基础组件

### 模块重构

- [ ] Auth 模块
- [ ] Chat 模块
- [ ] Consultation 模块
- [ ] Payment 模块
- [ ] Document 模块
- [ ] News 模块
- [ ] Lawyer 模块
- [ ] Settlement 模块

### 测试与部署

- [ ] 单元测试
- [ ] E2E 测试
- [ ] 性能测试
- [ ] 生产部署

---

**计划制定**: 2024年  
**最后更新**: 2026年2月6日  
**负责人**: 前端团队

---

> ⚠️ **注意**: 这是一个激进的重构计划，允许删除旧代码。请在执行前确保:
> 1. 完整备份现有代码
> 2. 获得所有利益相关者同意
> 3. 准备充分的测试环境

---

## 十一、旧前端迁移指南 (2026年2月新增)

### 11.1 可迁移模块清单

| 模块 | 优先级 | 状态 | 来源目录 | 说明 |
|-----|--------|------|---------|------|
| Payment | P0 | 待迁移 | `frontend/src/features/payment` | 支付系统完整 |
| Lawyer | P0 | 待迁移 | `frontend/src/features/lawyer` | 律师工作台完整 |
| Chat 增强 | P1 | 待迁移 | `frontend/src/features/chat` | 分享、导出、评价 |
| Forum | P2 | 待迁移 | `frontend/src/features/forum` | 社区功能 |
| News | P2 | 待迁移 | `frontend/src/features/news` | 资讯功能 |
| Document | P1 | 待迁移 | `frontend/src/features/document` | 文档功能 |

### 11.2 迁移优先级

```
P0 (核心业务):
├── Payment 支付模块
│   ├── 订单管理 (创建、支付、取消)
│   ├── 余额查询
│   ├── 交易记录
│   └── 银行卡管理
│
└── Lawyer 律师模块
    ├── 律师认证
    ├── 咨询管理
    ├── 回复模板
    ├── 日程管理
    ├── 收入统计
    └── 提现管理

P1 (核心功能):
├── Chat 增强
│   ├── 会话分享链接
│   ├── 会话导出
│   └── 消息评价
│
└── Document 文档模块

P2 (扩展功能):
├── Forum 社区
└── News 资讯
```

### 11.3 迁移自旧前端的设计亮点

#### 11.3.1 API 客户端设计

```typescript
// 借鉴自 frontend/src/api/client.ts
// 1. ApiException 统一错误类
export class ApiException extends Error {
  constructor(
    public readonly code: string,
    public readonly message: string,
    public readonly details?: unknown,
    public readonly requestId?: string,
    public readonly status?: number
  ) {
    super(message);
    this.name = 'ApiException';
  }
}

// 2. 流式请求 (SSE)
export function streamPost(
  url: string,
  data: unknown,
  options: StreamOptions
): AbortController {
  // 使用 fetch + ReadableStream 实现流式响应
}

// 3. Token 刷新队列机制
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];
```

#### 11.3.2 安全设计

```typescript
// 内存存储 Token (比 localStorage 更安全)
let authToken: string | null = null;

export function getToken(): string | null {
  return authToken;
}

export function setToken(token: string | null): void {
  authToken = token;
}
```

#### 11.3.3 React Query Hooks 规范

```typescript
// 借鉴自 frontend/src/features/chat/hooks/useChatSession.ts
const chatQueryKeys = {
  all: ['chat'] as const,
  sessions: () => [...chatQueryKeys.all, 'sessions'] as const,
  session: (sessionId: string) => [...chatQueryKeys.sessions(), sessionId] as const,
};

// 完整的 CRUD hooks
export const useChatSessions = (params?: { skip?: number; limit?: number }) => {
  return useQuery({
    queryKey: [...chatQueryKeys.sessions(), params],
    queryFn: () => chatApi.getSessions(params),
    staleTime: 5 * 60 * 1000,
  });
};
```

### 11.4 迁移步骤

#### Step 1: 迁移 API 层
1. 复制 `frontend/src/features/{module}/api.ts` → `features/{module}/api/index.ts`
2. 更新导入路径 (`@/api/client` → `@/shared/lib/api/client`)
3. 添加类型定义

#### Step 2: 迁移 Hooks
1. 复制 `frontend/src/features/{module}/hooks/*.ts` → `features/{module}/hooks/`
2. 更新导入路径
3. 确保 queryKeys 规范

#### Step 3: 迁移组件
1. 复制 `frontend/src/features/{module}/components/` → `features/{module}/components/`
2. 重构为函数式组件
3. 添加类型注解

#### Step 4: 迁移页面
1. 复制 `frontend/src/features/{module}/pages/` → `pages/{module}/`
2. 更新路由配置

### 11.5 迁移检查清单

- [ ] API 类型定义完整
- [ ] 错误处理统一 (ApiException)
- [ ] React Query hooks 规范 (queryKeys)
- [ ] 组件类型注解 (JSX.Element)
- [ ] ESLint 零错误
- [ ] 单元测试覆盖 >80%