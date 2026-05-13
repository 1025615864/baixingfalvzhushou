# 前端应用 (Frontend)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | frontend-v2 |
| 端口 | 3000 (Docker) / 5173 (开发) |
| 技术栈 | React 18 + TypeScript + Vite + Tailwind CSS |
| 构建产物 | Nginx 静态资源服务 |
| 健康检查 | GET / |

## 服务描述

百姓法律助手前端应用，基于 React 18 + TypeScript 构建的单页应用（SPA）。采用 Zustand 状态管理、TanStack React Query 数据获取、Ant Design 组件库，提供 AI 法律咨询、律师服务、社区论坛、新闻资讯、积分商城等完整用户界面。

## 技术架构

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2.0 | UI 框架 |
| TypeScript | 5.3.3 | 类型安全 |
| Vite | 5.4.10 | 构建工具 |
| Tailwind CSS | 3.4.0 | 原子化 CSS |
| Zustand | - | 全局状态管理 |
| TanStack React Query | - | 服务端数据获取与缓存 |
| Ant Design | 5.21.3 | 企业级 UI 组件库 |
| React Router DOM | 6.20.0 | 路由管理 |
| Framer Motion | 12.34.0 | 声明式动画 |
| Recharts | 3.7.0 | 数据可视化 |
| Playwright | - | E2E 测试 |

## 页面路由

| 路径 | 页面 | 说明 |
|------|------|------|
| / | Home | 首页 |
| /chat | Chat | AI 法律咨询 |
| /lawyers | Lawyer | 律师服务 |
| /news | News | 新闻资讯 |
| /login | Login | 登录注册 |
| /knowledge | Knowledge | 知识库 |
| /profile | Profile | 个人中心 |
| /payment | Payment | 支付 |
| /membership | Membership | 会员中心 |
| /points | Points | 积分商城 |
| /community | Community | 社区论坛 |
| /contract-review | ContractReview | 合同审查 |

## 目录结构

```
frontend-v2/src/
├── app/                    # 应用入口
│   ├── App.tsx            # 根组件
│   └── styles/            # 全局样式
├── components/            # 通用 UI 组件
│   └── ui/                # 基础组件 (Card, Form, Tabs)
├── features/              # 功能模块
│   ├── faq/              # 常见问题
│   ├── news/             # 新闻资讯
│   ├── notification/     # 通知中心
│   ├── search/           # 搜索
│   ├── security/         # 安全设置
│   ├── points/           # 积分系统
│   ├── promotion/        # 推广中心
│   ├── enterprise/       # 企业服务
│   ├── settlement/       # 结算
│   ├── payment/          # 支付
│   ├── post/             # 帖子
│   ├── forum/            # 论坛
│   └── membership/       # 会员中心
├── pages/                # 页面组件
├── shared/               # 共享资源
│   ├── hooks/           # 自定义 Hooks
│   ├── lib/             # 工具库 (API, logger)
│   ├── store/           # 状态管理
│   └── utils/           # 通用工具
├── test/                 # 测试配置
└── widgets/              # 小部件
```

## API 代理配置

开发环境通过 Vite 代理转发到各微服务：

| 前端路径 | 目标服务 | 端口 |
|----------|----------|------|
| /api/v1/auth | user-service | 8001 |
| /api/v1/users | user-service | 8001 |
| /api/v1/payment | payment-channel-service | 8002 |
| /api/v1/legal | legal-service | 8008 |
| /api/v1/ai | ai-service | 8005 |
| /api/v1/news | news-service | 8006 |
| /api/v1/community | community-service | 8007 |
| /api/v1/points | points-service | 8012 |
| /api/v1/notifications | notification-service | 8011 |
| /api/v1/recommendations | recommendation-service | 8010 |
| /api/v1/search | search-service | 8009 |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| backend-bff | HTTP | 主要 API 聚合入口 |
| 所有微服务 | HTTP (代理) | 开发环境直接代理 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| VITE_API_BASE_URL | http://localhost:8000 | API 基础地址 |
| VITE_WS_URL | ws://localhost:8000 | WebSocket 地址 |

## 部署信息

- Dockerfile: frontend-v2/Dockerfile
- 生产环境: Nginx 静态资源服务
- 健康检查: GET /
- 资源限制: CPU 0.5核 / 内存 256MB
