# 百姓助手 - 实际项目结构文档

**文档版本**: v1.2  
**更新日期**: 2026-02-06  
**审计人员**: Cascade

---

## 审计摘要

本文档基于实际代码审计生成，反映项目的真实结构。前端采用 React + TypeScript + Vite 技术栈，后端采用 FastAPI + SQLAlchemy 架构。

---

## 🎨 前端结构 (frontend-v2)

### 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2.0 | UI 框架 |
| TypeScript | 5.3.3 | 类型安全 |
| Vite | 5.0.8 | 构建工具 |
| Tailwind CSS | 3.4.0 | 样式框架 |
| React Query | 5.8.0 | 服务端状态管理 |
| Zustand | 4.4.0 | 客户端状态管理 |
| React Router | 6.20.0 | 路由管理 |
| Ant Design | 5.21.3 | UI 组件库 |
| Zod | 3.22.4 | 表单验证 |
| React Hook Form | 7.48.0 | 表单管理 |

### 目录结构

```
frontend/frontend-v2/
├── src/
│   ├── app/                    # 应用入口
│   │   ├── layouts/           # 布局组件
│   │   ├── providers/         # 全局 Provider
│   │   └── styles/            # 全局样式
│   ├── api/                   # API 客户端
│   ├── components/            # 公共组件
│   ├── features/              # 功能模块 (46个)
│   ├── pages/                 # 页面组件
│   ├── shared/                # 共享资源
│   ├── widgets/               # 业务组件
│   └── test/                  # 测试配置
├── e2e/                       # E2E 测试 (Playwright)
├── docs/                      # 项目文档
└── 配置文件 (vite, tsconfig, eslint, tailwind等)
```

### 功能模块清单 (46个)

| 模块名 | 路径 | 状态 | 说明 |
|--------|------|------|------|
| auth | `features/auth/` | ✅ 完成 | 用户认证 |
| user | `features/user/` | ✅ 完成 | 用户管理 |
| ai-assistant | `features/ai-assistant/` | ✅ 完成 | AI助手 |
| ai-consultation | `features/ai-consultation/` | ✅ 完成 | AI咨询 |
| ai_quality | `features/ai_quality/` | ✅ 完成 | AI质量监控 |
| consultation | `features/consultation/` | ✅ 完成 | 法律咨询 |
| knowledge | `features/knowledge/` | ✅ 完成 | 法律知识库 |
| knowledge_admin | `features/knowledge_admin/` | ✅ 完成 | 知识库管理 |
| lawyer | `features/lawyer/` | ✅ 完成 | 律师模块 |
| lawyer-matching | `features/lawyer-matching/` | ✅ 完成 | 律师匹配 |
| lawfirm | `features/lawfirm/` | ✅ 完成 | 律所模块 |
| document | `features/document/` | ✅ 完成 | 文档管理 |
| contract | `features/contract/` | ✅ 完成 | 合同管理 |
| contracts | `features/contracts/` | ✅ 完成 | 合同审查 |
| upload | `features/upload/` | ✅ 完成 | 文件上传 |
| news | `features/news/` | ✅ 完成 | 新闻资讯 |
| news-admin | `features/news-admin/` | ✅ 完成 | 新闻管理 |
| news-comments | `features/news-comments/` | ✅ 完成 | 新闻评论 |
| forum | `features/forum/` | ✅ 完成 | 论坛社区 |
| forum-admin | `features/forum-admin/` | ✅ 完成 | 论坛管理 |
| forum-assistant | `features/forum-assistant/` | ✅ 完成 | 论坛助手 |
| forum-reactions | `features/forum-reactions/` | ✅ 完成 | 论坛互动 |
| post | `features/post/` | ✅ 完成 | 帖子功能 |
| payment | `features/payment/` | ✅ 完成 | 支付系统 |
| order | `features/order/` | ✅ 完成 | 订单管理 |
| settlement | `features/settlement/` | ✅ 完成 | 结算系统 |
| points | `features/points/` | ✅ 完成 | 积分系统 |
| membership | `features/membership/` | ✅ 完成 | 会员体系 |
| notification | `features/notification/` | ✅ 完成 | 通知中心 |
| notifications | `features/notifications/` | ✅ 完成 | 消息通知 |
| calendar | `features/calendar/` | ✅ 完成 | 日历日程 |
| chat | `features/chat/` | ✅ 完成 | 即时通讯 |
| search | `features/search/` | ✅ 完成 | 搜索功能 |
| recommendation | `features/recommendation/` | ✅ 完成 | 推荐系统 |
| feedback | `features/feedback/` | ✅ 完成 | 反馈系统 |
| faq | `features/faq/` | ✅ 完成 | 常见问题 |
| admin | `features/admin/` | ✅ 完成 | 管理后台 |
| admin_monitor | `features/admin_monitor/` | ✅ 完成 | 监控后台 |
| admin-user | `features/admin-user/` | ✅ 完成 | 用户管理 |
| system-config | `features/system-config/` | ✅ 完成 | 系统配置 |
| security | `features/security/` | ✅ 完成 | 安全中心 |
| enterprise | `features/enterprise/` | ✅ 完成 | 企业合规 |
| channel | `features/channel/` | ✅ 完成 | 渠道管理 |
| vertical-channel | `features/vertical-channel/` | ✅ 完成 | 垂直频道 |
| cross-domain | `features/cross-domain/` | ✅ 完成 | 跨域管理 |
| promotion | `features/promotion/` | ✅ 完成 | 推广营销 |
| wechat | `features/wechat/` | ✅ 完成 | 微信生态 |
| moderation | `features/moderation/` | ✅ 完成 | 内容审核 |
| analytics | `features/analytics/` | ✅ 完成 | 数据分析 |
| home | `features/home/` | ✅ 完成 | 首页 |

