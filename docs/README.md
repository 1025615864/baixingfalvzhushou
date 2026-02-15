# 百姓法律助手

> 面向普通百姓的法律服务智能助手平台

---

## 📋 项目简介

百姓法律助手是一个基于 AI 的法律服务咨询平台，提供法律问答、文档生成、律所查询、社区论坛等功能，帮助普通用户便捷获取法律咨询服务。

---

## 🏗️ 技术架构

### 后端技术栈
| 技术 | 用途 |
|------|------|
| **FastAPI** | Web 框架 |
| **SQLAlchemy** | ORM 数据库访问 |
| **PostgreSQL** | 主数据库 |
| **Redis** | 缓存与任务队列 |
| **LangChain + OpenAI** | AI 对话能力 |
| **Sentry** | 错误监控 |
| **Prometheus** | 指标监控 |

### 前端技术栈
| 技术 | 用途 |
|------|------|
| **React 18** | UI 框架 |
| **TypeScript 5** | 类型安全 |
| **Vite** | 构建工具 |
| **React Router** | 路由管理 |
| **TanStack Query** | 数据请求 |
| **TailwindCSS** | 样式框架 |
| **Ant Design** | UI 组件库 |
| **Vitest** | 单元测试 |

---

## 📁 项目结构

```
百姓助手/
├── backend/                 # FastAPI 后端服务
│   ├── app/                 # 应用核心代码
│   ├── tests/               # 后端测试
│   ├── alembic/            # 数据库迁移
│   └── docs/               # 后端技术文档
├── frontend-v2/            # React + TypeScript 前端 (v2版本)
│   ├── src/                # 源代码
│   │   ├── features/       # 功能模块
│   │   ├── shared/         # 共享组件/工具
│   │   └── pages/          # 页面组件
│   └── dist/               # 构建输出
├── docs/                    # 项目文档
│   ├── guides/             # 开发指南
│   ├── plans/              # 执行计划
│   ├── grafana/            # Grafana仪表盘
│   └── prometheus/         # Prometheus告警
├── archive/                 # 归档文件
├── scripts/                 # 工具脚本
├── helm/                    # K8s 部署配置
└── docker-compose.yml       # Docker 编排
```

## 🚀 快速开始

### 环境要求
- Python 3.13+
- Node.js 20+
- PostgreSQL 15+（生产环境）
- Redis 7+

### 后端启动

```bash
cd backend

# 创建虚拟环境
py -m venv .venv
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 设置数据库、Redis 等配置

# 初始化数据库
py -m alembic upgrade head

# 启动服务
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动

```bash
cd frontend-v2

# 安装依赖
npm install

# 复制环境变量
cp .env.example .env

# 启动开发服务器
npm run dev
```

### 运行测试

```bash
# 后端测试
cd backend
pytest -q tests/ --tb=short

# 前端类型检查
cd frontend-v2
npm run type-check

# 前端构建
npm run build
```

## 📦 主要功能模块

### 用户模块
- 注册/登录（手机号、邮箱）
- JWT Token 认证
- 个人信息管理

### AI 法律助手
- 智能法律问答
- 会话历史管理
- 文书模板生成

### 社区论坛
- 帖子发布与评论
- 话题分类
- 点赞/收藏

### 新闻资讯
- 法律新闻浏览
- 话题订阅
- 智能推送

### 律所服务
- 律所/律师查询
- 在线预约
- 咨询记录

### VIP 会员
- 积分系统
- 会员套餐
- 支付订阅

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | - |
| `REDIS_URL` | Redis 连接字符串 | - |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `JWT_SECRET` | JWT 密钥 | - |
| `SENTRY_DSN` | Sentry DSN | - |
| `PROMETHEUS_ENABLED` | 启用 Prometheus | false |

### 详细配置

参考 `backend/.env.example` 获取完整配置示例。

## 📊 监控与运维

### Prometheus 指标
- 访问 `/metrics` 获取应用指标
- 支持 Prometheus + Grafana 监控

### 健康检查
- `GET /health` - 简单健康检查
- `GET /health/detailed` - 详细健康检查

## 🛡️ 安全特性

- ✅ CSRF 防护
- ✅ JWT Token 认证
- ✅ Token安全存储封装
- ✅ 速率限制
- ✅ 请求日志审计
- ✅ 敏感数据脱敏
- ✅ 错误边界保护

---

## 📚 文档导航

### 必读文档

| 文档 | 说明 | 优先级 |
|------|------|--------|
| **[project_rules.md](project_rules.md)** | 项目开发规范和约束 | ⭐⭐⭐⭐⭐ |
| **[WORK_STATUS.md](WORK_STATUS.md)** | 当前工作状态和任务进度 | ⭐⭐⭐⭐⭐ |
| **[PRODUCTION_READINESS_REPORT.md](PRODUCTION_READINESS_REPORT.md)** | 生产就绪报告 | ⭐⭐⭐⭐⭐ |

### 开发指南

| 文档 | 说明 |
|------|------|
| **[API.md](API.md)** | 完整API接口文档 |
| **[guides/AUTHENTICATION.md](guides/AUTHENTICATION.md)** | 认证系统指南 |
| **[guides/DEPLOYMENT.md](guides/DEPLOYMENT.md)** | 部署指南 |
| **[guides/SECURITY.md](guides/SECURITY.md)** | 安全最佳实践 |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | 贡献代码指南 |

---

## 📝 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解项目更新历史。

---

## 📁 归档文件

历史修复报告和临时文件已归档至 `archive/2026-02-11-reports/`。

---

## 🤝 贡献指南

参考 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何为项目贡献代码。

---

## 📄 许可证

MIT License

---

**最后更新**: 2026-02-11  
**项目状态**: ✅ 已准备好上线