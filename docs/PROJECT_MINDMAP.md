# 百姓助手 - 业务思维导图

> 项目业务架构全景图 - 便于直观了解项目结构和各模块功能细节

---

## 1. 项目概览

| 项目 | 描述 |
|------|------|
| **项目名称** | 百姓助手 |
| **项目定位** | 一站式法律服务平台 |
| **技术架构** | React + FastAPI + PostgreSQL + Redis + ChromaDB + LangChain |
| **部署方式** | Docker + Kubernetes (Helm) |
| **CI/CD** | GitHub Actions |

---

## 2. 核心业务模块（思维导图）

```
百姓助手
│
├── 📱 用户端
│   │
│   ├── 🔹 核心服务
│   │   ├── AI 法律咨询
│   │   │   ├── AI 问答（智能对话、法律问题分析）
│   │   │   ├── 文件上传分析（合同/文档 AI 审查）
│   │   │   ├── 语音输入（语音转文字咨询）
│   │   │   └── 咨询历史（会话记录、可追溯）
│   │   │
│   │   ├── 律师服务
│   │   │   ├── 律师列表（筛选、搜索）
│   │   │   ├── 律师详情（专长、评价、案例）
│   │   │   └── 律师预约（时段选择、预约管理）
│   │   │
│   │   ├── 视频咨询
│   │   │   ├── 预约咨询（在线预约）
│   │   │   ├── 时段选择（律师日程）
│   │   │   └── 视频通话（实时视频咨询）
│   │   │
│   │   └── 律师匹配
│   │       ├── 智能推荐（基于问题类型匹配）
│   │       └── 在线状态（实时可用性）
│   │
│   ├── 🔹 法律工具
│   │   ├── 合同审查
│   │   │   ├── 合同上传（多格式支持）
│   │   │   ├── AI 审查（风险点识别）
│   │   │   └── 审查报告（详细分析建议）
│   │   │
│   │   ├── 文档管理
│   │   │   ├── 文档上传/存储
│   │   │   ├── 文档分类
│   │   │   └── 文档导出（PDF/Word）
│   │   │
│   │   ├── 法律知识库
│   │   │   ├── 民法典
│   │   │   ├── 劳动法
│   │   │   ├── 婚姻法
│   │   │   ├── 合同法
│   │   │   └── 消费者权益保护法
│   │   │
│   │   └── 法律日历
│   │       ├── 时效计算
│   │       └── 重要日期提醒
│   │
│   ├── 🔹 社区内容
│   │   ├── 论坛
│   │   │   ├── 帖子发布（图文、AI 辅助）
│   │   │   ├── 评论互动（回复、@）
│   │   │   ├── 点赞收藏（表情反应）
│   │   │   └── 律师邀请（专业解答）
│   │   │
│   │   └── 新闻资讯
│   │       ├── AI 新闻生成
│   │       ├── 订阅管理
│   │       └── 评论互动
│   │
│   ├── 🔹 交易支付
│   │   ├── 支付
│   │   │   ├── 支付宝
│   │   │   ├── 微信支付
│   │   │   └── IkunPay（平台自有）
│   │   │
│   │   ├── 订单管理
│   │   │   ├── 订单列表
│   │   │   ├── 订单详情
│   │   │   └── 订单状态追踪
│   │   │
│   │   ├── 积分系统
│   │   │   ├── 每日签到
│   │   │   ├── 积分任务
│   │   │   ├── 积分商城
│   │   │   └── 积分兑换
│   │   │
│   │   ├── 会员订阅
│   │   │   ├── 月度会员
│   │   │   ├── 年度会员
│   │   │   └── 终身会员
│   │   │
│   │   └── 结算中心
│   │       ├── 收益管理（律师）
│   │       ├── 提现申请
│   │       └── 银行卡管理
│   │
│   ├── 🔹 企业服务
│   │   ├── 企业法律顾问
│   │   ├── 合规检查
│   │   └── 推广管理
│   │
│   ├── 🔹 用户中心
│   │   ├── 个人信息
│   │   ├── 账户安全（双因素认证）
│   │   ├── 通知中心
│   │   └── 反馈建议
│   │
│   └── 🔹 其他功能
│       ├── 全局搜索
│       ├── 个性化推荐
│       ├── FAQ 常见问题
│       ├── 微信生态集成
│       ├── 渠道追踪
│       ├── A/B 测试
│       ├── 文件上传
│       └── WebSocket 实时通信
│
├── 🔧 管理后台
│   │
│   ├── 系统监控
│   │   ├── 服务健康检查
│   │   ├── 性能指标监控
│   │   ├── 数据库连接池监控
│   │   ├── 慢查询追踪
│   │   └── 告警管理
│   │
│   ├── AI 质量监控
│   │   ├── 响应质量评估
│   │   ├── 会话审查
│   │   ├── 模型配置管理
│   │   └── 意图识别分析
│   │
│   ├── 内容审核
│   │   ├── UGC 审核
│   │   ├── 审核队列管理
│   │   ├── 审核记录追踪
│   │   └── 内容安全检测
│   │
│   ├── 新闻管理
│   │   ├── 文章发布/编辑
│   │   ├── 分类/标签管理
│   │   ├── 订阅管理
│   │   ├── 评论管理
│   │   ├── 新闻源配置
│   │   └── RSS 采集配置
│   │
│   ├── 论坛管理
│   │   ├── 帖子管理
│   │   ├── 评论管理
│   │   ├── 用户管理
│   │   ├── 分类/板块管理
│   │   └── 版主权限管理
│   │
│   ├── 知识库管理
│   │   ├── 文章管理
│   │   ├── 分类管理
│   │   ├── 向量化配置
│   │   └── RAG 检索优化
│   │
│   ├── 用户管理
│   │   ├── 用户列表
│   │   ├── 用户详情
│   │   ├── 角色权限管理
│   │   └── 登录审计
│   │
│   ├── 推广管理
│   │   ├── 推广链接生成
│   │   ├── 数据统计分析
│   │   ├── 佣金管理
│   │   └── 渠道追踪
│   │
│   ├── 数据分析
│   │   ├── 用户增长分析
│   │   ├── 功能使用分析
│   │   ├── 转化漏斗分析
│   │   └── 留存分析
│   │
│   └── 系统配置
│       ├── 参数配置
│       ├── 密钥管理
│       ├── AI 模型配置
│       ├── FAQ 管理
│       └── 系统日志
│
└── 🏗️ 技术架构
    │
    ├── 后端技术栈
    │   ├── Web 框架：FastAPI + Uvicorn
    │   ├── ORM：SQLAlchemy 2.0 (异步)
    │   ├── 数据库：PostgreSQL 15+
    │   ├── 缓存：Redis 7+
    │   ├── 迁移：Alembic
    │   └── 认证：JWT (RS256/HS256) + TOTP 2FA
    │
    ├── 前端技术栈
    │   ├── 框架：React 18 + TypeScript
    │   ├── 构建：Vite 5
    │   ├── 状态：Zustand + TanStack Query
    │   ├── UI 库：Ant Design 5
    │   ├── 样式：Tailwind CSS 3
    │   └── 路由：React Router DOM 6
    │
    ├── AI 技术栈
    │   ├── LLM 框架：LangChain
    │   ├── 向量库：ChromaDB
    │   ├── Embeddings：OpenAI Text Embedding
    │   ├── RAG 检索：向量检索 + 上下文增强
    │   └── 语音：Sherpa ASR
    │
    ├── 支付技术栈
    │   ├── 支付宝开放平台
    │   ├── 微信支付 V3
    │   ├── IkunPay（自有）
    │   └── 幂等性保障
    │
    └── 监控技术栈
        ├── 指标：Prometheus + Grafana
        ├── 告警：Alertmanager
        ├── 错误追踪：Sentry
        └── 日志：结构化日志 + 分析
```

---

## 3. 核心功能模块详情

