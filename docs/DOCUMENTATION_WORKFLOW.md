# 百姓助手文档分析与更新流程

> 目标：让后续维护者能够基于当前仓库源码，快速判断项目大致情况，并把高置信度信息更新到合适的文档中。

## 1. 先解决两个问题

在开始写任何文档前，先回答下面两个问题：

1. 我现在要回答的是“项目整体是什么”，还是“某个模块具体怎么做”？
2. 我写的是“当前源码可证实的事实”，还是“规划中的目标状态”？

如果这两个问题没分清，文档就很容易把现状、计划和假设写混。

## 2. 推荐的分析顺序

### 第一步：看仓库顶层结构

先确认系统由哪些部分组成，重点关注：

- `backend/`
- `frontend-v2/`
- `docs/`
- `docker-compose*.yml`
- `prometheus/`
- `grafana/`
- `alertmanager/`
- `helm/`
- `nginx/`

PowerShell 示例：

```powershell
Get-ChildItem -Force
Get-ChildItem docs
```

这一步的目标不是读完所有内容，而是先画出“系统边界”。

### 第二步：确认运行拓扑

先看容器编排文件，弄清楚项目真正依赖哪些服务、哪些端口、哪些环境变量。

优先检查：

- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-compose.prod.yml`
- `backend/.env.example`
- `frontend-v2/.env.example`

PowerShell 示例：

```powershell
Get-Content docker-compose.yml
Get-Content backend/.env.example
Get-Content frontend-v2/.env.example
```

这一步主要回答：

- 前后端如何连接
- 数据库与缓存是什么
- 是否有监控、告警、对象存储、第三方支付、AI 服务

### 第三步：确认后端真实能力

后端分析建议按“入口 -> 路由 -> 服务 -> 数据模型 -> 迁移 -> 测试”来做。

优先检查：

- `backend/app/main.py`
- `backend/app/routers/__init__.py`
- `backend/app/services/`
- `backend/app/models/`
- `backend/alembic/versions/`
- `backend/tests/`

PowerShell 示例：

```powershell
Get-Content backend/app/main.py
Get-Content backend/app/routers/__init__.py
Get-ChildItem backend/app/services
Get-ChildItem backend/app/models
Get-ChildItem backend/alembic/versions
Get-ChildItem backend/tests -Recurse -Filter "test_*.py"
```

判断原则：

- 只有路由，没有 service/model/test，通常说明功能仍需二次核实
- 有 migration 和测试支撑的功能，可信度更高
- 若要写“支持某功能”，最好同时能找到路由、服务和至少一处测试

### 第四步：确认前端真实入口

前端不要只看 `src/features/` 目录数量，更要看用户能否通过路由真正访问。

优先检查：

- `frontend-v2/package.json`
- `frontend-v2/src/main.tsx`
- `frontend-v2/src/app/providers/Router.tsx`
- `frontend-v2/src/features/`
- `frontend-v2/e2e/`

PowerShell 示例：

```powershell
Get-Content frontend-v2/package.json
Get-Content frontend-v2/src/app/providers/Router.tsx
Get-ChildItem frontend-v2/src/features
Get-ChildItem frontend-v2/e2e -Recurse -Filter "*.spec.ts"
```

判断原则：

- feature 目录存在，不等于页面已接入路由
- 路由存在，不等于 API 已接通
- 若同时存在页面、API 调用和 E2E 规格，通常说明功能更接近可用状态

### 第五步：对照现有文档

只有在掌握源码后，才去看 `docs/` 中哪些内容该保留、该补充、该降级表述。

建议阅读顺序：

1. `docs/README.md`
2. `docs/PROJECT_SNAPSHOT.md`
3. `docs/ARCHITECTURE.md`
4. `docs/FEATURES.md`
5. `docs/DEVELOPMENT.md`
6. 与当前任务相关的专题文档

这一步的重点不是复制旧文档，而是找出：

- 现有文档是否缺入口
- 文档里的端口、命令、文件路径是否仍然正确
- 文档是否把“计划中”写成了“已完成”

## 3. 更新文档时怎么分层

### 适合写进 `README.md` 的内容

- 项目一句话简介
- 仓库结构
- 最短启动方式
- 文档导航

### 适合写进 `docs/PROJECT_SNAPSHOT.md` 的内容

- 截止某个日期的项目整体判断
- 技术栈与架构大图
- 关键模块范围
- 当前主要事实与风险

### 适合写进专题文档的内容

- 架构细节写进 `docs/ARCHITECTURE.md`
- 功能清单写进 `docs/FEATURES.md`
- 开发规范写进 `docs/DEVELOPMENT.md`
- 运维流程写进 `docs/OPERATIONS.md`
- API 细节写进 `docs/API.md`

原则很简单：

- 入口文档只解决“先看哪里”
- 快照文档只解决“现在是什么”
- 专题文档才承载细节

## 4. 更新时的写法建议

为了降低文档失真，建议遵循下面几条：

- 写明快照日期，例如 `2026-03-08`
- 用“根据当前源码可见内容判断”这类表述，而不是过度下结论
- 命令、端口、文件路径都以仓库实际内容为准
- 不要把单个 feature 目录的存在直接写成“功能已完成”
- 如果工作区很脏，明确说明“当前为活跃迭代状态”

## 5. 一份可复用的更新清单

每次准备更新文档时，按这个清单走：

- 确认本次更新目标是入口、快照还是专题文档
- 检查 `docker-compose*.yml` 和 `.env.example`
- 检查后端入口、路由聚合、相关 service/model/test
- 检查前端路由、相关 feature、相关 E2E
- 只把能从源码直接验证的信息写进文档
- 为快照类文档补上日期
- 补充与已有文档之间的跳转链接

## 6. 本仓库当前最值得持续维护的文档

结合当前结构，后续建议优先维护这些文件：

- `README.md`
- `docs/PROJECT_SNAPSHOT.md`
- `docs/ARCHITECTURE.md`
- `docs/FEATURES.md`
- `docs/DEVELOPMENT.md`
- `docs/OPERATIONS.md`

这样做的好处是：

- 新人能快速进入上下文
- 老文档不会因为一次功能变动就全部失效
- 后续做模块审查时，也能更快定位事实来源
