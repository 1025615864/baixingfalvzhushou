# 📊 百姓法律助手 - 项目架构报备报告

**生成时间**: 2026-05-07  
**分支状态**: main (领先 origin/main 9 个提交，工作区干净)  
**架构模式**: 微服务 + BFF (Backend for Frontend)

---

## 一、整体架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户请求入口                               │
├──────────────┬──────────────────┬───────────────────────────────┤
│   Web 端      │   移动端 (未来)   │     第三方 API 调用            │
│  React/Vite  │                  │                               │
└──────┬───────┴──────────────────┴───────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│                     APISIX API 网关                              │
│              (路由/限流/认证/日志)                                │
└──────┬──────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│                    Backend (BFF 层)                              │
│              FastAPI - 业务聚合层                                  │
│              (API聚合/请求编排/数据适配)                           │
└──────┬──────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│                     微服务集群                                    │
│  ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐             │
│  │  legal   │ │community│ │  order  │ │  news    │             │
│  │ service  │ │ service │ │ service │ │ service  │             │
│  └──────────┘ └─────────┘ └─────────┘ └──────────┘             │
│  ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐             │
│  │ search   │ │recommen-│ │ user    │ │ ai       │             │
│  │ service  │ │dation   │ │ service │ │ service  │             │
│  └──────────┘ └─────────┘ └─────────┘ └──────────┘             │
└──────┬──────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│                     基础设施层                                    │
│  PostgreSQL  Redis  Kafka  Prometheus  Grafana  Alertmanager    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、微服务清单与状态

### 2.1 核心业务服务

| 服务名 | 端口 | 目录 | 状态 | 完成度 | 备注 |
|--------|------|------|------|--------|------|
| **legal-service** | 8008 | `services/legal-service/` | ✅ 完整 | 95% | 法律咨询核心服务，含 Alembic 迁移 |
| **community-service** | 8007 | `services/community-service/` | ✅ 完整 | 90% | 社区/论坛服务 |
| **order-service** | 8004 | `services/order-service/` | ✅ 完整 | 85% | 订单/支付服务 |
| **news-service** | 8006 | `services/news-service/` | ✅ 完整 | 85% | 新闻服务 + 评论 + 订阅 |
| **search-service** | 8009 | `services/search-service/` | ✅ 完整 | 80% | 跨服务聚合搜索 (新) |
| **recommendation-service** | 8010 | `services/recommendation-service/` | ✅ 完整 | 75% | 个性化推荐 (新) |
| **user-service** | 8003 | `services/user-service/` | ✅ 完整 | 90% | 用户管理 + AI 配置 |
| **ai-service** | 8011 | `services/ai-service/` | 🟡 基础 | 60% | AI 对话服务，待完善 |
| **notification-service** | 8005 | `services/notification-service/` | 🟡 基础 | 50% | 路由层完成，待提取服务层 |

### 2.2 支撑服务

| 服务名 | 目录 | 状态 | 完成度 | 备注 |
|--------|------|------|--------|------|
| **embedding-service** | `services/embedding-service/` | 🟡 占位 | 30% | 向量嵌入服务 |
| **knowledge-service** | `services/knowledge-service/` | 🟡 基础 | 40% | 知识库服务 |
| **archive-service** | `services/archive-service/` | 🟡 占位 | 20% | 归档服务 |
| **points-service** | `services/points-service/` | 🟡 基础 | 50% | 积分服务 |

### 2.3 共享模块

| 模块名 | 目录 | 状态 | 功能 |
|--------|------|------|------|
| **common** | `services/common/` | ✅ 完整 | 共享基础设施包 |
| - api/error_handler | | ✅ | 统一错误处理 |
| - cache | | ✅ | Redis 缓存 |
| - client/http_client | | ✅ | HTTP 客户端 |
| - config/loader | | ✅ | 配置管理 (Consul KV) |
| - events/kafka | | ✅ | Kafka 事件系统 |
| - grpc/client | | ✅ | gRPC 客户端 |
| - middleware/auth | | ✅ | 认证中间件 |
| - middleware/telemetry | | ✅ | OpenTelemetry |
| - outbox/publisher | | ✅ | Outbox 模式 |
| - saga/orchestrator | | ✅ | Saga 分布式事务 |
| - security/jwt_manager | | ✅ | JWT 密钥轮换 |
| - security/secrets | | ✅ | 密钥管理 |
| - services/i18n | | ✅ | 国际化 |
| - testing/fixtures | | ✅ | 测试工具 |
| - vector | | ✅ | 向量操作 |
| - proto | | ✅ | gRPC 定义 |

---

## 三、BFF 层 (Backend)

### 3.1 结构概览

