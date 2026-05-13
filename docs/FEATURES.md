# 百姓法律助手 - 功能清单

> 基于 2026-05-11 实际代码库

## 1. 微服务模块

| 服务 | 端口 | 功能 | 状态 |
|------|------|------|------|
| backend (BFF) | 8000 | BFF 聚合层 | ✅ |
| user-service | 8001 | 用户、认证、会员 | ✅ |
| legal-service | 8004 | 律师、法律知识 | ✅ |
| ai-service | 8005 | AI 对话 | ✅ |
| news-service | 8006 | 新闻资讯 | ✅ |
| community-service | 8007 | 社区论坛 | ✅ |
| points-service | 8008 | 积分系统 | ✅ |
| search-service | 8009 | 搜索服务 | ✅ |
| order-service | 8010 | 订单/支付 | ✅ |
| knowledge-service | 8081 | 知识库 | ✅ |
| archive-service | 8013 | 档案服务 | ✅ |
| embedding-service | 8082 | 向量嵌入 | ✅ |

## 2. 后端路由 (BFF 层)

### 2.1 认证与用户

| 路由 | 文件 | 功能 |
|------|------|------|
| /api/auth/* | auth.py | 登录/注册/登出/刷新 |
| /api/user/* | user_profile.py | 用户信息/设置 |
| /api/v1/security/* | security.py | 安全设置/2FA |

### 2.2 管理后台

| 路由 | 文件 | 功能 |
|------|------|------|
| /api/v1/admin/* | admin.py | 管理统计 |
| /api/v1/admin_v1/* | admin_v1.py | 新管理 API |
| /api/v1/admin/monitor/* | admin_monitor.py | 系统监控 |

### 2.3 核心业务

| 路由 | 文件 | 功能 |
|------|------|------|
| /api/v1/upload/* | upload.py | 文件上传/访问 |
| /api/v1/home/* | home.py | 首页/推荐 |
| /api/v1/ab/* | ab_testing.py | A/B 测试 |
| /api/v1/cross-domain/* | cross_domain.py | 跨域验证 |
| /ws | websocket.py | WebSocket 通知 |

### 2.4 微服务代理

| 路由前缀 | 目标服务 | 说明 |
|----------|---------|------|
| /api/v1/legal/* | legal-service:8004 | 律师/法律知识 |
| /api/v1/ai/* | ai-service:8005 | AI 对话 |
| /api/v1/news/* | news-service:8006 | 新闻资讯 |
| /api/v1/community/* | community-service:8007 | 社区论坛 |
| /api/v1/points/* | points-service:8008 | 积分系统 |
| /api/v1/search/* | search-service:8009 | 搜索服务 |
| /api/v1/orders/* | order-service:8010 | 订单/支付 |

## 3. 后端模型

| 模型 | 文件 | 说明 |
|------|------|------|
| User | user.py | 用户 |
| UserQuota | user_quota.py | 配额 |
| UserConsent | user_consent.py | 授权 |
| UserSecurity | user_security.py | 安全设置 |
| UserProfile | user_profile.py | 用户画像 |
| Consultation | consultation.py | 咨询 |
| Contract | contracts.py | 合同 |
| Domain | cross_domain.py | 域名 |
| Channel | channel.py | 渠道 |
| LawFirm | lawfirm.py | 律所 |
| LegalKnowledge | knowledge.py | 法律知识 |
| GeneratedDocument | document.py | 生成文档 |
| DocumentTemplate | document_template.py | 文档模板 |
| SystemConfig | system.py | 系统配置 |
| CalendarReminder | calendar.py | 日程提醒 |
| FeedbackTicket | feedback.py | 反馈工单 |
| Membership | membership.py | 会员 |
| Notification | notification.py | 通知 |
| Payment | payment.py | 支付 |
| PeriodicTask | periodic_task.py | 定时任务 |
| ModerationLog | moderation.py | 内容审核 |
| AnalyticsEvent | analytics.py | 分析事件 |

## 4. 前端功能模块 (frontend-v2)

### 4.1 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| / | Home | 首页 |
| /chat | Chat | AI 法律咨询 |
| /lawyer | Lawyer | 律师列表/详情 |
| /search | Search | 全局搜索 |
| /knowledge | Knowledge | 知识库 |
| /news | News | 新闻资讯 |
| /forum | Forum | 社区论坛 |
| /documents | LegalDocumentMall | 法律文书商城 |
| /contracts | ContractReview | 合同审查 |
| /vip | Membership | 会员中心 |
| /points | Points | 积分系统 |
| /profile | Profile | 个人中心 |
| /notification | NotificationCenter | 通知中心 |
| /payment | Payment | 支付 |
| /enterprise | Enterprise | 企业服务 |
| /login, /register | Auth | 登录/注册 |

### 4.2 功能特性

| 模块 | 特性 |
|------|------|
| AI 咨询 | LangChain + RAG 知识库问答、流式响应 |
| 律师服务 | 律师列表/详情/预约、律所展示 |
| 合同审查 | AI 自动审查、风险提示、建议列表 |
| 社区论坛 | 发帖/回帖、点赞/收藏、版主管理 |
| 新闻资讯 | 法律新闻、AI 生成、订阅管理 |
| 会员体系 | VIP/SVIP 等级、权益对比、支付宝/微信支付 |
| 积分系统 | 签到、积分兑换、积分商城 |
| 通知中心 | 实时 WebSocket 通知、模板管理 |
| 全局搜索 | 跨服务聚合搜索、搜索建议 |
| 安全设置 | TOTP 2FA、设备管理、登录审计 |
| 推广系统 | 推广链接、佣金管理、提现 |
| 企业服务 | 合规报告、企业法律顾问 |
| 视频咨询 | 在线视频法律咨询 |
| 垂直频道 | 频道内容、话题列表 |

### 4.3 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18 | UI 框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 5.x | 构建工具 |
| Tailwind CSS | 3.x | CSS 框架 |
| Zustand | 4.x | 状态管理 |
| TanStack Query | 5.x | 数据获取 |
| React Router | 6.x | 路由管理 |
| Playwright | - | E2E 测试 |
