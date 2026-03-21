# 百姓助手 - 功能清单

> 基于 2026-03-21 实际代码库

## 1. 微服务模块

| 服务 | 端口 | 功能 | 状态 |
|------|------|------|------|
| user-service | 8001 | 用户、认证、会员 | ✅ |
| payment-channel-service | 8002 | 支付通道 | ✅ |
| payment-accounting-service | 8003 | 账务结算 | ✅ |
| legal-service | 8004 | 律师、法律知识 | ✅ |
| ai-service | 8005 | AI 对话 | ✅ |
| news-service | 8006 | 新闻资讯 | ✅ |
| community-service | 8007 | 社区论坛 | ✅ |
| points-service | 8008 | 积分系统 | ✅ |
| notification-service | 8009 | 通知推送 | ✅ |
| recommendation-service | 8010 | 推荐系统 | ✅ |
| search-service | 8011 | 搜索服务 | ✅ |

## 2. 后端路由 (32 个)

### 2.1 管理后台

| 路由 | 文件 | 功能 |
|------|------|------|
| /admin/* | admin.py | 管理功能 |
| /admin_v1/* | admin_v1.py | 新管理 API |
| /admin_monitor/* | admin_monitor.py | 系统监控 |
| /system_admin/* | system_admin/ | 系统配置 |

### 2.2 核心业务

| 路由 | 文件 | 功能 |
|------|------|------|
| /lawfirm/* | lawfirm/ | 律师、律所 |
| /settlement/* | settlement/ | 结算 |
| /document/* | document.py | 文档 |
| /knowledge/* | knowledge.py | 知识库 |
| /membership/* | membership.py | 会员 |
| /video_consultation/* | video_consultation.py | 视频咨询 |
| /calendar/* | calendar.py | 日程 |
| /feedback/* | feedback.py | 反馈 |
| /reviews/* | reviews.py | 评价 |
| /promotion/* | promotion.py | 推广 |
| /enterprise/* | enterprise.py | 企业服务 |

### 2.3 基础设施

| 路由 | 文件 | 功能 |
|------|------|------|
| /wechat_pay/* | wechat_pay.py | 微信支付 |
| /upload/* | upload.py | 文件上传 |
| /security/* | security.py | 安全 |
| /websocket/* | websocket.py | WebSocket |
| /home/* | home.py | 首页 |
| /vertical/* | vertical_channel.py | 垂直频道 |
| /faq/* | faq.py | FAQ |
| /analytics/* | analytics.py | 分析 |
| /moderation/* | moderation.py | 内容审核 |
| /ab_testing/* | ab_testing.py | A/B 测试 |
| /funnel_analysis/* | funnel_analysis.py | 漏斗分析 |
| /channel_tracking/* | channel_tracking.py | 渠道追踪 |
| /cross_domain/* | cross_domain.py | 跨域 |
| /integration/* | integration.py | 集成 |
| /consultation_templates/* | consultation_templates.py | 咨询模板 |
| /document_templates/* | document_templates.py | 文档模板 |
| /knowledge_admin/* | knowledge_admin.py | 知识管理 |
| /system/* | system.py | 系统 |

## 3. 后端模型 (29 个)

| 模型 | 文件 | 说明 |
|------|------|------|
| User | user.py | 用户 |
| UserQuota | user_quota.py | 配额 |
| UserConsent | user_consent.py | 授权 |
| UserSecurity | user_security.py | 安全设置 |
| Consultation | consultation.py | 咨询 |
| ConsultationReview | consultation_review.py | 咨询审核 |
| Contract | contracts.py | 合同 |
| Domain | cross_domain.py | 域名 |
| Channel | channel.py | 渠道 |
| LawFirm | lawfirm.py | 律所 |
| Lawyer | lawfirm.py | 律师 |
| LawyerConsultation | lawfirm.py | 律师咨询 |
| LawyerReview | lawfirm.py | 律师评价 |
| LegalKnowledge | knowledge.py | 法律知识 |
| ConsultationTemplate | knowledge.py | 咨询模板 |
| GeneratedDocument | document.py | 生成文档 |
| DocumentTemplate | document_template.py | 文档模板 |
| SystemConfig | system.py | 系统配置 |
| AdminLog | system.py | 管理员日志 |
| CalendarReminder | calendar.py | 日程提醒 |
| FeedbackTicket | feedback.py | 反馈工单 |
| LawyerWallet | settlement.py | 律师钱包 |
| LawyerIncome | settlement.py | 律师收入 |
| LawyerBank | settlement.py | 银行账户 |
| Withdrawal | settlement.py | 提现 |
| UserProfile | user_profile.py | 用户画像 |
| UserInterest | user_profile.py | 用户兴趣 |
| UserTag | user_profile.py | 用户标签 |
| PeriodicTask | periodic_task.py | 定时任务 |
| Membership | membership.py | 会员 |
| VideoConsultation | video_consultation.py | 视频咨询 |
| Notification | notification.py | 通知 |
| Payment | payment.py | 支付 |

## 4. 前端 (frontend-v2)

### 4.1 路由配置

- `/` - 首页
- `/chat` - AI 咨询
- `/lawfirm` - 律师列表
- `/search` - 全局搜索
- `/knowledge` - 知识库
- `/news` - 新闻资讯
- `/forum` - 社区论坛
- `/documents` - 文档中心
- `/contracts` - 合同审查
- `/vip` - 会员中心
- `/admin` - 管理后台

### 4.2 技术栈

- React 18
- TypeScript
- Vite
- React Router
- TanStack Query
- Ant Design
- Zustand

## 5. 已删除功能

以下功能已从后端删除，迁移到微服务：

- ❌ `news/` 目录 → news-service (8006)
- ❌ `forum/` 目录 → community-service (8007)
- ❌ `ai/` 目录 → ai-service (8005)
- ❌ `user.py` → user-service (8001)
- ❌ `payment/` 目录 → payment-channel-service (8002)
- ❌ `points/` 目录 → points-service (8008)
- ❌ `notification.py` → notification-service (8009)
- ❌ `recommendation/` → recommendation-service (8010)
- ❌ `search/` → search-service (8011)
- ❌ `contracts.py` → legal-service (8004)
- ❌ `rss_ingest_service.py` → news-service
- ❌ `news_ai/` → news-service
- ❌ `n1_query_optimizer.py` → 已删除
- ❌ `lawyer_points_service.py` → points-service
- ❌ `order_tasks.py` → payment-channel-service