| 层级 | 目录 | 文件数 | 状态 |
|------|------|--------|------|
| **配置** | `app/config/` | 3 | ✅ 领域拆分 |
| **核心** | `app/core/` | 15 | ✅ 健康检查/指标/生命周期 |
| **数据库** | `app/database/` | 6 | ✅ 引擎/会话/迁移/修复 |
| **中间件** | `app/middleware/` | 3 | ✅ IP白名单/限流/日志清洗 |
| **模型** | `app/models/` | 22 | ✅ 完整的领域模型 |
| **路由** | `app/routers/` | 8 | 🟡 部分聚合到 BFF |
| **Schema** | `app/schemas/` | 11 | ✅ Pydantic 模型 |
| **服务** | `app/services/` | 14 | 🟡 混合了业务和工具 |
| **工具** | `app/utils/` | 32 | ⚠️ 数量较多，需精简 |
| **脚本** | `scripts/` | 22 | ✅ 运维工具集 |
| **测试** | `tests/` | 100+ | ✅ 高覆盖率 |

### 3.2 待改进项

1. **utils/ 目录过于庞大** (32个文件) - 部分工具应迁移到 common 模块或各微服务
2. **routers/ 层** - 需要进一步向微服务迁移，BFF 只做聚合
3. **services/ 层** - 需区分 BFF 聚合服务和底层业务逻辑

---

## 四、前端架构

| 项目 | 技术栈 | 状态 | 完成度 |
|------|--------|------|--------|
| **frontend-v2** | React + Vite + TypeScript + Tailwind | ✅ 运行中 | 80% |
| 状态管理 | Zustand | ✅ | - |
| 数据获取 | React Query | ✅ | - |
| 测试 | Vitest + Playwright | ✅ | - |
| UI 组件 | 自组件库 (Badge, Card, Input, Modal, Tabs, Toast) | 🟡 基础 | 40% |
| E2E 测试 | Playwright (11 个 spec 文件) | ✅ | 70% |

### 前端待改进
- UI 组件库不完整，缺少 Table, Form, Select, DatePicker 等
- 页面数量有限 (仅 6 个页面)
- 缺少设计系统文档

---

## 五、基础设施

### 5.1 数据层

| 组件 | 版本 | 用途 | 状态 |
|------|------|------|------|
| PostgreSQL | 15-alpine | 主数据库 | ✅ Docker Compose |
| Redis | 7-alpine | 缓存/会话/限流 | ✅ Docker Compose |
| Kafka | 3.6.1 | 事件驱动/异步消息 | ✅ Docker Compose (含 SASL) |
| pgvector | - | 向量搜索 | 🟡 待启用 |

### 5.2 监控层

| 组件 | 用途 | 状态 |
|------|------|------|
| Prometheus | 指标采集 | ✅ 配置完整 |
| Grafana | 可视化面板 | ✅ 包含业务面板 |
| Alertmanager | 告警路由 | ✅ 配置完整 |
| 告警规则 | | ✅ 多套规则 (backend/api/performance/ai) |

### 5.3 网关层

| 组件 | 用途 | 状态 |
|------|------|------|
| APISIX | API 网关 | ✅ 路由配置 |
| Nginx | 反向代理/静态文件 | ✅ 生产配置 |

### 5.4 部署

| 方式 | 状态 | 备注 |
|------|------|------|
| Docker Compose | ✅ 完整 | 多环境 (dev/prod/microservices/monitoring) |
| Helm (K8s) | ✅ 基础 | Chart.yaml + values.yaml |
| CI/CD (GitHub Actions) | ✅ 完整 | 10 个 workflow 文件 |

---

## 六、CI/CD 流水线

### 6.1 Workflow 清单

| Workflow | 用途 | 状态 |
|----------|------|------|
| `ci-cd.yml` | 主流水线 (微服务并行测试 + Docker 构建 + 部署) | ✅ 最新 |
| `ci.yml` | 旧版 CI (已废弃) | ⚠️ 可删除 |
| `code-quality.yml` | 代码质量检查 | ✅ |
| `test.yml` | 测试运行 | ✅ |
| `type-check.yml` | TypeScript 类型检查 | ✅ |
| `pr-checks.yml` | PR 检查 | ✅ |
| `security-scan.yml` | 安全扫描 | ✅ |
| `pact.yml` | 契约测试 | ✅ |
| `release.yml` | 发布流程 | ✅ |
| `post-deploy-smoke.yml` | 部署后冒烟测试 | ✅ |

### 6.2 CI/CD 特点
- **并行测试**: 7 个服务同时运行测试
- **Docker 矩阵构建**: 所有服务独立构建
- **环境分离**: staging (develop 分支) / production (main 分支)
- **安全扫描**: Trivy 漏洞扫描
- **通知集成**: Slack Webhook 部署通知

---

## 七、测试覆盖

### 7.1 测试类型

| 测试类型 | 位置 | 覆盖范围 | 状态 |
|----------|------|----------|------|
| 单元测试 | `backend/tests/` | 100+ 测试文件 | ✅ 高覆盖 |
| 契约测试 | `services/*/tests/test_contracts.py` | 5 个服务 | ✅ 新增 |
| 集成测试 | `services/tests/` | Saga/Outbox/限流/安全 | ✅ |
| E2E 测试 | `frontend-v2/e2e/` | 11 个场景 spec | ✅ |
| Playwright E2E | `backend/tests/e2e/` | 支付等 | ✅ |

