# 百姓法律助手

面向法律服务场景的全栈 Web 应用，采用微服务 + BFF 架构。

## 项目状态

- **当前版本**: v3.0
- **最后更新**: 2026-05-11
- **项目状态**: 生产就绪

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS + Zustand |
| BFF | FastAPI + SQLAlchemy 2.0 (异步) |
| 微服务 | FastAPI + PostgreSQL + Redis + Kafka |
| AI | OpenAI API + LangChain + RAG + pgvector |
| 网关 | APISIX |
| 部署 | Docker Compose + Kubernetes (Helm) |
| 监控 | Prometheus + Grafana + OpenTelemetry |

## 目录结构

```
.
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
├── deploy/               # 部署配置 (APISIX / systemd)
├── docs/                 # 项目文档
├── scripts/              # 运维脚本
├── helm/                 # Kubernetes Helm Charts
├── nginx/                # Nginx 反向代理配置
├── prometheus/           # Prometheus 监控配置
└── .github/workflows/    # CI/CD 流水线
```

## 快速开始

### Docker Compose 一键启动

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

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

## 文档

详细文档请参阅 [docs/](docs/) 目录：

### 核心文档

| 文档 | 说明 |
|------|------|
| [项目概览](docs/README.md) | 完整项目介绍与文档导航 |
| [架构设计](docs/ARCHITECTURE.md) | 系统架构与设计模式 |
| [API 参考](docs/API.md) | API 接口文档 |
| [开发指南](docs/DEVELOPMENT.md) | 本地开发流程与规范 |
| [功能清单](docs/FEATURES.md) | 功能特性列表 |
| [v3.0 迭代计划](docs/V3_ITERATION_PLAN.md) | v3.0迭代（已完成） |
| [v3.0 验收报告](docs/V3_ACCEPTANCE_REPORT.md) | v3.0验收结果（已通过） |

### 微服务文档

| 服务 | 端口 | 说明 | 文档 |
|------|------|------|------|
| Backend BFF | 8000 | API 聚合层 | [backend-bff.md](docs/services/backend-bff.md) |
| User Service | 8001 | 用户认证与会员 | [user-service.md](docs/services/user-service.md) |
| Payment Channel | 8002 | 支付渠道 | [payment-channel-service.md](docs/services/payment-channel-service.md) |
| Embedding | 8003 | 向量嵌入 | [embedding-service.md](docs/services/embedding-service.md) |
| Order | 8004 | 订单管理 | [order-service.md](docs/services/order-service.md) |
| AI | 8005 | AI 对话 | [ai-service.md](docs/services/ai-service.md) |
| News | 8006 | 新闻资讯 | [news-service.md](docs/services/news-service.md) |
| Community | 8007 | 社区论坛 | [community-service.md](docs/services/community-service.md) |
| Legal | 8008 | 法律咨询 | [legal-service.md](docs/services/legal-service.md) |
| Search | 8009 | 搜索服务 | [search-service.md](docs/services/search-service.md) |
| Recommendation | 8010 | 推荐服务 | [recommendation-service.md](docs/services/recommendation-service.md) |
| Notification | 8011 | 通知服务 | [notification-service.md](docs/services/notification-service.md) |
| Points | 8012 | 积分系统 | [points-service.md](docs/services/points-service.md) |
| Archive | 8013 | 档案服务 | [archive-service.md](docs/services/archive-service.md) |
| Knowledge | 8081 | 知识库 | [knowledge-service.md](docs/services/knowledge-service.md) |
| Frontend | 3000 | 前端应用 | [frontend.md](docs/services/frontend.md) |

## 许可证

MIT License