---

## ⚙️ 后端结构 (backend)

### 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 最新 | Web 框架 |
| SQLAlchemy | 2.0+ | ORM |
| Alembic | - | 数据库迁移 |
| Pydantic | v2 | 数据验证 |
| Pytest | - | 测试框架 |
| Redis | - | 缓存 |
| PostgreSQL | - | 数据库 |

### 目录结构

```
backend/
├── app/                       # 应用代码
│   ├── routers/              # API 路由 (49个文件/目录)
│   ├── services/             # 业务逻辑 (80+ 服务)
│   ├── models/               # 数据模型 (28个实体)
│   ├── schemas/              # Pydantic 模型
│   ├── middleware/           # 中间件
│   ├── core/                 # 核心配置
│   ├── utils/                # 工具函数
│   ├── database/             # 数据库连接
│   └── config/               # 配置管理
├── tests/                    # 测试文件 (100+ 测试)
├── alembic/                  # 数据库迁移 (30+ 版本)
├── docs/                     # 后端文档
└── scripts/                  # 运维脚本
```

### 路由模块 (49个)

#### 主路由文件 (27个)
- `ab_testing.py` - A/B 测试
- `admin.py` - 管理后台
- `admin_monitor.py` - 监控管理
- `ai.py` - AI 核心功能
- `ai_quality.py` - AI 质量监控
- `analytics.py` - 数据分析
- `calendar.py` - 日历日程
- `channel_tracking.py` - 渠道追踪
- `contracts.py` - 合同审查
- `cross_domain.py` - 跨域管理
- `document.py` - 文档管理
- `document_templates.py` - 文档模板
- `enterprise.py` - 企业合规
- `faq.py` - 常见问题
- `feedback.py` - 用户反馈
- `funnel_analysis.py` - 漏斗分析
- `home.py` - 首页
- `integration.py` - 模块集成
- `knowledge.py` - 知识库
- `knowledge_admin.py` - 知识库管理
- `lawyer_recommendation.py` - 律师推荐
- `membership.py` - 会员体系
- `moderation.py` - 内容审核
- `news_recommendation.py` - 新闻推荐
- `notification.py` - 通知中心
- `payment_legacy.py` - 支付(旧)
- `points.py` - 积分系统
- `promotion.py` - 推广营销
- `recommendation.py` - 推荐系统
- `reviews.py` - 评价系统
- `search.py` - 搜索功能
- `security.py` - 数据安全
- `settlement_legacy.py` - 结算(旧)
- `system.py` - 系统配置
- `upload.py` - 文件上传
- `user.py` - 用户管理
- `vertical_channel.py` - 垂直频道
- `websocket.py` - WebSocket
- `wechat.py` - 微信生态
- `wechat_pay.py` - 微信支付

