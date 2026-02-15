# 百姓助手 Frontend v2

全新的百姓助手前端项目，基于 React 18 + TypeScript 5 + Vite 构建。

## 技术栈

- **框架**: React 18.2
- **语言**: TypeScript 5.3
- **构建**: Vite 5
- **路由**: React Router 6.20
- **状态管理**: Zustand + React Query
- **样式**: Tailwind CSS 3.4
- **测试**: Vitest + React Testing Library
- **代码规范**: ESLint + Prettier

## 项目结构

```
frontend-v2/
├── src/
│   ├── app/              # 应用入口和全局配置
│   │   ├── layouts/      # 布局组件
│   │   ├── providers/    # 全局 Provider
│   │   └── styles/       # 全局样式
│   ├── features/         # 功能模块
│   │   ├── auth/         # 认证模块 
│   │   ├── chat/         # AI 对话 
│   │   ├── consultation/ # 法律咨询
│   │   ├── document/     # 文档管理
│   │   ├── lawyer/       # 律师端 
│   │   ├── news/         # 法律资讯
│   │   ├── payment/      # 支付系统 
│   │   └── settlement/   # 结算系统
│   ├── pages/            # 页面组件
│   ├── shared/           # 共享资源
│   │   ├── components/   # 通用组件
│   │   ├── lib/          # 工具库
│   │   └── utils/        # 工具函数
│   ├── widgets/          # 业务组件
│   └── test/             # 测试配置
├── tests/                # E2E 测试
└── public/               # 静态资源
```

## 功能模块状态

| 模块 | 状态 | 说明 |
|-----|------|------|
| Auth | ✅ 已完成 | 登录、注册、Token 管理 |
| Chat | ✅ 已完成 | AI 对话、消息管理 |
| Notification | ✅ 已完成 | 通知系统、WebSocket |
| Payment | 🔄 待迁移 | 从旧前端迁移 |
| Lawyer | 🔄 待迁移 | 从旧前端迁移 |
| Consultation | 📋 规划中 | 律师咨询 |
| Document | 📋 规划中 | 文档生成 |
| News | 📋 规划中 | 法律资讯 |
| Forum | 📋 规划中 | 社区论坛 |

## 快速开始

```bash
# 安装依赖
npm install

# 复制环境变量
cp .env.example .env

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npm test
```

## 代码规范

- 零 `any` 类型政策
- 所有组件必须显式返回类型 `JSX.Element`
- 使用 Feature-Based 架构组织代码
- 测试覆盖率 >80%
- 借鉴旧前端设计：ApiException 错误类、内存 Token 存储、流式请求

## 迁移自旧前端的设计亮点

### 1. 统一错误处理

```typescript
// 借鉴旧前端 ApiException 设计
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
```

### 2. 安全 Token 存储

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

### 3. React Query Hooks 规范

```typescript
// queryKeys 模式
const queryKeys = {
  all: ['payment'] as const,
  orders: (params) => [...queryKeys.all, 'orders', params] as const,
};
```

## 文档

- [开发贡献规范](CONTRIBUTING.md)
- [重构计划](REFACTOR_PLAN.md)