### 7.2 测试工具
- **pytest** + **pytest-asyncio** (Python)
- **Vitest** + **React Testing Library** (前端单元)
- **Playwright** (E2E)
- **httpx** (异步 HTTP 客户端测试)

---

## 八、文档体系

| 文档 | 位置 | 内容 | 状态 |
|------|------|------|------|
| README | `README.md` | 项目总览 | ✅ |
| 架构设计 | `docs/ARCHITECTURE.md` | 架构文档 | ✅ |
| API 文档 | `docs/API.md` | API 参考 | ✅ |
| 开发指南 | `docs/DEVELOPMENT.md` | 开发流程 | ✅ |
| 部署指南 | `docs/DEPLOYMENT.md` | 部署流程 | ✅ |
| 运维手册 | `docs/OPERATIONS.md` | 运维指南 | ✅ |
| 服务通信规范 | `docs/service-communication-spec.md` | 服务间通信 | ✅ |
| 分布式事务设计 | `docs/DISTRIBUTED_TRANSACTION_DESIGN.md` | Saga 设计 | ✅ |
| 契约测试设计 | `docs/CONTRACT_TESTING_DESIGN.md` | Pact 设计 | ✅ |
| 代码评审清单 | `docs/CODE_REVIEW_CHECKLIST.md` | 评审标准 | ✅ |
| 特性清单 | `docs/FEATURES.md` | 功能清单 | ✅ |

---

## 九、项目统计

| 指标 | 数值 |
|------|------|
| **微服务数量** | 12 (含支撑服务) |
| **完整度 80%+ 服务** | 7 个 |
| **Docker 服务** | 7 个 (有 Dockerfile) |
| **BFF 测试文件** | 100+ |
| **前端 E2E 场景** | 11 个 |
| **CI/CD Workflow** | 10 个 |
| **Prometheus 告警规则** | 7 套 |
| **文档数量** | 15+ 份核心文档 |
| **代码行数 (估计)** | ~50,000+ |
| **本地领先远程** | 9 个提交 (未推送) |

---

## 十、当前存在的问题与风险

### 10.1 🔴 高优先级

| 问题 | 影响 | 建议 |
|------|------|------|
| **本地代码未推送** | 远程代码落后 9 个提交 | 尽快推送到远程仓库 |
| **部分服务未 Docker 化** | news/search/recommendation/notification 等缺少 Dockerfile 或不够完整 | 补充 Dockerfile 并验证 |
| **BFF 层仍有业务逻辑** | services/ 目录包含较多业务逻辑 | 持续迁移到微服务 |
| **utils/ 目录膨胀** | 32 个文件职责不清 | 按领域拆分迁移 |

### 10.2 🟡 中优先级

| 问题 | 影响 | 建议 |
|------|------|------|
| **前端组件库不完整** | 缺少常用 UI 组件 | 补充 Table/Form/Select 等 |
| **前端页面有限** | 仅 6 个页面 | 补充完整页面体系 |
| **部分微服务测试缺失** | ai-service/notification-service 等无测试 | 补充契约测试 |
| **CI workflow 冗余** | ci.yml 等已废弃但未删除 | 清理冗余 workflow |
| **gRPC 定义不完整** | proto 文件定义较少 | 补充关键服务的 gRPC 定义 |

### 10.3 🟢 低优先级

| 问题 | 影响 | 建议 |
|------|------|------|
| **文档未实时更新** | 部分文档可能滞后于代码 | 建立文档更新机制 |
| **Helm Chart 待完善** | K8s 部署配置较基础 | 补充完整 Helm 配置 |
| **缺少 API Mock 服务** | 前端开发需 mock | 考虑引入 Mock 服务 |

---

## 十一、技术栈总结

### 后端
- **框架**: FastAPI (BFF + 微服务)
- **数据库**: PostgreSQL 15 (AsyncPG)
- **缓存**: Redis 7
- **消息队列**: Kafka 3.6.1 (SASL 认证)
- **ORM**: SQLAlchemy 2.0 (async)
- **数据验证**: Pydantic 2.x
- **服务发现**: Consul KV
- **分布式事务**: Saga + Outbox 模式
- **API 网关**: APISIX
- **监控**: Prometheus + Grafana + Alertmanager

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **CSS**: Tailwind CSS
- **状态管理**: Zustand
- **数据获取**: React Query
- **测试**: Vitest + Playwright + MSW
- **路由**: React Router

### DevOps
- **容器化**: Docker + Docker Compose
- **编排**: Kubernetes (Helm)
- **CI/CD**: GitHub Actions
- **代码质量**: Black + isort + Ruff + ESLint
- **安全扫描**: Trivy

---

## 十二、下一步建议

1. **立即**: 推送 9 个未提交到远程仓库
2. **短期**: 完善 ai-service 和 notification-service 的服务层 + 测试
3. **短期**: 精简 backend/utils/ 目录
4. **中期**: 补充前端组件库和页面
5. **中期**: 完善 K8s Helm Chart 配置
6. **长期**: 逐步将 BFF 层业务逻辑迁移到微服务

---

*报告生成完毕 - 2026-05-07*