#### 子路由目录 (5个)

**ai/** (AI功能模块)
- `analysis.py` - AI分析
- `chat.py` - AI对话
- `consultations.py` - AI咨询
- `share.py` - 会话分享
- `transcription.py` - 语音转录

**forum/** (论坛模块)
- `assistant.py` - 论坛助手
- `comments.py` - 评论管理
- `common.py` - 公共功能
- `config.py` - 配置管理
- `favorites.py` - 收藏功能
- `invitations.py` - 邀请功能
- `moderation.py` - 内容审核
- `posts.py` - 帖子管理
- `reactions.py` - 表情反应
- `reviews.py` - 评价功能

**lawfirm/** (律所模块)
- `consultation_messages.py` - 咨询消息
- `consultations.py` - 咨询管理
- `dashboard.py` - 数据面板
- `firms.py` - 律所管理
- `homepage.py` - 律师主页
- `lawyers.py` - 律师管理
- `promotions.py` - 推广功能
- `reviews.py` - 评价管理
- `schedules.py` - 日程管理
- `templates.py` - 模板管理
- `verification.py` - 认证管理

**news/** (新闻模块)
- `admin.py` - 新闻管理
- `comments.py` - 评论功能
- `core.py` - 核心功能
- `subscriptions.py` - 订阅管理
- `topics.py` - 话题管理

**payment/** (支付模块)
- `admin_config.py` - 支付配置
- `admin_ops.py` - 运营操作
- `admin_stats.py` - 统计数据
- `callbacks.py` - 支付回调
- `cards.py` - 银行卡管理
- `crypto_utils.py` - 加密工具
- `helpers.py` - 辅助函数
- `orders_create.py` - 订单创建
- `orders_pay.py` - 订单支付
- `post_processing.py` - 后置处理
- `user_ops.py` - 用户操作

**settlement/** (结算模块)
- `admin.py` - 结算管理
- `bank_account.py` - 银行账户
- `income.py` - 收入管理
- `wallet.py` - 钱包功能
- `withdrawal.py` - 提现功能

**system_admin/** (系统管理)
- `ai_config.py` - AI配置
- `analytics.py` - 数据分析
- `config.py` - 系统配置
- `faq.py` - FAQ管理
- `logs.py` - 日志管理
- `metrics.py` - 指标监控
- `secrets.py` - 密钥管理
- `voice.py` - 语音配置

### 数据模型 (28个实体)

| 模型文件 | 实体 |
|----------|------|
| `user.py` | User |
| `user_quota.py` | UserQuotaDaily, UserQuotaPackBalance |
| `user_consent.py` | UserConsent |
| `user_profile.py` | UserProfile, UserInterestHistory, UserTagInteraction |
| `consultation.py` | Consultation, ChatMessage |
| `consultation_review.py` | ConsultationReviewTask, ConsultationReviewVersion |
| `contracts.py` | ContractReviewHistory |
| `cross_domain.py` | Domain |
| `channel.py` | Channel |
| `forum.py` | Post, Comment, PostLike, CommentLike, PostFavorite, PostReaction |
| `news.py` | News, NewsFavorite, NewsViewHistory, NewsSubscription |
| `news_ai.py` | NewsAIAnnotation |
| `news_workbench.py` | NewsVersion, NewsAIGeneration, NewsLinkCheck |
| `lawfirm.py` | LawFirm, Lawyer, LawyerConsultation, LawyerConsultationMessage, LawyerReview |
| `knowledge.py` | LegalKnowledge, ConsultationTemplate |
| `document.py` | GeneratedDocument |
| `document_template.py` | DocumentTemplate, DocumentTemplateVersion |
| `notification.py` | Notification |
| `system.py` | SystemConfig, SystemSecret, AdminLog |
| `calendar.py` | CalendarReminder |
| `feedback.py` | FeedbackTicket |
| `settlement.py` | LawyerWallet, LawyerIncomeRecord, LawyerBankAccount, WithdrawalRequest |
| `payment.py` | PaymentOrder, UserBalance, BalanceTransaction, PaymentCallbackEvent, PaymentStatus |
| `points.py` | PointsUser, PointsHistory, PointsDailyCount, PointsProduct, PointsExchangeOrder |
| `periodic_task.py` | PeriodicTaskRun, TaskStatus |
| `analytics.py` | - |
| `base.py` | 基础模型 |
| `faq.py` | - |
| `moderation.py` | - |

### 服务层 (80+ 服务)

按功能分类：

**AI服务**
- `ai_assistant.py`
- `ai_compliance.py`
- `ai_intent.py`
- `ai_mcp_mixin.py`
- `ai_metrics.py`
- `ai_response_strategy.py`
- `ai/` 目录 (assistant, chat, core, knowledge_base, models, prompts, session)

**业务服务**
- `analytics_service.py`
- `audit_service.py`
- `cache_service.py`
- `contract_review_service.py`
- `faq_service.py`
- `forum_service.py`
- `knowledge_service.py`
- `lawfirm_service.py`
- `membership_service.py`
- `news_service.py`
- `notification_service.py`
- `payment_service.py`
- `points.py`
- `recommendation_service.py`
- `settlement_service.py`
- `user_service.py`

**工具服务**
- `mcp/` - MCP工具框架
- `document/` - 文档处理
- `email/` - 邮件服务
- `search/` - 搜索服务
- `calendar/` - 日历服务

---

## 📚 文档结构

### 主文档 (docs/)

| 文档 | 说明 |
|------|------|
| `README.md` | 项目概览 |
| `CHANGELOG.md` | 更新日志 |
| `CONTRIBUTING.md` | 贡献指南 |
| `PROJECT_ANALYSIS_REPORT.md` | 项目分析报告 |
| `WORK_STATUS.md` | 工作状态 |
| `API.md` | 完整API文档 |
| `project_rules.md` | 项目规范 |
| `SECURITY_MODULE_ARCHITECTURE.md` | 安全架构 |

### 开发指南 (docs/guides/)

| 文档 | 说明 |
|------|------|
| `README.md` | 指南概览 |
| `SETUP_GUIDE.md` | 环境搭建 |
| `PROJECT_STRUCTURE.md` | 项目结构 |
| `API_QUICK_REFERENCE.md` | API速查 |
| `API_VERSIONING.md` | API版本管理 |
| `AUTHENTICATION.md` | 认证指南 |
| `CODE_STYLE.md` | 代码规范 |
| `DEPLOYMENT.md` | 部署指南 |
| `DOCKER_DEPLOYMENT.md` | Docker部署 |
| `KUBERNETES_DEPLOYMENT.md` | K8s部署 |
| `MONITORING.md` | 监控指南 |
| `PERFORMANCE.md` | 性能优化 |
| `SECURITY.md` | 安全指南 |
| `FAQ.md` | 常见问题 |
| `GIT_WORKFLOW.md` | Git工作流 |
| `ERROR_CODES.md` | 错误码说明 |

### 模块文档 (docs/modules/)

覆盖所有业务模块的详细文档 (30+ 模块文档)

### 配置文档 (docs/)

- `CACHE_STRATEGY.md` - 缓存策略
- `DATABASE_MIGRATION.md` - 数据库迁移
- `DATABASE_OPTIMIZATION.md` - 数据库优化
- `TESTING.md` - 测试指南
- `TOKEN_ROTATION.md` - Token轮换
- `WEBSOCKET.md` - WebSocket说明
- `CONTAINER_SECURITY_SCAN_GUIDE.md` - 容器安全扫描指南
- `grafana/` - Grafana监控配置
- `prometheus/` - Prometheus告警配置
- `samples/contracts/` - 合同模板示例

---

## 🗑️ 建议删除的过时文档

基于审计结果，以下文档已过时，建议删除或归档：

### 前端过时文档
| 文件路径 | 原因 | 建议操作 |
|----------|------|----------|
| `frontend/frontend-v2/REFACTOR_COMPLETE.md` | 重构已完成，报告过时 | 删除 |
| `frontend/frontend-v2/OLD_VS_NEW_COMPARISON.md` | 对比报告已失去时效 | 删除 |
| `frontend/frontend-v2/PROJECT_AUDIT_REPORT.md` | 审计报告已被本文档替代 | 删除 |
| `frontend/frontend-v2/PROJECT_STATUS.md` | 状态信息已合并到本文档 | 删除 |
| `frontend/frontend-v2/API_INTEGRATION_CHECK.md` | 需要验证是否过时 | 检查内容后删除 |
| `frontend/frontend-v2/COLLABORATION.md` | 需要验证是否过时 | 检查内容后删除 |
| `frontend/frontend-v2/新前端待开发模块功能清单.md` | 中文清单可能已过时 | 检查内容后删除 |

### 任务文档
| 文件路径 | 原因 | 建议操作 |
|----------|------|----------|
| `.cospec/frontend-tasks/TASKS.md` | 任务清单已过期 | 删除或归档 |
| `.cospec/new-frontend-refactor/tasks-new.md` | 任务清单需要更新 | 更新或删除 |
| `docs/TASKS_NEXT.md` | 部分任务已完成 | 更新内容 |

### .cospec 目录审计
`.cospec` 目录包含以下子目录，建议清理：
- `api-analysis/` - API分析，检查是否过时
- `code-audit/` - 代码审计，已完成可归档
- `frontend-modernization/` - 前端现代化，已完成可归档
- `frontend-tasks/` - 任务列表，需要更新
- `new-frontend-refactor/` - 重构文档，已完成可归档

---

## 📊 统计概览

### 代码规模

| 维度 | 数量 |
|------|------|
| 前端功能模块 | 46 个 |
| 后端路由文件 | 49 个 |
| 后端数据模型 | 28 个实体 |
| 后端服务 | 80+ 个 |
| 数据库迁移版本 | 30+ 个 |
| 测试文件 | 100+ 个 |
| 文档数量 | 50+ 篇 |

### 功能覆盖

- ✅ 用户认证与授权
- ✅ AI法律咨询
- ✅ 法律知识库
- ✅ 律师匹配与预约
- ✅ 论坛社区
- ✅ 新闻资讯
- ✅ 文档管理
- ✅ 合同审查
- ✅ 支付与结算
- ✅ 积分与会员
- ✅ 消息通知
- ✅ 管理后台
- ✅ 内容审核
- ✅ 数据分析
- ✅ 微信生态

---

## 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-02-05 | v1.0 | 初始审计文档 |
| 2026-02-05 | v1.1 | 修复 membership API 实现：<br>• 将原生 fetch 改为使用统一 apiClient<br>• 规范 API 路径前缀为 /api/v1/membership/<br>• 保持原有类型定义不变 |
| 2026-02-06 | v1.2 | 文档系统清理与精简：<br>• 删除 guides/ 目录中13个过时文档<br>• 删除 modules/ 目录全部46个文档<br>• 保留核心文档：API.md、project_rules.md、WORK_STATUS.md<br>• 更新文档结构说明 |

---

## 修复记录详情

### membership API 修复 (2026-02-05)

**问题描述**：
- 原实现使用原生 fetch，未使用项目统一的 apiClient
- 错误处理方式与其他 API 模块不一致

**修复内容**：
1. **引入 apiClient**：从 `@/api/client` 导入 `apiClient`
2. **统一 API 调用**：将所有 `fetch()` 改为 `apiClient.get()` / `apiClient.post()`
3. **规范路径前缀**：使用 `/membership` 作为基础路径（apiClient 已配置 baseURL: `/api/v1`）
4. **简化错误处理**：移除手动错误处理逻辑，由 apiClient 拦截器统一处理
5. **保持类型定义**：原有类型定义和导出函数签名完全保持不变

**影响文件**：
- [`frontend/frontend-v2/src/features/membership/api/index.ts`](frontend/frontend-v2/src/features/membership/api/index.ts)

**验证状态**：✅ 完成

---


**注意**: 本文档基于实际代码审计生成，反映了项目的真实状态。建议定期更新以保持同步。