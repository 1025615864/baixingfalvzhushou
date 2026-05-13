# 百姓法律助手

一站式法律服务平台

## 项目状态

- **当前版本**: v3.0
- **最后更新**: 2026-05-11
- **项目状态**: 生产就绪
- **架构模式**: 微服务 + BFF (Backend for Frontend)

## 项目概述

百姓法律助手是一个专注于法律服务领域的全栈Web应用平台，采用**微服务架构**，旨在为普通民众提供便捷、专业、高效的法律服务。

### 核心功能

| 功能模块 | 说明 | 状态 |
|----------|------|------|
| AI法律咨询 | 基于 LangChain + RAG 知识库的智能法律问答 | ✅ 已完成 |
| 律师服务 | 在线预约、推荐、主页展示 | ✅ 已完成 |
| 合同审查 | AI 自动合同审查与风险提示 | ✅ 已完成 |
| 社区论坛 | 法律知识分享、案例讨论 | ✅ 已完成 |
| 新闻资讯 | 法律新闻、案例报道、政策解读 | ✅ 已完成 |
| 个性化推荐 | 基于用户兴趣的智能推荐 | ✅ 已完成 |
| 全局搜索 | 跨服务聚合搜索 | ✅ 已完成 |
| 通知系统 | 实时通知、模板管理 | ✅ 已完成 |
| 订单支付 | 订单管理 + 支付宝/微信支付 | ✅ 已完成 |
| 积分体系 | 签到、积分兑换 | ✅ 已完成 |

## 技术架构

### 微服务集群

| 服务 | 端口 | 说明 | 详细文档 |
|------|------|------|----------|
| **backend (BFF)** | 8000 | BFF 聚合层 | [backend-bff.md](services/backend-bff.md) |
| **user-service** | 8001 | 用户管理 | [user-service.md](services/user-service.md) |
| **payment-channel-service** | 8002 | 支付通道 | [payment-channel-service.md](services/payment-channel-service.md) |
| **embedding-service** | 8003 | 向量嵌入 | [embedding-service.md](services/embedding-service.md) |
| **order-service** | 8004 | 订单服务 | [order-service.md](services/order-service.md) |
| **ai-service** | 8005 | AI 对话 | [ai-service.md](services/ai-service.md) |
| **news-service** | 8006 | 新闻服务 | [news-service.md](services/news-service.md) |
| **community-service** | 8007 | 社区论坛 | [community-service.md](services/community-service.md) |
| **legal-service** | 8008 | 法律咨询 | [legal-service.md](services/legal-service.md) |
| **search-service** | 8009 | 搜索服务 | [search-service.md](services/search-service.md) |
| **recommendation-service** | 8010 | 推荐服务 | [recommendation-service.md](services/recommendation-service.md) |
| **notification-service** | 8011 | 通知服务 | [notification-service.md](services/notification-service.md) |
| **points-service** | 8012 | 积分服务 | [points-service.md](services/points-service.md) |
| **archive-service** | 8013 | 档案服务 | [archive-service.md](services/archive-service.md) |
| **knowledge-service** | 8081 | 知识库 | [knowledge-service.md](services/knowledge-service.md) |
| **frontend-v2** | 3000 | 前端应用 | [frontend.md](services/frontend.md) |

### 后端技术栈

| 技术 | 用途 |
|------|------|
| FastAPI | Web 框架 |
| SQLAlchemy 2.0 | ORM (异步) |
| PostgreSQL 15 | 主数据库 |
| Redis 7 | 缓存/会话/限流 |
| Kafka 3.6 | 事件驱动/异步消息 |
| APISIX | API 网关 |
| Alembic | 数据库迁移 |
| OpenTelemetry | 分布式追踪 |
| Prometheus + Grafana | 监控与告警 |

### 前端技术栈

| 技术 | 用途 |
|------|------|
| React 18 | UI 框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Tailwind CSS | CSS 框架 |
| Zustand | 状态管理 |
| React Query | 数据获取 |
| React Router | 路由管理 |
| Playwright | E2E 测试 |

### AI 与数据

| 技术 | 用途 |
|------|------|
| OpenAI API | 大语言模型 |
| LangChain | AI 应用框架 |
| RAG | 知识库检索 |
| pgvector | 向量数据库 |

### 部署与运维

| 技术 | 用途 |
|------|------|
| Docker + Compose | 容器化部署 |
| Kubernetes (Helm) | 生产编排 |
| Nginx | 反向代理/静态文件 |
| Certbot | SSL 证书自动续期 |
| GitHub Actions | CI/CD |

## 目录结构

