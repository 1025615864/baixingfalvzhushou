# 百姓助手

一站式法律服务平台

## 项目状态

> **当前版本**: v2.0.0
> **最后更新**: 2026-02-18
> **项目状态**: ✅ 已完成开发

## 项目概述

百姓助手是一个专注于法律服务领域的全栈Web应用平台，旨在为普通民众提供便捷、专业、高效的法律服务。

### 核心功能

| 功能模块 | 说明 | 状态 |
|----------|------|------|
| AI法律咨询 | 基于LangChain + RAG知识库的智能法律问答助手 | ✅ 已完成 |
| 律师服务 | 在线预约律师、律师推荐、律师主页展示 | ✅ 已完成 |
| 视频咨询 | 与律师进行实时视频咨询 | ✅ 已完成 |
| 合同审查 | AI自动合同审查与风险提示 | ✅ 已完成 |
| 法律文书商城 | 专业法律文书模板下载购买 | ✅ 已完成 |
| 论坛社区 | 法律知识分享、案例讨论、用户互动 | ✅ 已完成 |
| 新闻资讯 | 法律新闻、案例报道、政策解读 | ✅ 已完成 |
| 积分商城 | 用户积分体系、签到、积分兑换商品 | ✅ 已完成 |
| 会员订阅制 | VIP会员权益、会员专属优惠 | ✅ 已完成 |
| 企业服务 | 为企业提供法律咨询与合规服务 | ✅ 已完成 |
| 个性化推荐 | 基于用户兴趣的智能推荐系统 | ✅ 已完成 |
| 通知系统 | 实时通知、已读/未读状态管理 | ✅ 已完成 |

## 技术架构

### 后端技术栈

| 技术 | 用途 |
|------|------|
| FastAPI | Web框架 |
| SQLAlchemy | ORM |
| PostgreSQL | 主数据库 |
| Redis | 缓存、会话 |
| Alembic | 数据库迁移 |
| Celery | 任务队列 |
| WebSocket | 实时通信 |

### 前端技术栈

| 技术 | 用途 |
|------|------|
| React 18 | UI框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Ant Design | UI组件库 |
| React Query | 数据获取与状态管理 |
| React Router | 路由管理 |

### AI 与数据

| 技术 | 用途 |
|------|------|
| LangChain | AI应用框架 |
| OpenAI | 大语言模型 |
| RAG | 知识库检索 |
| MCP | 模型上下文协议 |
| Sherpa ASR | 语音识别 |

### 支付与监控

| 技术 | 用途 |
|------|------|
| 支付宝 | 支付渠道 |
| 微信支付 | 支付渠道 |
| IkunPay | 支付渠道 |
| Prometheus | 指标监控 |
| Grafana | 可视化监控 |
| Sentry | 错误追踪 |
| Alertmanager | 告警管理 |

### 基础设施

| 技术 | 用途 |
|------|------|
| Docker | 容器化部署 |
| Docker Compose | 本地开发环境 |
| Nginx | Web服务器 |
| Kubernetes | 生产环境部署(配置) |

## 目录结构

```
百姓助手/
├── backend/              # 后端服务 (FastAPI)
│   ├── app/              # 应用代码
│   │   ├── core/         # 核心模块
│   │   ├── database/     # 数据库配置
│   │   ├── middleware/   # 中间件
│   │   ├── models/      # 数据模型
│   │   ├── routers/     # API路由
│   │   ├── schemas/     # Pydantic模型
│   │   ├── services/    # 业务逻辑
│   │   └── utils/       # 工具函数
│   ├── tests/           # 测试代码
│   └── alembic/         # 数据库迁移
│
├── frontend-v2/         # 前端应用 (React)
│   ├── src/
│   │   ├── features/    # 功能模块
│   │   ├── pages/       # 页面组件
│   │   └── ...
│   └── ...
│
├── docs/                # 项目文档
├── scripts/             # 运维脚本
├── knowledge_base/      # 法律知识库
│   └── laws/           # 法律法规JSON
├── helm/               # Kubernetes部署配置
├── nginx/              # Nginx配置
├── prometheus/         # 监控配置
├── grafana/            # Grafana仪表盘
├── alertmanager/       # 告警配置
└── .github/            # CI/CD工作流
```

## 快速开始

### 环境要求

- Docker & Docker Compose
- Node.js 18+ (前端开发)
- Python 3.11+ (后端开发)

### 使用Docker Compose启动

```bash
# 克隆项目后，进入项目根目录
cd 百姓助手

# 启动所有服务（开发环境）
docker-compose -f docker-compose.dev.yml up -d

# 或启动生产环境
docker-compose -f docker-compose.prod.yml up -d
```

服务启动后可访问：
- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs
- Prometheus：http://localhost:9090
- Grafana：http://localhost:3001

### 本地开发环境启动

#### 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 复制环境变量配置
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端启动

```bash
# 进入前端目录
cd frontend-v2

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 文档导航

### 开发文档

- [后端API文档](./API_ADMIN_V1.md) - 管理员API接口文档
- [测试报告](./backend/TEST_REPORT.md) - 后端测试覆盖报告
- [E2E测试文档](./backend/tests/e2e/README.md) - 端到端测试指南

### 运维文档

- [数据库备份脚本](./scripts/db_backup.py) - 数据库备份操作
- [安全扫描脚本](./scripts/security_scan.py) - 安全漏洞扫描
- [监控配置](./prometheus/) - Prometheus监控配置

### 知识库

- [法律知识库](./knowledge_base/) - 法律法规JSON文件
  - 民法典
  - 消费者权益保护法
  - 合同法
  - 劳动法
  - 婚姻法

## 项目状态

| 指标 | 状态 |
|------|------|
| 后端测试覆盖率 | 85%+ |
| 前端E2E测试 | ✅ |
| Docker部署 | ✅ |
| CI/CD | ✅ |
| API文档 | ✅ |

![CI/CD](https://github.com/your-repo/baixing/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/your-repo/baixing)
![Version](https://img.shields.io/github/v/release/your-repo/baixing)

## 许可证

MIT License - 查看 [LICENSE](../LICENSE) 了解详情

## 联系方式

- 网站：https://baixing.com
- 邮箱：support@baixing.com