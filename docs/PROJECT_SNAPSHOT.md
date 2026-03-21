# 百姓助手项目现状快照

> 快照日期：2026-03-08
> 说明：本文件基于当前仓库源码结构整理，只记录高置信度、可从代码直接观察到的信息，用作后续更新文档时的基线。

## 1. 项目是什么

百姓助手是一个围绕法律服务场景构建的全栈平台。按当前仓库可见内容判断，它不是单一的“AI 问答应用”，而是一个覆盖咨询、律师服务、内容社区、支付交易、会员积分、企业服务和运维监控的综合系统。

从命名和路由聚合情况来看，当前项目至少覆盖这些业务域：

- AI 法律咨询与聊天
- 律师/律所与律师匹配
- 视频咨询
- 合同审查与模板
- 法律文书商城
- 新闻、论坛、帖子与内容管理
- 支付、订单、结算
- 会员、积分、推荐、通知
- 企业服务、系统配置、后台监控

## 2. 当前技术结构

### 后端

- 主框架：FastAPI
- 入口文件：`backend/app/main.py`
- 路由聚合：`backend/app/routers/__init__.py`
- 依赖特征：SQLAlchemy、Alembic、PostgreSQL、Redis、LangChain、OpenAI、Chroma、Prometheus、Sentry
- 目录分层清晰，已拆分出 `config`、`core`、`database`、`middleware`、`models`、`routers`、`schemas`、`services`、`tasks`、`utils`

根据当前目录统计，后端至少包含：

- 33 个模型文件
- 183 个服务实现文件
- 37 个 Alembic 迁移文件
- 209 个 `test_*.py` 测试文件

### 前端

- 主框架：React 18 + TypeScript + Vite
- 入口文件：`frontend-v2/src/main.tsx`
- 路由入口：`frontend-v2/src/app/providers/Router.tsx`
- 状态/数据层：TanStack Query、Zustand、React Hook Form、Zod
- UI 层：Ant Design 为主，辅以自定义组件和 Framer Motion

根据当前目录统计，前端至少包含：

- 52 个一级 `features` 功能目录
- 14 个 Playwright E2E 规格文件
- 一套按 `app / features / shared / widgets / pages` 组织的模块化结构

### 基础设施与运维

根目录 `docker-compose.yml` 当前可见的核心服务有：

- `db`
- `redis`
- `redis-exporter`
- `backend`
- `prometheus`
- `grafana`
- `alertmanager`
- `frontend`

这说明当前仓库已经把“应用运行”和“可观测性”放在同一个交付面里，而不是单独维护。

## 3. 代码层面的几个重要事实

### 业务边界很宽

从后端路由聚合和前端路由文件都能看出，该项目已经不是早期 MVP 体量。单是路由层就已经覆盖用户、AI、新闻、论坛、知识库、支付、结算、会员、推荐、安全、企业服务、后台管理、视频咨询、法律文书商城等多个域。

### 后端是“聚合式业务服务层”

`backend/app/services/` 规模较大，说明项目的大部分业务复杂度沉在服务层，而不是只写在路由里。后续做文档更新时，若要判断某个功能是否真的上线，不能只看路由声明，通常还要同步检查对应 service、schema、model、migration 与测试。

### 前端是模块化扩展型结构

`frontend-v2/src/features/` 数量较多，且路由使用大量懒加载页面，说明前端正在向“按业务模块拆分”的方向发展。补前端文档时，最可靠的入口是 `Router.tsx` 和每个 feature 的 `api / pages / hooks / types`。

### 监控是正式能力，不是临时脚本

仓库中同时存在 Prometheus、Grafana、Alertmanager 配置，并且 `docker-compose.yml` 直接挂载相关配置。说明监控与告警是系统的一部分，相关文档应视为核心文档，不应放在“可有可无”的附录位置。

## 4. 当前文档状态判断

现有 `docs/` 已经覆盖这些方向：

- 架构：`ARCHITECTURE.md`
- 功能清单：`FEATURES.md`
- 开发规范：`DEVELOPMENT.md`
- API：`API.md`
- 运维：`OPERATIONS.md`
- 集成测试、验收、性能、改进建议等专题文档

但从当前仓库状态看，文档仍然存在几个实际问题：

- 根目录缺少统一入口，第一次进入仓库的人很难判断先看哪里
- 大文档偏重“完整陈述”，不利于快速建立当前状态认知
- 工作区存在大量未提交改动，意味着“项目已完成开发”这类结论容易过时
- 文档与源码之间缺少一份明确的“核对方法”，维护成本偏高

## 5. 推荐把哪些文件当作事实来源

如果后续要判断某个说法是否应该写进文档，优先级建议如下：

1. 运行入口与编排
   - `docker-compose.yml`
   - `docker-compose.dev.yml`
   - `docker-compose.prod.yml`

2. 后端真实能力
   - `backend/app/main.py`
   - `backend/app/routers/__init__.py`
   - `backend/app/services/`
   - `backend/app/models/`
   - `backend/alembic/versions/`

3. 前端真实入口
   - `frontend-v2/package.json`
   - `frontend-v2/src/app/providers/Router.tsx`
   - `frontend-v2/src/features/`

4. 配置与可运行性
   - `backend/.env.example`
   - `frontend-v2/.env.example`

5. 完整性与验证
   - `backend/tests/`
   - `frontend-v2/e2e/`

## 6. 后续文档维护建议

- 根目录 README 负责“入口导航”和“启动方式”，不要塞进太多细节。
- `docs/PROJECT_SNAPSHOT.md` 负责记录当前仓库的高层现状，每次做较大功能合并后更新一次日期和结论。
- 细节类文档继续放在 `docs/ARCHITECTURE.md`、`docs/FEATURES.md`、`docs/DEVELOPMENT.md` 等专题文件里。
- 任何“已完成”“已上线”“全量支持”这类结论，都要先和源码、路由、测试、Compose 配置对齐后再写。

## 7. 建议阅读顺序

如果你是第一次接手这个仓库，建议按下面顺序阅读：

1. `README.md`
2. `docs/PROJECT_SNAPSHOT.md`
3. `docs/ARCHITECTURE.md`
4. `docs/FEATURES.md`
5. `docs/DEVELOPMENT.md`
6. 需要细节时再进入对应模块源码