```
百姓法律助手/
├── backend/              # BFF 层 (FastAPI :8000)
├── frontend-v2/          # 前端应用 (React + Vite)
├── services/             # 微服务集群
│   ├── common/           # 共享模块 (gRPC, Kafka, Auth...)
│   ├── ai-service/       # AI 对话服务
│   ├── legal-service/    # 法律咨询服务
│   ├── community-service/# 社区论坛服务
│   ├── news-service/     # 新闻资讯服务
│   ├── user-service/     # 用户管理服务
│   ├── order-service/    # 订单支付服务
│   ├── search-service/   # 搜索服务
│   ├── points-service/   # 积分服务
│   ├── knowledge-service/# 知识库服务
│   ├── archive-service/  # 档案服务
│   ├── embedding-service/# 向量嵌入服务
│   ├── notification-service/# 通知服务
│   ├── payment-channel-service/# 支付通道服务
│   └── recommendation-service/# 推荐服务
├── deploy/               # 部署配置 (APISIX/systemd)
├── docs/                 # 项目文档
├── scripts/              # 运维脚本
├── helm/                 # Kubernetes 部署配置
├── nginx/                # Nginx 配置
├── prometheus/           # 监控配置
└── .github/workflows/    # CI/CD 流水线
```

## 快速开始

### Docker Compose 一键启动

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

服务启动后可访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- Prometheus：http://localhost:9090
- Grafana：http://localhost:3001

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend-v2
npm install
npm run dev
```

## 文档导航

### 开发文档

| 文档 | 说明 |
|------|------|
| [架构设计](./ARCHITECTURE.md) | 系统架构与设计模式 |
| [API 参考](./API.md) | API 接口文档 |
| [开发指南](./DEVELOPMENT.md) | 本地开发流程 |
| [服务通信规范](./service-communication-spec.md) | 微服务间通信标准 |
| [特性清单](./FEATURES.md) | 功能特性列表 |

### 微服务文档

每个微服务的详细文档包含：服务概览、API 端点、数据模型、关联服务、配置项、部署信息。

| 服务 | 文档 | 服务 | 文档 |
|------|------|------|------|
| Backend BFF | [backend-bff.md](services/backend-bff.md) | User | [user-service.md](services/user-service.md) |
| Payment Channel | [payment-channel-service.md](services/payment-channel-service.md) | Embedding | [embedding-service.md](services/embedding-service.md) |
| Order | [order-service.md](services/order-service.md) | AI | [ai-service.md](services/ai-service.md) |
| News | [news-service.md](services/news-service.md) | Community | [community-service.md](services/community-service.md) |
| Legal | [legal-service.md](services/legal-service.md) | Search | [search-service.md](services/search-service.md) |
| Recommendation | [recommendation-service.md](services/recommendation-service.md) | Notification | [notification-service.md](services/notification-service.md) |
| Points | [points-service.md](services/points-service.md) | Archive | [archive-service.md](services/archive-service.md) |
| Knowledge | [knowledge-service.md](services/knowledge-service.md) | Frontend | [frontend.md](services/frontend.md) |

### 设计文档

| 文档 | 说明 |
|------|------|
| [分布式事务设计](./DISTRIBUTED_TRANSACTION_DESIGN.md) | Saga + Outbox 设计 |
| [契约测试设计](./CONTRACT_TESTING_DESIGN.md) | Pact 契约测试 |
| [代码评审清单](./CODE_REVIEW_CHECKLIST.md) | 代码审查标准 |

### 运维文档

| 文档 | 说明 |
|------|------|
| [生产部署指南](./PRODUCTION_DEPLOYMENT_GUIDE.md) | 生产环境部署全流程 |
| [Docker 部署](./DOCKER_DEPLOYMENT.md) | Docker Compose 部署 |
| [运维手册](./OPERATIONS.md) | 日常运维操作 |

### 迭代文档

| 文档 | 说明 |
|------|------|
| [v2.1 迭代计划](./V2.1_ITERATION_PLAN.md) | v2.1迭代进度与验收 |
| [v3.0 迭代计划](./V3_ITERATION_PLAN.md) | v3.0迭代（已完成） |
| [v2.1 验收报告](./V2_ACCEPTANCE_REPORT.md) | v2.1验收结果 |
| [v3.0 验收报告](./V3_ACCEPTANCE_REPORT.md) | v3.0验收结果（已通过） |

### 运维脚本

| 脚本 | 说明 |
|------|------|
| `scripts/health-check.sh` | 14服务健康检查 |
| `scripts/verify-docker-builds.sh` | Docker构建验证 |
| `scripts/production-readiness.sh` | 生产就绪8项检查 |
| `scripts/perf/run-perf-tests.sh` | 性能压测运行器 |

## CI/CD

| Workflow | 说明 |
|----------|------|
| `ci.yml` | 主流水线 (CI + 测试 + 类型检查) |
| `code-quality.yml` | 代码质量 + 安全扫描 |
| `release.yml` | 发布流水线 |
| `pact.yml` | 契约测试 |

## 许可证

MIT License
