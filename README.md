# 百姓助手

面向法律服务场景的全栈 Web 项目，采用微服务架构。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + PostgreSQL + Redis
- **前端**: React 18 + TypeScript + Vite + Ant Design
- **微服务**: 11 个独立服务（用户、支付、法律、AI、新闻、社区等）
- **部署**: Docker + Kubernetes

## 目录结构

```
.
├── backend/              # FastAPI 后端 (单体保留部分)
├── frontend-v2/         # React 前端
├── services/            # 11 个微服务
│   ├── user-service/    # 用户服务 (8001)
│   ├── payment-channel-service/   # 支付通道 (8002)
│   ├── payment-accounting-service/ # 账务服务 (8003)
│   ├── legal-service/   # 法律服务 (8004)
│   ├── ai-service/      # AI服务 (8005)
│   ├── news-service/    # 新闻服务 (8006)
│   ├── community-service/ # 社区服务 (8007)
│   ├── points-service/  # 积分服务 (8008)
│   ├── notification-service/ # 通知服务 (8009)
│   ├── recommendation-service/ # 推荐服务 (8010)
│   └── search-service/ # 搜索服务 (8011)
├── docs/                # 项目文档
├── scripts/             # 辅助脚本
└── services/k8s/       # K8s 部署配置
```

## 快速启动

### 后端 (单体)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

### 前端

```bash
cd frontend-v2
npm install
npm run dev
```

### 微服务

```bash
# 每个服务需要单独启动
cd services/user-service && uvicorn app.main:app --port 8001
cd services/news-service && uvicorn app.main:app --port 8006
# ... 其他服务
```

### 联调测试

```bash
bash scripts/test-microservices.sh
```

## 文档

- [API 文档](docs/API.md)
- [架构文档](docs/ARCHITECTURE.md)
- [功能清单](docs/FEATURES.md)
- [项目快照](docs/PROJECT_SNAPSHOT.md)
- [开发规范](docs/DEVELOPMENT.md)

## 微服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| backend | 8080 | 核心业务 API |
| user-service | 8001 | 用户、认证、会员 |
| payment-channel | 8002 | 支付通道 |
| payment-accounting | 8003 | 账务结算 |
| legal-service | 8004 | 律师、法律知识 |
| ai-service | 8005 | AI 对话 |
| news-service | 8006 | 新闻资讯 |
| community-service | 8007 | 社区论坛 |
| points-service | 8008 | 积分系统 |
| notification-service | 8009 | 通知推送 |
| recommendation | 8010 | 推荐系统 |
| search-service | 8011 | 搜索服务 |