### 3.1 AI 法律咨询 (`ai-consultation`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 基于 LangChain 的 AI 法律咨询服务，支持文字/语音/文件多模态输入，RAG 知识检索增强 |
| **主要页面** | [`AIConsultationPage.tsx`](frontend-v2/src/features/ai-consultation/pages/AIConsultationPage.tsx:1)、[`ConsultationChatPage.tsx`](frontend-v2/src/features/ai-consultation/pages/ConsultationChatPage.tsx:1)、[`ConsultationHistoryPage.tsx`](frontend-v2/src/features/ai-consultation/pages/ConsultationHistoryPage.tsx:1) |
| **核心组件** | `AIResponseFormatter`、`ConfidenceIndicator`、`FileUpload`、`VoiceInput`、`ShareDialog` |
| **API 端点** | `/api/v1/ai/chat`、`/api/v1/ai/consultations`、`/api/v1/ai/analysis`、`/api/v1/ai/transcription` |
| **服务层** | [`ai_assistant.py`](backend/app/services/ai_assistant.py:1)、[`consultation_service.py`](backend/app/services/ai/consultation_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖、✅ E2E 测试覆盖 |

### 3.2 律师服务 (`lawyer`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 律师信息管理、主页展示、推广链接、回复模板、认证审核 |
| **主要页面** | [`LawFirmsPage.tsx`](frontend-v2/src/features/lawyer/pages/LawFirmsPage.tsx:1)、[`LawyerHomepage.tsx`](frontend-v2/src/features/lawyer/pages/LawyerHomepage.tsx:1)、[`PromotionPage.tsx`](frontend-v2/src/features/lawyer/pages/PromotionPage.tsx:1) |
| **核心组件** | `LawyerCard`、`LawyerList`、`HomepageEditor`、`PromotionLinkGenerator`、`ReplyTemplates` |
| **API 端点** | `/api/v1/lawfirm/lawyers`、`/api/v1/lawfirm/firms`、`/api/v1/lawfirm/homepage` |
| **服务层** | [`lawfirm_service.py`](backend/app/services/lawfirm_service.py:1)、[`lawyer_homepage_service.py`](backend/app/services/lawyer_homepage_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.3 合同审查 (`contracts`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 合同上传、AI 风险识别、审查报告生成、审查历史追踪 |
| **主要页面** | [`ContractReviewPage.tsx`](frontend-v2/src/features/contracts/pages/ContractReviewPage.tsx:1)、[`ContractHistoryPage.tsx`](frontend-v2/src/features/contracts/pages/ContractHistoryPage.tsx:1) |
| **核心组件** | `ContractReviewer`、`ContractGenerator`、`ContractCompare`、`ContractList` |
| **API 端点** | `/api/v1/contracts/review`、`/api/v1/contracts/history` |
| **服务层** | [`contract_review_service.py`](backend/app/services/contract_review_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.4 文档管理 (`document`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 法律文档上传、分类、存储、导出（PDF/Word）、模板管理 |
| **主要页面** | [`DocumentsPage.tsx`](frontend-v2/src/features/document/pages/DocumentsPage.tsx:1) |
| **核心组件** | `DocumentCard`、`DocumentList`、`DocumentViewer`、`DocumentExport` |
| **API 端点** | `/api/v1/document`、`/api/v1/document/templates` |
| **服务层** | [`document/core.py`](backend/app/services/document/core.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.5 论坛 (`forum`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 法律社区论坛，支持发帖、评论、点赞、收藏、律师邀请 |
| **主要页面** | [`ForumHomePage.tsx`](frontend-v2/src/features/forum/pages/ForumHomePage.tsx:1)、[`PostDetailPage.tsx`](frontend-v2/src/features/forum/pages/PostDetailPage.tsx:1) |
| **核心组件** | `PostCard`、`ReactionBar`、`FavoriteButton`、`LawyerInviteDialog` |
| **API 端点** | `/api/v1/forum/posts`、`/api/v1/forum/comments`、`/api/v1/forum/reactions` |
| **服务层** | [`forum_service.py`](backend/app/services/forum_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖、✅ E2E 测试覆盖 |

### 3.6 支付系统 (`payment`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 多通道支付（支付宝、微信支付、IkunPay），订单管理、幂等性保障 |
| **主要页面** | [`OrdersPage.tsx`](frontend-v2/src/features/payment/pages/OrdersPage.tsx:1)、[`PaymentResultPage.tsx`](frontend-v2/src/features/payment/pages/PaymentResultPage.tsx:1) |
| **核心组件** | `OrderCard`、`OrderList`、`PaymentModal`、`PaymentMethodSelector`、`PaymentQRCode` |
| **API 端点** | `/api/v1/payment/orders`、`/api/v1/payment/pay`、`/api/v1/payment/callbacks` |
| **服务层** | [`payment_service.py`](backend/app/services/payment_service.py:1)、[`payment/core.py`](backend/app/services/payment/core.py:1) |
| **测试状态** | ✅ 单元测试覆盖、✅ E2E 测试覆盖、✅ 集成测试覆盖 |

### 3.7 积分系统 (`points`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 积分获取（签到、任务）、积分商城、积分兑换、积分流水 |
| **主要页面** | [`PointsMallPage.tsx`](frontend-v2/src/features/points/pages/PointsMallPage.tsx:1)、[`PointsHistoryPage.tsx`](frontend-v2/src/features/points/pages/PointsHistoryPage.tsx:1) |
| **核心组件** | `PointsBalance`、`CheckInButton`、`CheckInCalendar`、`ExchangeConfirmDialog` |
| **API 端点** | `/api/v1/points/checkin`、`/api/v1/points/products`、`/api/v1/points/exchange` |
| **服务层** | [`points_service.py`](backend/app/services/points_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.8 会员系统 (`membership`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 会员套餐（月度/年度/终身）、会员权益、自动续费 |
| **主要页面** | [`VipPage.tsx`](frontend-v2/src/features/membership/pages/VipPage.tsx:1) |
| **核心组件** | `MembershipCard`、`MembershipComparison`、`PricingCard`、`PurchaseFlow` |
| **API 端点** | `/api/v1/membership/plans`、`/api/v1/membership/upgrade` |
| **服务层** | [`membership_service.py`](backend/app/services/membership_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖、✅ E2E 测试覆盖 |

### 3.9 视频咨询 (`video-consultation`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 律师视频咨询预约、日程管理、视频通话、评价 |
| **主要页面** | [`VideoConsultationPage.tsx`](frontend-v2/src/features/video-consultation/pages/VideoConsultationPage.tsx:1) |
| **核心组件** | `VideoConsultationBooking`、`VideoConsultationRoom`、`LawyerSchedulePicker` |
| **API 端点** | `/api/v1/video-consultations`、`/api/v1/video-consultations/{id}/confirm` |
| **服务层** | [`video_consultation.py`](backend/app/services/video_consultation.py:1) |
| **测试状态** | ✅ 单元测试覆盖、✅ E2E 测试覆盖 |

### 3.10 结算系统 (`settlement`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 律师收益管理、提现申请、银行卡管理、收入统计 |
| **主要页面** | [`WalletPage.tsx`](frontend-v2/src/features/settlement/pages/WalletPage.tsx:1)、[`WithdrawalPage.tsx`](frontend-v2/src/features/settlement/pages/WithdrawalPage.tsx:1) |
| **核心组件** | `SettlementCard`、`SettlementList` |
| **API 端点** | `/api/v1/settlement/income`、`/api/v1/settlement/withdrawal` |
| **服务层** | [`settlement_service.py`](backend/app/services/settlement_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.11 管理后台 (`admin`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 系统监控、AI 质量监控、内容审核、用户管理、系统配置 |
| **主要页面** | [`AdminDashboardPage.tsx`](frontend-v2/src/features/admin/pages/AdminDashboardPage.tsx:1)、[`MonitorPage.tsx`](frontend-v2/src/features/admin_monitor/pages/MonitorPage.tsx:1) |
| **核心组件** | `Sidebar`、`StatsCards`、`UserTable`、`MetricCard` |
| **API 端点** | `/api/v1/admin`、`/api/v1/admin_monitor`、`/api/v1/ai_quality` |
| **服务层** | [`system_monitor.py`](backend/app/services/system_monitor.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.12 通知系统 (`notification`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 站内通知、WebSocket 实时推送、系统消息管理 |
| **主要页面** | [`NotificationCenter.tsx`](frontend-v2/src/features/notification/pages/NotificationCenter.tsx:1)、[`NotificationsPage.tsx`](frontend-v2/src/features/notification/pages/NotificationsPage.tsx:1) |
| **核心组件** | `NotificationBell`、`NotificationDropdown`、`ConnectionStatus`、`NotificationToast` |
| **API 端点** | `/api/v1/notification`、`/ws` |
| **服务层** | [`notification_service.py`](backend/app/services/notification_service.py:1)、[`websocket_service.py`](backend/app/services/websocket_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.13 安全中心 (`security`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 账户安全管理、双因素认证、设备管理、登录审计 |
| **主要页面** | [`SecurityPage.tsx`](frontend-v2/src/features/security/pages/SecurityPage.tsx:1)、[`TwoFactorSetupPage.tsx`](frontend-v2/src/features/security/pages/TwoFactorSetupPage.tsx:1) |
| **核心组件** | `TwoFactorSetup`、`DeviceList`、`LoginAuditTable`、`PasswordChange` |
| **API 端点** | `/api/v1/security`、`/api/v1/user/devices` |
| **服务层** | [`user_security_service.py`](backend/app/services/user_security_service.py:1)、[`totp_service.py`](backend/app/services/totp_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.14 搜索功能 (`search`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 全局搜索、多类型结果、搜索建议、搜索历史 |
| **主要页面** | [`SearchPage.tsx`](frontend-v2/src/features/search/pages/SearchPage.tsx:1) |
| **核心组件** | `SearchInput`、`SearchResults`、`SearchSuggestions`、`SearchHistory` |
| **API 端点** | `/api/v1/search`、`/api/v1/search/suggestions` |
| **服务层** | [`search_service.py`](backend/app/services/search_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.15 企业服务 (`enterprise`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 企业法律顾问、合规检查、团队管理、权限设置 |
| **主要页面** | [`EnterprisePage.tsx`](frontend-v2/src/features/enterprise/pages/EnterprisePage.tsx:1) |
| **核心组件** | `ComplianceDashboard`、`TeamManager`、`PermissionSettings`、`ComplianceReportGenerator` |
| **API 端点** | `/api/v1/enterprise`、`/api/v1/enterprise/compliance` |
| **服务层** | [`enterprise_compliance.py`](backend/app/services/enterprise_compliance.py:1) |
| **测试状态** | ✅ 单元测试覆盖、✅ E2E 测试覆盖 |

### 3.16 推广系统 (`promotion`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 推广链接生成、二维码生成、佣金管理、数据统计 |
| **主要页面** | [`PromotionPage.tsx`](frontend-v2/src/features/promotion/pages/PromotionPage.tsx:1)、[`WithdrawalPage.tsx`](frontend-v2/src/features/promotion/pages/WithdrawalPage.tsx:1) |
| **核心组件** | `PromotionLinkGenerator`、`PromotionStats`、`CommissionList`、`QRCodeGenerator` |
| **API 端点** | `/api/v1/promotion`、`/api/v1/promotion/withdrawals` |
| **服务层** | [`lawyer_promotion_link_service.py`](backend/app/services/lawyer_promotion_link_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.17 知识库 (`knowledge`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 法律知识查询、分类浏览、文章详情、RAG 检索增强 |
| **主要页面** | [`KnowledgePage.tsx`](frontend-v2/src/features/knowledge/pages/KnowledgePage.tsx:1)、[`KnowledgeAdminPage.tsx`](frontend-v2/src/features/knowledge_admin/pages/KnowledgeAdminPage.tsx:1) |
| **核心组件** | `KnowledgeCard`、`KnowledgeDetail`、`KnowledgeSearch`、`CategoryFilter` |
| **API 端点** | `/api/v1/knowledge`、`/api/v1/knowledge_admin` |
| **服务层** | [`knowledge_service.py`](backend/app/services/knowledge_service.py:1)、[`rag_knowledge.py`](backend/app/services/rag_knowledge.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.18 法律日历 (`calendar`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 法律时效计算、重要日期提醒、日程管理 |
| **主要页面** | [`CalendarPage.tsx`](frontend-v2/src/features/calendar/pages/CalendarPage.tsx:1) |
| **核心组件** | `CalendarView`、`ReminderForm`、`ReminderList`、`ReminderModal` |
| **API 端点** | `/api/v1/calendar` |
| **服务层** | [`calendar/core.py`](backend/app/services/calendar/core.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.19 聊天功能 (`chat`)

| 属性 | 详情 |
|------|------|
| **功能描述** | AI 聊天对话、会话管理、消息历史 |
| **主要页面** | [`ChatPage.tsx`](frontend-v2/src/features/chat/pages/ChatPage.tsx:1) |
| **核心组件** | `ChatInput`、`MessageList` |
| **API 端点** | `/api/v1/ai/chat` |
| **服务层** | [`ai/chat.py`](backend/app/services/ai/chat.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.20 数据分析 (`analytics`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 用户增长分析、功能使用统计、转化漏斗、留存分析 |
| **主要页面** | [`AnalyticsDashboardPage.tsx`](frontend-v2/src/features/analytics/pages/AnalyticsDashboardPage.tsx:1)、[`FunnelAnalysisPage.tsx`](frontend-v2/src/features/analytics/pages/FunnelAnalysisPage.tsx:1) |
| **核心组件** | `UserGrowthChart`、`FeatureUsageChart`、`FunnelChart`、`StatCard` |
| **API 端点** | `/api/v1/analytics`、`/api/v1/funnel_analysis` |
| **服务层** | [`analytics_service.py`](backend/app/services/analytics_service.py:1)、[`funnel_analysis.py`](backend/app/services/funnel_analysis.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.21 垂直频道模块 (`vertical-channel`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 为婚姻家庭和劳动争议领域提供专属法律服务入口，包含频道列表、新闻资讯、咨询类型、文书模板等功能 |
| **主要页面** | [`VerticalChannelPage.tsx`](frontend-v2/src/features/vertical-channel/pages/VerticalChannelPage.tsx:1) |
| **核心组件** | `ChannelList`、`ChannelContent`、`TopicList` |
| **API 端点** | `/vertical/channels`、`/vertical/channels/{key}/news`、`/vertical/channels/{key}/consultation/types`、`/vertical/channels/{key}/document/types`、`/vertical/channels/{key}/stats` |
| **服务层** | [`news_service.py`](backend/app/services/news_service.py:1)、[`vertical_channel.py`](backend/app/routers/vertical_channel.py:1) |
| **测试状态** | ⏳ 待补充 |

### 3.22 渠道追踪模块 (`channel`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 渠道管理与追踪分析，支持落地页配置、优惠配置、追踪配置，提供转化漏斗、渠道对比等数据分析功能 |
| **主要页面** | [`ChannelPage.tsx`](frontend-v2/src/features/channel/pages/ChannelPage.tsx:1) |
| **核心组件** | `ChannelList`、`ChannelStats`、`ChannelForm` |
| **API 端点** | `/api/v1/channel-tracking/list`、`/api/v1/channel-tracking/detail/{id}`、`/api/v1/channel-tracking/analytics`、`/api/v1/channel-tracking/track`、`/api/v1/channel-tracking/stats` |
| **服务层** | [`channel_tracking.py`](backend/app/routers/channel_tracking.py:1)、[`analytics_service.py`](backend/app/services/analytics_service.py:1) |
| **测试状态** | ⏳ 待补充 |

### 3.23 反馈系统 (`feedback`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 用户意见反馈功能，支持提交反馈工单、查看反馈历史、管理员回复反馈、反馈状态管理 |
| **主要页面** | [`FeedbackPage.tsx`](frontend-v2/src/features/feedback/pages/FeedbackPage.tsx:1)、[`FeedbackAdminPage.tsx`](frontend-v2/src/features/feedback/pages/FeedbackAdminPage.tsx:1) |
| **核心组件** | `FeedbackForm`、`FeedbackList`、`FeedbackSuccess`、`FeedbackModal` |
| **API 端点** | `/api/v1/feedback`、`/api/v1/feedback/admin/tickets`、`/api/v1/feedback/admin/tickets/{id}` |
| **服务层** | [`feedback.py`](backend/app/models/feedback.py:1)、[`feedback_service.py`](backend/app/services/feedback.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_feedback_router.py`) |

### 3.24 FAQ 系统

| 属性 | 详情 |
|------|------|
| **功能描述** | 常见问题解答系统，支持 FAQ 搜索、分类浏览、智能搜索、热门 FAQ，管理员可进行 FAQ 管理 |
| **主要页面** | [`FAQPage.tsx`](frontend-v2/src/features/faq/pages/FAQPage.tsx:1)、[`FAQAdminPage.tsx`](frontend-v2/src/features/faq/pages/FAQAdminPage.tsx:1) |
| **核心组件** | `FAQList`、`FAQDetail`、`FAQSearch`、`FAQForm` |
| **API 端点** | `/api/v1/faq/search`、`/api/v1/faq/{id}`、`/api/v1/faq/categories`、`/api/v1/faq/popular`、`/api/v1/faq/smart-search`、`/api/v1/faq/admin/faqs` |
| **服务层** | [`faq.py`](backend/app/models/faq.py:1)、[`faq_service.py`](backend/app/services/faq/faq_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_faq.py`、`test_faq_service.py`) |

### 3.25 内容审核模块 (`moderation`)

| 属性 | 详情 |
|------|------|
| **功能描述** | UGC 内容审核中心，支持审核队列管理、审核记录追踪、内容安全检测、关键词检查、批量审核 |
| **主要页面** | [`ModerationPage.tsx`](frontend-v2/src/features/moderation/pages/ModerationPage.tsx:1) |
| **核心组件** | `ModerationQueue`、`ModerationDetail`、`ModerationStats`、`ContentPreview` |
| **API 端点** | `/moderation/queue`、`/moderation/records`、`/moderation/{id}/review`、`/moderation/batch-review`、`/moderation/stats`、`/moderation/keyword/check` |
| **服务层** | [`moderation.py`](backend/app/models/moderation.py:1)、[`content_moderation.py`](backend/app/services/content_moderation.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_content_moderation.py`) |

### 3.26 律师匹配模块 (`lawyer-matching`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 智能律师推荐与匹配系统，基于问题类型、法律领域进行律师推荐，支持律师搜索、在线状态查看、预约管理、评价系统 |
| **主要页面** | [`LawyerMatchingPage.tsx`](frontend-v2/src/features/lawyer-matching/pages/LawyerMatchingPage.tsx:1) |
| **核心组件** | `LawyerRecommendation`、`LawyerBookingModal`、`LawyerOnlineStatus`、`LawyerReviewModal` |
| **API 端点** | `/api/v1/lawyer-recommendation/recommend`、`/api/v1/lawyer-recommendation/recommend-by-keywords`、`/api/v1/lawfirm/lawyers`、`/api/v1/lawfirm/consultations`、`/api/v1/lawfirm/reviews` |
| **服务层** | [`lawyer_matching_service_enhanced.py`](backend/app/services/lawyer_matching_service_enhanced.py:1)、[`lawfirm_service.py`](backend/app/services/lawfirm_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_lawyer_matching_service.py`、`test_lawyer_recommendation_router.py`) |

### 3.27 法律文书商城 (`legal-document-mall`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 法律文书模板商城，支持文书浏览、分类筛选、价格计算、在线购买、收藏管理、订单管理 |
| **主要页面** | [`LegalDocumentMallPage.tsx`](frontend-v2/src/features/legal-document-mall/pages/LegalDocumentMallPage.tsx:1) |
| **核心组件** | `DocumentCard`、`DocumentCategoryList`、`DocumentGrid`、`DocumentPurchaseFlow` |
| **API 端点** | `/api/legal-documents`、`/api/legal-documents/categories`、`/api/legal-documents/{id}`、`/api/legal-documents/{id}/price`、`/api/legal-documents/{id}/purchase`、`/api/legal-documents/user/favorites` |
| **服务层** | [`legal_document_service.py`](backend/app/services/legal_document_service.py:1)、[`legal_document.py`](backend/app/models/legal_document.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_legal_document_service.py`)、✅ E2E 测试覆盖 (`legal-document.spec.ts`) |

### 3.28 推荐系统 (`recommendation`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 个性化推荐引擎，基于用户兴趣和行为进行律师、帖子、新闻的个性化推荐，支持新用户引导问卷、兴趣标签管理、用户交互记录 |
| **主要页面** | [`RecommendationPage.tsx`](frontend-v2/src/features/recommendation/pages/RecommendationPage.tsx:1)、[`OnboardingPage.tsx`](frontend-v2/src/features/recommendation/pages/OnboardingPage.tsx:1) |
| **核心组件** | 推荐卡片组件、兴趣标签组件、引导问卷组件 |
| **API 端点** | `/api/v1/recommendation/personalized`、`/api/v1/recommendation/enhanced`、`/api/v1/recommendation/survey`、`/api/v1/recommendation/onboarding`、`/api/v1/recommendation/interaction` |
| **服务层** | [`recommendation_service.py`](backend/app/services/recommendation_service.py:1)、[`user_interest_service.py`](backend/app/services/user_interest_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_recommendation_service.py`、`test_recommendation_api.py`) |

### 3.29 系统配置模块 (`system-config`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 系统配置管理中心，支持配置项管理、配置历史追踪、配置分组、配置导出导入、缓存刷新 |
| **主要页面** | [`SystemConfigPage.tsx`](frontend-v2/src/features/system-config/pages/SystemConfigPage.tsx:1) |
| **核心组件** | `ConfigList`、`ConfigEditor`、`ConfigHistory` |
| **API 端点** | `/api/v1/system/configs`、`/api/v1/system/configs/{id}`、`/api/v1/system/configs/history`、`/api/v1/system/configs/export`、`/api/v1/system/configs/import`、`/api/v1/system/configs/cache/refresh` |
| **服务层** | [`system/config.py`](backend/app/services/system/config.py:1)、[`unified_config.py`](backend/app/services/system/unified_config.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_system_config_service.py`、`test_unified_config.py`) |

### 3.30 上传功能 (`upload`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 统一文件上传服务，支持图片和附件上传、批量上传、进度追踪、图片压缩、文件校验 |
| **主要页面** | 无独立页面，作为基础服务被各模块调用 |
| **核心组件** | `FileUploader`、`ImageUploader`、`UploadDropzone`、`UploadList`、`UploadProgress` |
| **API 端点** | `/api/v1/upload/file`、`/api/v1/upload/image`、`/api/v1/upload/avatar`、`/api/v1/upload/files/{filename}`、`/api/v1/upload/images/{filename}` |
| **服务层** | [`upload.py`](backend/app/routers/upload.py:1)、[`storage_service.py`](backend/app/services/storage_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_upload.py`) |

### 3.31 系统监控 (`admin_monitor`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 系统监控与告警，支持服务健康检查、性能指标监控、数据库连接池监控、慢查询追踪、日志查看 |
| **主要页面** | [`MonitorPage.tsx`](frontend-v2/src/features/admin_monitor/pages/MonitorPage.tsx:1) |
| **核心组件** | `MetricCard`、`Charts`、`AlertList`、`LogViewer` |
| **API 端点** | `/api/v1/admin_monitor/metrics`、`/api/v1/admin_monitor/health`、`/api/v1/admin_monitor/logs`、`/api/v1/admin_monitor/alerts` |
| **服务层** | [`system_monitor.py`](backend/app/services/system_monitor.py:1)、[`admin_monitor.py`](backend/app/routers/admin_monitor.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_admin_monitor_router.py`) |

### 3.32 AI 质量监控 (`ai_quality`)

| 属性 | 详情 |
|------|------|
| **功能描述** | AI 服务质量监控与评估，支持响应质量评估、会话审查、模型配置管理、意图识别分析、指标追踪 |
| **主要页面** | [`AIQualityPage.tsx`](frontend-v2/src/features/ai_quality/pages/AIQualityPage.tsx:1) |
| **核心组件** | `QualityDashboard`、`MetricsChart`、`AlertList`、`SessionReview` |
| **API 端点** | `/api/v1/ai_quality/metrics`、`/api/v1/ai_quality/sessions`、`/api/v1/ai_quality/alerts`、`/api/v1/ai_quality/configs` |
| **服务层** | [`ai_quality.py`](backend/app/routers/ai_quality.py:1)、[`ai_metrics.py`](backend/app/services/ai_metrics.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_ai_quality_load.py`、`test_ai_quality_middleware.py`) |

### 3.33 AI 助手 (`ai-assistant`)

| 属性 | 详情 |
|------|------|
| **功能描述** | AI 助手服务，提供智能对话、法律知识问答、上下文理解能力 |
| **主要页面** | 无独立页面，作为基础服务被各模块调用 |
| **核心组件** | 无独立组件，集成到各咨询场景 |
| **API 端点** | `/api/v1/ai/assistant`、`/api/v1/ai/chat` |
| **服务层** | [`ai_assistant.py`](backend/app/services/ai_assistant.py:1)、[`ai/session.py`](backend/app/services/ai/session.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_ai_assistant.py`) |

### 3.34 认证模块 (`auth`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 用户认证与授权，支持登录、注册、JWT 令牌管理、双因素认证 |
| **主要页面** | [`Login/index.tsx`](frontend-v2/src/pages/auth/Login/index.tsx:1)、[`Register/index.tsx`](frontend-v2/src/pages/auth/Register/index.tsx:1) |
| **核心组件** | `LoginForm`、`RegisterForm`、`AuthStore` |
| **API 端点** | `/api/v1/auth/login`、`/api/v1/auth/register`、`/api/v1/auth/refresh`、`/api/v1/auth/logout` |
| **服务层** | [`user_service.py`](backend/app/services/user_service.py:1)、[`totp_service.py`](backend/app/services/totp_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_user_router.py`)、✅ E2E 测试覆盖 (`auth.spec.ts`) |

### 3.35 合同模块 (`contract`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 合同基础服务，提供合同数据结构与类型定义 |
| **主要页面** | 无独立页面，作为基础模块被 contracts 模块调用 |
| **核心组件** | 无独立组件 |
| **API 端点** | 与 contracts 模块共享 |
| **服务层** | [`contracts.py`](backend/app/models/contracts.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_contracts_export.py`) |

### 3.36 跨域模块 (`cross-domain`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 跨域配置与管理，支持域名管理、CORS 策略配置、跨域请求追踪 |
| **主要页面** | [`CrossDomainPage.tsx`](frontend-v2/src/features/cross-domain/pages/CrossDomainPage.tsx:1) |
| **核心组件** | `DomainForm`、`DomainList` |
| **API 端点** | `/api/v1/cross-domain/domains`、`/api/v1/cross-domain/configs` |
| **服务层** | [`cross_domain.py`](backend/app/routers/cross_domain.py:1)、[`cross_domain.py`](backend/app/models/cross_domain.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.37 论坛管理 (`forum-admin`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 论坛后台管理，支持帖子管理、评论管理、用户管理、分类/板块管理、内容审核 |
| **主要页面** | [`ForumAdminPage.tsx`](frontend-v2/src/features/forum-admin/pages/ForumAdminPage.tsx:1) |
| **核心组件** | `CategoryManager`、`UserManagement`、`ContentModeration` |
| **API 端点** | `/api/v1/forum/admin/posts`、`/api/v1/forum/admin/comments`、`/api/v1/forum/admin/categories`、`/api/v1/forum/admin/users` |
| **服务层** | [`forum_service.py`](backend/app/services/forum_service.py:1)、[`forum/moderation.py`](backend/app/routers/forum/moderation.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_forum_router.py`) |

### 3.38 论坛助手 (`forum-assistant`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 论坛 AI 助手，支持内容推荐、智能回复、帖子质量评估 |
| **主要页面** | [`ForumAssistantPage.tsx`](frontend-v2/src/features/forum-assistant/pages/ForumAssistantPage.tsx:1) |
| **核心组件** | `ContentRecommendation`、`SmartReply` |
| **API 端点** | `/api/v1/forum/assistant/recommend`、`/api/v1/forum/assistant/reply` |
| **服务层** | [`forum_ai_service.py`](backend/app/services/forum_ai_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.39 论坛表情反应 (`forum-reactions`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 论坛表情反应系统，支持点赞、收藏、表情反应、反应统计 |
| **主要页面** | 无独立页面，集成到论坛模块 |
| **核心组件** | `ReactionBar`、`ReactionPicker`、`FavoriteButton`、`PostReactions` |
| **API 端点** | `/api/v1/forum/reactions`、`/api/v1/forum/favorites` |
| **服务层** | [`forum/reactions.py`](backend/app/routers/forum/reactions.py:1)、[`forum/favorites.py`](backend/app/routers/forum/favorites.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_forum_favorites_reactions.py`) |

### 3.40 首页 (`home`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 平台首页，展示功能入口、推荐内容、统计信息、快速操作 |
| **主要页面** | [`HomePage.tsx`](frontend-v2/src/features/home/pages/HomePage.tsx:1) |
| **核心组件** | `HeroSection`、`FeatureCards`、`QuickActions`、`Recommendations`、`StatsSection` |
| **API 端点** | `/api/v1/home`、`/api/v1/home/stats`、`/api/v1/home/recommendations` |
| **服务层** | [`home.py`](backend/app/routers/home.py:1)、[`personalized_home.py`](backend/app/services/personalized_home.py:1) |
| **测试状态** | ✅ 单元测试覆盖、✅ E2E 测试覆盖 (`home.spec.ts`) |

### 3.41 知识库管理 (`knowledge_admin`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 法律知识库后台管理，支持文章管理、分类管理、向量化配置、RAG 检索优化 |
| **主要页面** | [`KnowledgeAdminPage.tsx`](frontend-v2/src/features/knowledge_admin/pages/KnowledgeAdminPage.tsx:1) |
| **核心组件** | `ArticleEditor`、`ArticleList`、`CategoryManager`、`KnowledgeStats` |
| **API 端点** | `/api/v1/knowledge_admin/articles`、`/api/v1/knowledge_admin/categories`、`/api/v1/knowledge_admin/vectorize` |
| **服务层** | [`knowledge_service.py`](backend/app/services/knowledge_service.py:1)、[`rag_knowledge.py`](backend/app/services/rag_knowledge.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.42 新闻 (`news`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 新闻资讯模块，支持新闻列表、新闻详情、新闻订阅 |
| **主要页面** | 无独立页面，集成到各内容场景 |
| **核心组件** | `NewsCard`、`NewsList` |
| **API 端点** | `/api/v1/news`、`/api/v1/news/{id}`、`/api/v1/news/subscriptions` |
| **服务层** | [`news/core.py`](backend/app/routers/news/core.py:1)、[`news_service.py`](backend/app/services/news_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_news_router.py`、`test_news_service.py`) |

### 3.43 新闻管理 (`news-admin`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 新闻后台管理，支持文章发布/编辑、分类/标签管理、新闻源配置、RSS 采集、评论管理 |
| **主要页面** | [`NewsAdminPage.tsx`](frontend-v2/src/features/news-admin/pages/NewsAdminPage.tsx:1)、[`NewsSourcesPage.tsx`](frontend-v2/src/features/news-admin/pages/NewsSourcesPage.tsx:1)、[`NewsTopicsPage.tsx`](frontend-v2/src/features/news-admin/pages/NewsTopicsPage.tsx:1) |
| **核心组件** | `ArticleEditor`、`ArticleList`、`ArticleReview`、`CategoryManager`、`NewsIngestRunList` |
| **API 端点** | `/api/v1/news/admin/articles`、`/api/v1/news/admin/sources`、`/api/v1/news/admin/topics`、`api/v1/news/admin/ingest-runs` |
| **服务层** | [`news/admin.py`](backend/app/routers/news/admin.py:1)、[`news_ai_pipeline_service.py`](backend/app/services/news_ai_pipeline_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.44 新闻评论 (`news-comments`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 新闻评论系统，支持评论发布、评论列表、评论管理、评论互动 |
| **主要页面** | [`NewsCommentsPage.tsx`](frontend-v2/src/features/news-comments/pages/NewsCommentsPage.tsx:1) |
| **核心组件** | `CommentForm`、`CommentList`、`CommentItem`、`CommentPanel`、`CommentPagination` |
| **API 端点** | `/api/v1/news/comments`、`/api/v1/news/comments/{id}` |
| **服务层** | [`news/comments.py`](backend/app/routers/news/comments.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.45 新闻内容 (`news-content`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 新闻内容创作与管理，支持新闻编辑、草稿管理、AI 内容辅助、标签管理、图片库 |
| **主要页面** | 无独立页面，集成到新闻管理模块 |
| **核心组件** | `NewsEditor`、`DraftsManager`、`AIContentAssistant`、`TagManager`、`ImageGallery` |
| **API 端点** | `/api/v1/news/content/editor`、`/api/v1/news/content/drafts`、`/api/v1/news/content/tags` |
| **服务层** | [`news/core.py`](backend/app/routers/news/core.py:1)、[`news_quality_service.py`](backend/app/services/news_quality_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.46 订单模块 (`order`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 订单管理，支持订单列表、订单详情、订单筛选、订单状态追踪 |
| **主要页面** | [`OrderListPage.tsx`](frontend-v2/src/features/order/pages/OrderListPage.tsx:1)、[`OrderDetailPage.tsx`](frontend-v2/src/features/order/pages/OrderDetailPage.tsx:1) |
| **核心组件** | `OrderCard`、`OrderList`、`OrderDetail`、`OrderFilter` |
| **API 端点** | `/api/v1/orders`、`/api/v1/orders/{id}` |
| **服务层** | [`payment/orders.py`](backend/app/routers/payment/orders.py:1)、[`order_tasks.py`](backend/app/tasks/order_tasks.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_payment_orders_create.py`) |

### 3.47 帖子模块 (`post`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 论坛帖子管理，支持帖子发布、编辑、删除、帖子列表、帖子详情 |
| **主要页面** | [`PostListPage.tsx`](frontend-v2/src/features/post/pages/PostListPage.tsx:1)、[`PostDetailPage.tsx`](frontend-v2/src/features/post/pages/PostDetailPage.tsx:1)、[`NewPostPage.tsx`](frontend-v2/src/features/post/pages/NewPostPage.tsx:1)、[`EditPostPage.tsx`](frontend-v2/src/features/post/pages/EditPostPage.tsx:1) |
| **核心组件** | `PostCard`、`PostEditor`、`PostList` |
| **API 端点** | `/api/v1/forum/posts`、`/api/v1/forum/posts/{id}` |
| **服务层** | [`forum/posts.py`](backend/app/routers/forum/posts.py:1)、[`forum_service.py`](backend/app/services/forum_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_forum_posts.py`) |

### 3.48 设置模块 (`settings`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 系统设置与用户偏好配置 |
| **主要页面** | [`SystemSettingsPage.tsx`](frontend-v2/src/features/settings/pages/SystemSettingsPage.tsx:1) |
| **核心组件** | 无独立组件，集成到各设置场景 |
| **API 端点** | `/api/v1/settings`、`/api/v1/user/settings` |
| **服务层** | [`user_service.py`](backend/app/services/user_service.py:1) |
| **测试状态** | ✅ 单元测试覆盖 |

### 3.49 用户模块 (`user`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 用户信息管理，支持个人资料、头像上传、用户设置、偏好配置 |
| **主要页面** | [`UserProfilePage.tsx`](frontend-v2/src/features/user/pages/UserProfilePage.tsx:1)、[`UserSettingsPage.tsx`](frontend-v2/src/features/user/pages/UserSettingsPage.tsx:1) |
| **核心组件** | `AvatarUpload`、`UserProfileForm` |
| **API 端点** | `/api/v1/user/profile`、`/api/v1/user/settings`、`/api/v1/user/avatar` |
| **服务层** | [`user_service.py`](backend/app/services/user_service.py:1)、[`user.py`](backend/app/routers/user.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_user_router.py`、`test_user_service.py`) |

### 3.50 微信模块 (`wechat`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 微信生态集成，支持微信登录、微信支付、微信公众号绑定、微信分享 |
| **主要页面** | [`WechatPage.tsx`](frontend-v2/src/features/wechat/pages/WechatPage.tsx:1)、[`WechatOfficialAccountPage.tsx`](frontend-v2/src/features/wechat/pages/WechatOfficialAccountPage.tsx:1)、[`WechatCallbackPage.tsx`](frontend-v2/src/features/wechat/pages/WechatCallbackPage.tsx:1) |
| **核心组件** | `WechatLoginButton`、`WechatPayButton`、`WechatBindCard`、`OfficialAccountQrCode`、`WechatShareDialog` |
| **API 端点** | `/api/v1/wechat/login`、`/api/v1/wechat/bind`、`api/v1/wechat/official-account`、`/api/v1/wechat-pay` |
| **服务层** | [`wechat_service.py`](backend/app/services/wechat_service.py:1)、[`wechat.py`](backend/app/routers/wechat.py:1)、[`wechat_pay.py`](backend/app/routers/wechat_pay.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_wechat.py`、`test_wechat_service.py`、`test_wechatpay_v3.py`) |

### 3.51 咨询模块 (`consultation`)

| 属性 | 详情 |
|------|------|
| **功能描述** | 法律咨询管理，支持咨询列表、咨询详情、咨询模板、咨询创建 |
| **主要页面** | [`ConsultationTemplatesPage.tsx`](frontend-v2/src/features/consultation/pages/ConsultationTemplatesPage.tsx:1) |
| **核心组件** | `ConsultationCard`、`ConsultationDetail`、`ConsultationList`、`CreateConsultationModal` |
| **API 端点** | `/api/v1/consultations`、`/api/v1/consultation-templates` |
| **服务层** | [`ai/consultations.py`](backend/app/services/ai/consultations.py:1)、[`consultation_templates.py`](backend/app/routers/consultation_templates.py:1) |
| **测试状态** | ✅ 单元测试覆盖 (`test_consultations.py`) |

---

## 4. 测试场景清单

### 4.1 用户认证场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| AUTH-001 | 用户注册 | 无 | 1. 访问注册页 2. 填写用户名/邮箱/密码 3. 提交表单 | 注册成功，跳转登录页 |
| AUTH-002 | 邮箱验证 | 已注册未验证 | 1. 点击验证邮件链接 | 邮箱验证成功 |
| AUTH-003 | 用户登录 | 已注册 | 1. 输入邮箱密码 2. 点击登录 | 登录成功，获取 Token |
| AUTH-004 | 双因素认证 | 已启用 2FA | 1. 输入密码登录 2. 输入 TOTP 码 | 验证成功，登录成功 |
| AUTH-005 | Token 刷新 | 已登录 | 1. Access Token 过期 2. 使用 Refresh Token 刷新 | 获取新 Token |
| AUTH-006 | 退出登录 | 已登录 | 1. 点击退出 | Token 失效，跳转登录页 |

### 4.2 AI 咨询场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| AI-001 | 文字咨询 | 已登录 | 1. 输入法律问题 2. 发送 | 获取 AI 响应，会话保存 |
| AI-002 | 语音咨询 | 已登录 | 1. 点击语音输入 2. 说话 3. 发送 | 语音转文字，获取响应 |
| AI-003 | 文件分析 | 已登录 | 1. 上传合同 2. 点击分析 | 识别风险点，生成报告 |
| AI-004 | 咨询历史 | 已登录 | 1. 访问历史页 | 显示历史会话列表 |
| AI-005 | 会话分享 | 已登录 | 1. 选择会话 2. 点击分享 | 生成分享链接 |

### 4.3 支付场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| PAY-001 | 创建订单 | 已登录 | 1. 选择商品 2. 点击购买 | 订单创建成功 |
| PAY-002 | 支付宝支付 | 有订单 | 1. 选择支付宝 2. 跳转支付 | 支付成功，订单更新 |
| PAY-003 | 微信支付 | 有订单 | 1. 选择微信 2. 扫码支付 | 支付成功，订单更新 |
| PAY-004 | 幂等性检查 | 重复回调 | 1. 发送相同回调 | 不重复处理 |
| PAY-005 | 订单查询 | 已登录 | 1. 访问订单页 | 显示订单列表 |

### 4.4 积分场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| PNT-001 | 每日签到 | 已登录 | 1. 访问签到页 2. 点击签到 | 获得积分 |
| PNT-002 | 连续签到 | 已连续签到 | 1. 第 7 天签到 | 获得额外奖励 |
| PNT-003 | 积分商城 | 已登录 | 1. 访问商城 | 显示商品列表 |
| PNT-004 | 积分兑换 | 有足够积分 | 1. 选择商品 2. 兑换 | 兑换成功，扣减积分 |
| PNT-005 | 积分流水 | 已登录 | 1. 访问流水页 | 显示积分记录 |

### 4.5 会员场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| VIP-001 | 会员购买 | 已登录 | 1. 选择套餐 2. 支付 | 会员激活 |
| VIP-002 | 权益验证 | 已会员 | 1. 使用付费功能 | 享受折扣 |
| VIP-003 | 会员续费 | 即将过期 | 1. 点击续费 | 有效期延长 |

### 4.6 视频咨询场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| VID-001 | 预约咨询 | 已登录 | 1. 选择律师 2. 选择时段 3. 支付 | 预约成功 |
| VID-002 | 日程冲突 | 时段已占用 | 1. 选择相同时段 | 提示冲突 |
| VID-003 | 进入房间 | 已预约 | 1. 咨询时间到 2. 点击进入 | 进入视频房间 |
| VID-004 | 结束咨询 | 咨询中 | 1. 点击结束 2. 填写总结 | 状态更新为完成 |

### 4.7 论坛场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| FOR-001 | 发布帖子 | 已登录 | 1. 点击发帖 2. 填写内容 | 帖子发布成功 |
| FOR-002 | 发表评论 | 已登录 | 1. 打开帖子 2. 发表评论 | 评论成功 |
| FOR-003 | 点赞 | 已登录 | 1. 点击表情 | 表情计数 +1 |
| FOR-004 | 收藏 | 已登录 | 1. 点击收藏 | 添加到收藏夹 |

### 4.8 通知场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| NOT-001 | 接收通知 | 已登录 | 1. 系统发送通知 2. 检查通知列表 | 通知显示在列表中 |
| NOT-002 | WebSocket 连接 | 已登录 | 1. 打开页面 2. 检查 WebSocket 状态 | 连接成功，实时接收 |
| NOT-003 | 标记已读 | 有未读通知 | 1. 点击通知 2. 检查状态 | 标记为已读 |
| NOT-004 | 通知设置 | 已登录 | 1. 修改通知偏好 | 设置保存成功 |

### 4.9 安全场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| SEC-001 | 启用 2FA | 已登录 | 1. 访问安全页 2. 扫描二维码 3. 输入验证码 | 2FA 启用成功 |
| SEC-002 | 设备管理 | 已登录 | 1. 查看设备列表 2. 移除设备 | 设备移除成功 |
| SEC-003 | 登录审计 | 已登录 | 1. 访问登录审计页 | 显示登录历史 |
| SEC-004 | 修改密码 | 已登录 | 1. 输入旧密码 2. 设置新密码 | 密码修改成功 |

### 4.10 搜索场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| SRH-001 | 关键词搜索 | 已登录 | 1. 输入关键词 2. 搜索 | 返回相关结果 |
| SRH-002 | 搜索建议 | 已登录 | 1. 输入部分文字 | 显示建议列表 |
| SRH-003 | 搜索历史 | 已登录 | 1. 访问搜索页 | 显示历史搜索 |
| SRH-004 | 多类型筛选 | 已登录 | 1. 选择类型筛选 | 结果按类型过滤 |

### 4.11 企业服务场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| ENT-001 | 企业信息设置 | 已登录 | 1. 填写企业信息 2. 保存 | 信息保存成功 |
| ENT-002 | 合规检查 | 已登录 | 1. 运行合规检查 2. 查看报告 | 生成合规报告 |
| ENT-003 | 团队管理 | 已登录 | 1. 添加成员 2. 设置权限 | 成员添加成功 |

### 4.12 推广场景

| 场景 ID | 场景名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| PRO-001 | 生成推广链接 | 律师已登录 | 1. 访问推广页 2. 生成链接 | 链接生成成功 |
| PRO-002 | 生成二维码 | 有推广链接 | 1. 点击生成二维码 | 二维码生成成功 |
| PRO-003 | 查看统计 | 有推广数据 | 1. 访问统计页 | 显示详细数据 |
| PRO-004 | 申请提现 | 有佣金余额 | 1. 填写提现金额 2. 提交 | 提现申请成功 |

---

## 5. 快速测试指南

### 5.1 后端测试

#### 运行所有测试
```bash
cd backend
py -m pytest tests/ -v
```

#### 运行特定模块测试
```bash
# AI 相关测试
py -m pytest tests/test_ai_*.py -v

# 支付相关测试
py -m pytest tests/test_payment*.py -v

# 论坛相关测试
py -m pytest tests/test_forum*.py -v

# 用户相关测试
py -m pytest tests/test_user*.py -v
```

#### 运行集成测试
```bash
py -m pytest tests/test_orders_pay_integration.py -v
```

#### 运行负载测试
```bash
py -m pytest tests/test_load.py -v
```

#### 运行安全测试
```bash
py -m pytest tests/test_security.py -v
```

#### 生成覆盖率报告
```bash
py -m pytest tests/ --cov=app --cov-report=html
```

### 5.2 前端测试

#### 运行 E2E 测试
```bash
cd frontend-v2

# 所有 E2E 测试
npm run test:e2e

# 特定测试
npm run test:e2e -- auth.spec.ts
npm run test:e2e -- payment.spec.ts
npm run test:e2e -- consultation.spec.ts
```

### 5.3 按功能模块测试

| 功能模块 | 后端测试命令 | 前端测试命令 |
|---------|-------------|-------------|
| AI 咨询 | `py -m pytest tests/test_ai_chat_comprehensive.py -v` | `npm run test:e2e -- consultation.spec.ts` |
| 支付系统 | `py -m pytest tests/test_payment_flow.py -v` | `npm run test:e2e -- payment.spec.ts` |
| 会员系统 | `py -m pytest tests/test_membership_service.py -v` | `npm run test:e2e -- membership.spec.ts` |
| 论坛功能 | `py -m pytest tests/test_forum_posts.py -v` | - |
| 视频咨询 | `py -m pytest tests/test_video_consultation.py -v` | `npm run test:e2e -- video-consultation.spec.ts` |
| 用户认证 | `py -m pytest tests/test_user_router.py -v` | `npm run test:e2e -- auth.spec.ts` |
| 积分系统 | `py -m pytest tests/test_points_service.py -v` | `npm run test:e2e -- points.spec.ts` |
| 推广系统 | `py -m pytest tests/test_promotion.py -v` | `npm run test:e2e -- promotion.spec.ts` |
| 通知系统 | `py -m pytest tests/test_notification_service.py -v` | `npm run test:e2e -- notification.spec.ts` |
| 安全中心 | `py -m pytest tests/test_security.py -v` | - |
| 搜索功能 | `py -m pytest tests/test_search_router.py -v` | - |
| 企业服务 | `py -m pytest tests/test_enterprise.py -v` | `npm run test:e2e -- enterprise.spec.ts` |
| 数据分析 | `py -m pytest tests/test_analytics_router.py -v` | `npm run test:e2e -- analytics.spec.ts` |
| 知识库 | `py -m pytest tests/test_knowledge_service.py -v` | - |
| 合同审查 | `py -m pytest tests/test_contract_review_api.py -v` | - |
| 法律文书 | `py -m pytest tests/test_legal_document_service.py -v` | `npm run test:e2e -- legal-document.spec.ts` |

### 5.4 前端组件测试

```bash
cd frontend-v2

# 运行组件单元测试
npm run test:unit

# 特定组件测试
npm run test:unit -- src/features/points/__tests__/CheckInButton.test.tsx
npm run test:unit -- src/features/points/__tests__/PointsBalance.test.tsx
npm run test:unit -- src/components/ui/__tests__/EmptyState.test.tsx
```

### 5.5 E2E 测试清单

| 测试文件 | 覆盖功能 | 状态 |
|---------|---------|------|
| `auth.spec.ts` | 登录、注册、认证流程 | ✅ |
| `payment.spec.ts` | 订单创建、支付流程 | ✅ |
| `consultation.spec.ts` | AI 咨询、律师预约 | ✅ |
| `membership.spec.ts` | 会员购买、权益验证 | ✅ |
| `video-consultation.spec.ts` | 视频咨询预约、进入房间 | ✅ |
| `points.spec.ts` | 积分签到、兑换 | ✅ |
| `promotion.spec.ts` | 推广链接、佣金管理 | ✅ |
| `notification.spec.ts` | 通知推送、标记已读 | ✅ |
| `enterprise.spec.ts` | 企业合规检查、团队管理 | ✅ |
| `legal-document.spec.ts` | 法律文书浏览、购买 | ✅ |
| `analytics.spec.ts` | 数据分析图表 | ✅ |
| `home.spec.ts` | 首页加载、功能入口 | ✅ |
| `navigation.spec.ts` | 路由导航、页面跳转 | ✅ |
| `responsive.spec.ts` | 响应式布局、移动端适配 | ✅ |

### 5.6 测试数据准备

#### 后端测试数据

```bash
cd backend

# 初始化测试数据
py scripts/seed_data.py

# 清理测试数据
py scripts/cleanup_e2e_data.py
```

#### 前端测试数据

```bash
cd frontend-v2

# 使用 Mock 数据
# 测试数据定义在 src/test/mocks/handlers.ts
```

---

## 6. 后端 API 路由清单

### 6.1 用户与认证

| 路由模块 | 路径前缀 | 描述 |
|---------|---------|------|
| 用户 | `/api/v1/user` | 用户信息管理 |
| 安全 | `/api/v1/security` | 账户安全、双因素认证 |
| 认证 | - | 登录、注册、JWT 令牌管理 |

### 6.2 AI 服务

| 路由模块 | 路径前缀 | 描述 |
|---------|---------|------|
| AI | `/api/v1/ai` | AI 对话、咨询 |
| AI 质量 | `/api/v1/ai_quality` | AI 服务质量监控 |
| 推荐 | `/api/v1/recommendation` | 个性化推荐 |

### 6.3 社区与内容

| 路由模块 | 路径前缀 | 描述 |
|---------|---------|------|
| 论坛 | `/api/v1/forum` | 论坛帖子、评论管理 |
| 新闻 | `/api/v1/news` | 新闻资讯 |

### 6.4 法律服务

| 路由模块 | 路径前缀 | 描述 |
|---------|---------|------|
| 律所 | `/api/v1/lawfirm` | 律所、律师管理 |
| 合同 | `/api/v1/contracts` | 合同审查 |
| 文档 | `/api/v1/document` | 文档管理 |
| 知识库 | `/api/v1/knowledge` | 法律知识查询 |

### 6.5 支付与结算

| 路由模块 | 路径前缀 | 描述 |
|---------|---------|------|
| 支付 | `/api/v1/payment` | 支付订单处理 |
| 结算 | `/api/v1/settlement` | 律师收益结算 |
| 积分 | `/api/v1/points` | 积分管理 |
| 会员 | `/api/v1/membership` | 会员权益 |

### 6.6 管理后台

| 路由模块 | 路径前缀 | 描述 |
|---------|---------|------|
| 管理员 | `/api/v1/admin` | 后台管理 |
| 管理 V1 | `/api/v1/admin_v1` | 后台管理 V1 |
| 系统管理 | `/api/v1/system_admin` | 系统配置管理 |

---

## 7. 数据库模型清单

### 7.1 用户相关

| 模型 | 描述 |
|------|------|
| `User` | 用户基本信息 |
| `UserProfile` | 用户扩展信息 |
| `UserSecurity` | 用户安全信息（双因素认证） |
| `UserConsent` | 用户同意记录 |
| `UserQuota` | 用户配额 |
| `UserBehaviorLog` | 用户行为日志 |

### 7.2 律师与律所

| 模型 | 描述 |
|------|------|
| `Lawfirm` | 律所信息 |
| `Lawyer` | 律师信息 |
| `LawyerSchedule` | 律师日程 |
| `LawyerHomepage` | 律师个人主页 |
| `LawyerReplyTemplate` | 律师回复模板 |
| `LawyerPromotionLink` | 律师推广链接 |

### 7.3 咨询与对话

| 模型 | 描述 |
|------|------|
| `Consultation` | 咨询记录 |
| `ConsultationMessage` | 咨询消息 |
| `ConsultationReview` | 咨询评价 |
| `AIChatSession` | AI 聊天会话 |
| `AIChatMessage` | AI 聊天消息 |

### 7.4 社区与内容

| 模型 | 描述 |
|------|------|
| `Forum` | 论坛 |
| `ForumPost` | 论坛帖子 |
| `ForumComment` | 论坛评论 |
| `ForumReaction` | 论坛点赞 |
| `ForumFavorite` | 收藏 |
| `News` | 新闻资讯 |
| `NewsComment` | 新闻评论 |

### 7.5 支付与订单

| 模型 | 描述 |
|------|------|
| `Order` | 订单 |
| `Payment` | 支付记录 |
| `PaymentCallback` | 支付回调 |
| `Refund` | 退款记录 |
| `Settlement` | 结算记录 |
| `SettlementWithdrawal` | 提现记录 |
| `SettlementIncome` | 收入记录 |
| `SettlementBankAccount` | 银行账户 |

### 7.6 积分与会员

| 模型 | 描述 |
|------|------|
| `PointsAccount` | 积分账户 |
| `PointsTransaction` | 积分流水 |
| `PointsProduct` | 积分商品 |
| `PointsOrder` | 积分订单 |
| `Membership` | 会员信息 |
| `MembershipPlan` | 会员计划 |

---

## 9. 前端 E2E 测试覆盖详情

### 9.1 认证流程测试

| 测试用例 | 描述 | 状态 |
|---------|------|------|
| `auth.spec.ts - 用户注册` | 验证注册流程 | ✅ |
| `auth.spec.ts - 用户登录` | 验证登录流程 | ✅ |
| `auth.spec.ts - Token 刷新` | 验证 Token 自动刷新 | ✅ |
| `auth.spec.ts - 退出登录` | 验证退出流程 | ✅ |

### 9.2 支付流程测试

| 测试用例 | 描述 | 状态 |
|---------|------|------|
| `payment.spec.ts - 创建订单` | 验证订单创建 | ✅ |
| `payment.spec.ts - 订单列表` | 验证订单展示 | ✅ |
| `payment.spec.ts - 支付回调` | 验证支付结果 | ✅ |

### 9.3 AI 咨询测试

| 测试用例 | 描述 | 状态 |
|---------|------|------|
| `consultation.spec.ts - 文字咨询` | 验证 AI 问答 | ✅ |
| `consultation.spec.ts - 咨询历史` | 验证历史记录 | ✅ |
| `consultation.spec.ts - 律师推荐` | 验证推荐功能 | ✅ |

---

## 10. 版本信息

| 项目 | 值 |
|------|-----|
| 文档版本 | 1.4.0 |
| 创建日期 | 2026-02-18 |
| 最后更新 | 2026-02-18 |
| 更新说明 | 新增 21 个前端功能模块详情：admin_monitor, ai_quality, ai-assistant, auth, contract, cross-domain, forum-admin, forum-assistant, forum-reactions, home, knowledge_admin, news, news-admin, news-comments, news-content, order, post, settings, user, wechat, consultation |
| 项目 | 百姓助手 |

---

> 本文档为百姓助手项目的业务架构思维导图，旨在帮助团队成员快速了解项目整体结构和各模块功能。

---

## 附录 A：快速链接

| 文档 | 路径 |
|------|------|
| 技术架构文档 | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| 功能清单 | [`FEATURES.md`](FEATURES.md) |
| API 文档 | [`API.md`](API.md) |
| 开发指南 | [`DEVELOPMENT.md`](DEVELOPMENT.md) |
| 运维文档 | [`OPERATIONS.md`](OPERATIONS.md) |
| 测试指南 | [`backend/tests/TESTING_GUIDE.md`](backend/tests/TESTING_GUIDE.md) |

## 附录 B：核心文件索引

### 后端核心文件

| 文件 | 描述 |
|------|------|
| [`backend/app/main.py`](backend/app/main.py:1) | FastAPI 应用入口 |
| [`backend/app/config/settings.py`](backend/app/config/settings.py:1) | 应用配置 |
| [`backend/app/database/engine.py`](backend/app/database/engine.py:1) | 数据库引擎 |
| [`backend/app/services/`](backend/app/services/) | 业务服务层 |
| [`backend/app/routers/`](backend/app/routers/) | API 路由 |
| [`backend/app/models/`](backend/app/models/) | 数据模型 |

### 前端核心文件

| 文件 | 描述 |
|------|------|
| [`frontend-v2/src/main.tsx`](frontend-v2/src/main.tsx:1) | React 应用入口 |
| [`frontend-v2/src/app/App.tsx`](frontend-v2/src/app/App.tsx:1) | 根组件 |
| [`frontend-v2/src/app/providers/Router.tsx`](frontend-v2/src/app/providers/Router.tsx:1) | 路由配置 |
| [`frontend-v2/src/features/`](frontend-v2/src/features/) | 功能模块 |
| [`frontend-v2/src/components/`](frontend-v2/src/components/) | 通用组件 |
| [`frontend-v2/src/shared/`](frontend-v2/src/shared/) | 共享资源 |

## 附录 C：测试命令速查

### 后端测试速查

```bash
# 运行所有测试
cd backend && py -m pytest tests/ -v

# 运行特定模块
py -m pytest tests/test_ai_*.py -v          # AI 测试
py -m pytest tests/test_payment*.py -v      # 支付测试
py -m pytest tests/test_forum*.py -v        # 论坛测试
py -m pytest tests/test_user*.py -v         # 用户测试

# 运行集成测试
py -m pytest tests/test_orders_pay_integration.py -v

# 生成覆盖率报告
py -m pytest tests/ --cov=app --cov-report=html
```

### 前端测试速查

```bash
cd frontend-v2

# 运行 E2E 测试
npm run test:e2e

# 运行特定 E2E 测试
npm run test:e2e -- auth.spec.ts
npm run test:e2e -- payment.spec.ts
npm run test:e2e -- consultation.spec.ts

# 运行组件测试
npm run test:unit
```