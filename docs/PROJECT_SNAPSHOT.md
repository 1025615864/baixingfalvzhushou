# 百姓助手项目现状快照

> 快照日期：2026-03-21

## 1. 项目概述

百姓助手是一个面向法律服务场景的全栈 Web 项目，采用**渐进式微服务架构**。

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + PostgreSQL + Redis |
| 前端 | React 18 + TypeScript + Vite + Ant Design |
| 微服务 | 11 个独立服务 |
| 部署 | Docker + Kubernetes |

### 项目规模

| 指标 | 数量 |
|------|------|
| 微服务 | 11 个 |
| 后端路由 | 32 个 |
| 后端模型 | 29 个 |
| 前端特性目录 | 52 个 |

## 2. 微服务架构

### 已拆分服务 (11 个)

```
frontend-v2 (5173)
    │
    ├── backend (8080) - 核心业务 API
    │
    ├── user-service (8001) - 用户、认证、会员
    ├── payment-channel-service (8002) - 支付通道
    ├── payment-accounting-service (8003) - 账务结算
    ├── legal-service (8004) - 律师、法律知识
    ├── ai-service (8005) - AI 对话
    ├── news-service (8006) - 新闻资讯
    ├── community-service (8007) - 社区论坛
    ├── points-service (8008) - 积分系统
    ├── notification-service (8009) - 通知推送
    ├── recommendation-service (8010) - 推荐系统
    └── search-service (8011) - 搜索服务
```

### 前端代理配置

前端 `vite.config.ts` 已配置所有 11 个服务的代理。

## 3. 后端保留模块

### 核心业务路由 (32 个)

- **管理**: admin, admin_v1, admin_monitor, system_admin, analytics
- **业务**: lawfirm, settlement, document, knowledge, membership, video_consultation
- **工具**: calendar, feedback, reviews, promotion, enterprise
- **基础设施**: wechat_pay, upload, security, websocket, home, faq
- **其他**: moderation, ab_testing, funnel_analysis, channel_tracking, cross_domain

### 数据库模型 (29 个)

核心模型: User, Consultation, LawFirm, Lawyer, Document, Knowledge, Settlement, Membership, Payment, Notification

## 4. 代码清理成果

### 已删除 (约 41,000 行)

| 类别 | 文件数 | 说明 |
|------|--------|------|
| 路由 | 49 | user, ai, news, forum, payment, points 等 |
| 模型 | 7 | forum, news, payment, points 等 |
| Schema | 7 | ai, forum, news 等 |
| 服务 | 45+ | ai/, forum/, news/, payment/, points/ 等 |

### 恢复的模型

- `notification.py` - settlement, lawfirm 等核心功能仍需要
- `payment.py` - settlement, membership, wechat_pay 等核心功能仍需要

## 5. 文档状态

### 当前文档

- ✅ README.md - 已更新
- ✅ API.md - 已更新
- ✅ ARCHITECTURE.md - 已更新
- ✅ FEATURES.md - 已重写
- ✅ PROJECT_SNAPSHOT.md - 已重写
- 📋 DEVELOPMENT.md - 待更新
- 📋 OPERATIONS.md - 待更新

### 已删除

- ❌ FRONTEND_INTEGRATION_PLAN.md
- ❌ IMPROVEMENTS.md
- ❌ INTEGRATION_TEST.md
- ❌ PERFORMANCE_BENCHMARK.md
- ❌ PROJECT_MINDMAP.md

## 6. 下一步工作

1. 测试后端与微服务联调
2. 更新 DEVELOPMENT.md
3. 更新 OPERATIONS.md
4. 完善微服务业务逻辑
5. 添加数据迁移验证
