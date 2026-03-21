# 百姓助手

百姓助手是一个面向法律服务场景的全栈 Web 项目，当前仓库包含前端、后端、监控、容器编排和配套文档。为了避免入口信息分散，这份 README 只承担两件事：快速说明项目是什么，以及告诉你应该先看哪些文档。

## 项目概览

- 用户侧能力覆盖 AI 法律咨询、律师/律所服务、合同审查、法律文书、支付、会员、积分、通知、论坛、新闻和企业服务。
- 后端位于 `backend/`，以 FastAPI 为核心，配合 SQLAlchemy、Alembic、PostgreSQL、Redis 和 LangChain/OpenAI。
- 前端位于 `frontend-v2/`，使用 React 18、TypeScript、Vite、React Router、TanStack Query 和 Ant Design。
- 运维与观测能力位于根目录和 `prometheus/`、`grafana/`、`alertmanager/`、`helm/`、`nginx/` 等目录。

## 快速定位

- 项目现状快照：[`docs/PROJECT_SNAPSHOT.md`](./docs/PROJECT_SNAPSHOT.md)
- 文档维护方法：[`docs/DOCUMENTATION_WORKFLOW.md`](./docs/DOCUMENTATION_WORKFLOW.md)
- 文档总览：[`docs/README.md`](./docs/README.md)
- 技术架构：[`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)
- 功能清单：[`docs/FEATURES.md`](./docs/FEATURES.md)
- 开发规范：[`docs/DEVELOPMENT.md`](./docs/DEVELOPMENT.md)
- API 文档：[`docs/API.md`](./docs/API.md)
- 运维说明：[`docs/OPERATIONS.md`](./docs/OPERATIONS.md)

## 目录结构

```text
.
├── backend/           FastAPI 后端
├── frontend-v2/       React 前端
├── docs/              项目文档
├── scripts/           辅助脚本
├── data/              数据与模型文件
├── prometheus/        Prometheus 配置
├── grafana/           Grafana 仪表盘与 provisioning
├── alertmanager/      告警配置
├── helm/              Kubernetes 部署配置
└── nginx/             网关配置
```

## 本地运行入口

### Docker Compose

```powershell
docker compose up -d
```

默认会启动这些核心服务：

- 前端：`http://localhost:3000`
- 后端 API：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`
- Prometheus：`http://localhost:19090`
- Grafana：`http://localhost:3001`
- Alertmanager：`http://localhost:9200`

### 分别启动前后端

后端：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```powershell
cd frontend-v2
npm install
npm run dev
```

## 维护说明

- 当前仓库处于活跃迭代中，根目录和各子目录下存在较多未提交改动。
- 若你需要先判断“现在这个项目到底做到哪一步”，请优先阅读 [`docs/PROJECT_SNAPSHOT.md`](./docs/PROJECT_SNAPSHOT.md)。
- 若你需要继续补文档，不建议直接扩写所有大文档，先按 [`docs/DOCUMENTATION_WORKFLOW.md`](./docs/DOCUMENTATION_WORKFLOW.md) 做一次源码核对，再决定更新范围。
