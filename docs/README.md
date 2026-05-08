# 百姓法律助手

一站式法律服务平台

## 项目状态

> **当前版本**: v2.0.0
> **最后更新**: 2026-05-07
> **项目状态**: 🟡 生产就绪（核心功能完成，待上线前验证）
> **架构模式**: 微服务 + BFF (Backend for Frontend)

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

| 服务 | 端口 | 说明 |
|------|------|------|
| **legal-service** | 8008 | 法律咨询服务 |
| **community-service** | 8007 | 社区/论坛服务 |
| **order-service** | 8004 | 订单/支付服务 |
| **news-service** | 8006 | 新闻服务（含评论/订阅） |
| **search-service** | 8009 | 跨服务聚合搜索 |
| **recommendation-service** | 8010 | 个性化推荐 |
| **notification-service** | 8005 | 通知服务（含模板系统） |
| **user-service** | 8003 | 用户管理 |
| **ai-service** | 8011 | AI 对话服务 |
| **knowledge-service** | 8081 | 知识库服务 |
| **points-service** | 8012 | 积分服务 |
| **archive-service** | 8013 | 档案服务 |

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
├── backend/              # BFF 层 (FastAPI)
├── frontend-v2/          # 前端应用 (React + Vite)
├── services/             # 微服务集群
│   ├── common/           # 共享模块
│   ├── legal-service/
│   ├── community-service/
│   ├── order-service/
│   ├── news-service/
│   ├── search-service/
│   ├── recommendation-service/
│   ├── notification-service/
│   ├── user-service/
│   ├── ai-service/
│   ├── knowledge-service/
│   ├── points-service/
│   └── archive-service/
├── deploy/               # 部署配置 (APISIX/systemd)
├── docs/                 # 项目文档
├── scripts/              # 运维脚本
├── knowledge_base/       # 法律知识库
├── helm/                 # Kubernetes 部署配置
├── nginx/                # Nginx 配置
├── prometheus/           # 监控配置
├── grafana/              # Grafana 仪表盘
└── .github/workflows/    # CI/CD 流水线
```

## 快速开始

### Docker Compose 一键启动

```bash
# 克隆项目后，进入项目根目录

# 生成安全密钥
bash scripts/generate_secrets.sh

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入生成的密钥

# 启动所有服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 初始化数据库
docker exec -i baixing_db_prod bash < scripts/init_db_prod.sh

# 查看服务状态
docker compose ps
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
python -m venv venv
source venv/bin/activate
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
| [运维手册](./OPERATIONS.md) | 日常运维操作 |
| [生产就绪报告](./PRODUCTION_READINESS_REPORT.md) | 上线差距分析 |

### 知识库

| 文档 | 说明 |
|------|------|
| [法律知识库](../knowledge_base/) | 法律法规 JSON |

## CI/CD 状态

- 主流水线：`.github/workflows/ci-cd.yml`
- 安全扫描：`.github/workflows/security-scan.yml`
- 契约测试：`.github/workflows/pact.yml`
- 自动化测试：`.github/workflows/test.yml`
- 类型检查：`.github/workflows/type-check.yml`

## 许可证

MIT License - 查看 [LICENSE](../LICENSE) 了解详情
