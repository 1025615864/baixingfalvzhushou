# 百姓助手 - 业务功能清单文档

> 本文档记录百姓助手系统的所有业务功能模块，包括用户端功能、管理后台功能、后端API路由、服务层和数据模型。

---

## 1. 功能模块总览

| 类别 | 数量 |
|------|------|
| 用户端功能模块 | 25+ |
| 管理后台功能模块 | 8+ |
| 后端API路由模块 | 45+ |
| 后端服务层模块 | 95+ |
| 数据库模型 | 35+ |

---

## 2. 用户端功能模块

### 2.1 核心服务

| 功能模块 | 标识符 | 描述 |
|----------|--------|------|
| AI法律咨询 | `ai-consultation` | AI智能法律咨询、问答 |
| AI聊天 | `chat` | 基于LangChain的AI对话 |
| 律师服务 | `lawyer` | 律师查找、咨询、预约 |
| 律师匹配 | `lawyer-matching` | 智能律师推荐匹配 |

### 2.2 法律工具

| 功能模块 | 标识符 | 描述 |
|----------|--------|------|
| 合同管理 | `contracts` | 合同审查、管理 |
| 文档管理 | `document` | 法律文档处理 |
| 法律知识库 | `knowledge` | 法律知识查询 |
| 法律日历 | `calendar` | 法律时效计算 |

### 2.3 社区与内容

| 功能模块 | 标识符 | 描述 |
|----------|--------|------|
| 论坛 | `forum` | 法律论坛、社区讨论 |
| 帖子 | `post` | 帖子发布与管理 |
| 新闻资讯 | `news` | 法律新闻推送 |

### 2.4 交易与支付

| 功能模块 | 标识符 | 描述 |
|----------|--------|------|
| 支付 | `payment` | 多通道支付（支付宝、微信、IkunPay） |
| 订单 | `order` | 订单管理 |
| 积分系统 | `points` | 积分商城、积分任务 |
| 会员 | `membership` | 会员权益管理 |
| 结算 | `settlement` | 律师收益结算 |

### 2.5 用户中心

| 功能模块 | 标识符 | 描述 |
|----------|--------|------|
| 用户 | `user` | 个人信息管理 |
| 安全中心 | `security` | 账户安全、双因素认证 |
| 通知 | `notification` | 消息通知 |
| 反馈 | `feedback` | 用户反馈 |

### 2.6 企业服务

| 功能模块 | 标识符 | 描述 |
|----------|--------|------|
| 企业服务 | `enterprise` | 企业法律服务 |
| 推广 | `promotion` | 律师推广管理 |

### 2.7 其他功能

| 功能模块 | 标识符 | 描述 |
|----------|--------|------|
| 搜索 | `search` | 全局搜索 |
| 推荐 | `recommendation` | 个性化推荐 |
| FAQ | `faq` | 常见问题 |
| 静态页面 | `static-pages` | 关于、帮助、隐私条款 |
| 微信生态 | `wechat` | 微信公众号集成 |
| 渠道管理 | `channel` | 渠道追踪 |

---

## 3. 管理后台功能模块

| 功能模块 | 标识符 | 描述 |
|----------|--------|------|
| 系统监控 | `admin_monitor` | 系统运行状态监控 |
| AI质量监控 | `ai_quality` | AI服务质量追踪 |
| 论坛管理 | `forum-admin` | 论坛内容管理 |
| 新闻管理 | `news-admin` | 新闻发布管理 |
| 知识库管理 | `knowledge_admin` | 知识库维护 |
| 内容审核 | `moderation` | UGC内容审核 |
| 推广管理 | `promotion` | 推广活动管理 |
| 系统配置 | `system-config` | 系统参数配置 |

---

## 4. 后端API路由清单

### 4.1 用户与认证

| 路由模块 | 路径前缀 | 描述 |
|----------|----------|------|
| 用户 | `/api/v1/user` | 用户信息管理 |
| 安全 | `/api/v1/security` | 账户安全、双因素认证 |
| 认证 | - | 登录、注册、JWT令牌管理 |

### 4.2 AI服务

| 路由模块 | 路径前缀 | 描述 |
|----------|----------|------|
| AI | `/api/v1/ai` | AI对话、咨询 |
| AI质量 | `/api/v1/ai_quality` | AI服务质量监控 |
| 推荐 | `/api/v1/recommendation` | 个性化推荐 |

### 4.3 社区与内容

| 路由模块 | 路径前缀 | 描述 |
|----------|----------|------|
| 论坛 | `/api/v1/forum` | 论坛帖子、评论管理 |
| 新闻 | `/api/v1/news` | 新闻资讯 |
| 问答 | - | 问答社区 |

### 4.4 法律服务

| 路由模块 | 路径前缀 | 描述 |
|----------|----------|------|
| 律所 | `/api/v1/lawfirm` | 律所、律师管理 |
| 合同 | `/api/v1/contracts` | 合同审查 |
| 文档 | `/api/v1/document` | 文档管理 |
| 知识库 | `/api/v1/knowledge` | 法律知识查询 |

### 4.5 支付与结算

| 路由模块 | 路径前缀 | 描述 |
|----------|----------|------|
| 支付 | `/api/v1/payment` | 支付订单处理 |
| 结算 | `/api/v1/settlement` | 律师收益结算 |
| 积分 | `/api/v1/points` | 积分管理 |
| 会员 | `/api/v1/membership` | 会员权益 |

### 4.6 管理后台

| 路由模块 | 路径前缀 | 描述 |
|----------|----------|------|
| 管理员 | `/api/v1/admin` | 后台管理 |
| 管理V1 | `/api/v1/admin_v1` | 后台管理V1 |
| 系统管理 | `/api/v1/system_admin` | 系统配置管理 |
| 系统 | `/api/v1/system` | 系统参数 |

### 4.7 分析与监控

| 路由模块 | 路径前缀 | 描述 |
|----------|----------|------|
| 分析 | `/api/v1/analytics` | 数据分析 |
| 漏斗分析 | `/api/v1/funnel_analysis` | 转化漏斗分析 |
| 监控 | `/api/v1/admin_monitor` | 系统监控 |
| 健康检查 | - | 健康检查接口 |

### 4.8 其他服务

| 路由模块 | 路径前缀 | 描述 |
|----------|----------|------|
| 搜索 | `/api/v1/search` | 全局搜索 |
| 通知 | `/api/v1/notification` | 消息通知 |
| 反馈 | `/api/v1/feedback` | 用户反馈 |
| FAQ | `/api/v1/faq` | 常见问题 |
| 上传 | `/api/v1/upload` | 文件上传 |
| WebSocket | `/ws` | WebSocket实时通信 |
| A/B测试 | `/api/v1/ab_testing` | A/B测试 |
| 渠道追踪 | `/api/v1/channel` | 渠道追踪 |
| 微信 | `/api/v1/wechat` | 微信生态集成 |
| 企业服务 | `/api/v1/enterprise` | 企业法律服务 |
| 咨询模板 | `/api/v1/consultation_templates` | 咨询模板管理 |
| 文档模板 | `/api/v1/document_templates` | 文档模板管理 |
| 律师推荐 | `/api/v1/lawyer_recommendation` | 律师推荐 |
| 评价 | `/api/v1/reviews` | 服务评价 |
| 律师主页 | - | 律师个人主页 |
| 日历 | `/api/v1/calendar` | 法律日历 |
| 首页 | `/api/v1/home` | 首页数据 |
| 集成 | `/api/v1/integration` | 第三方集成 |
| 跨域 | `/api/v1/cross_domain` | 跨域数据 |

---

## 5. 后端服务层清单

### 5.1 核心服务

| 服务模块 | 路径 | 描述 |
|----------|------|------|
| 基础服务 | `services/base.py` | 基础服务类 |
| 用户服务 | `services/user_service.py` | 用户管理 |
| AI助手 | `services/ai_assistant.py` | AI助手 |
| 律师服务 | `services/lawyer_matching_service.py` | 律师匹配 |
| 律师增强服务 | `services/lawyer_matching_service_enhanced.py` | 增强律师匹配 |
| 推荐服务 | `services/recommendation_service.py` | 个性化推荐 |
| 搜索服务 | `services/search_service.py` | 搜索功能 |
| 缓存服务 | `services/cache_service.py` | 缓存管理 |
| 分析服务 | `services/analytics_service.py` | 数据分析 |

### 5.2 AI服务

| 服务模块 | 路径 | 描述 |
|----------|------|------|
| AI核心 | `services/ai/core.py` | AI核心逻辑 |
| AI会话 | `services/ai/session.py` | 会话管理 |
| AI知识库 | `services/ai/knowledge_base.py` | 知识库 |
| AI配置 | `services/ai/config_manager.py` | 配置管理 |
| AI模型 | `services/ai/models.py` | 模型管理 |
| AI提示词 | `services/ai/prompts.py` | 提示词管理 |
| AI咨询 | `services/ai/consultation_service.py` | 咨询服务 |
| AI聊天 | `services/ai/chat.py` | 聊天服务 |
| AI用户画像 | `services/ai/user_profile.py` | 用户画像 |
| AI合规 | `services/ai_compliance.py` | 合规检查 |
| AI意图识别 | `services/ai_intent.py` | 意图识别 |
| AI响应策略 | `services/ai_response_strategy.py` | 响应策略 |
| AI MCP | `services/ai_mcp_mixin.py` | MCP集成 |
| AI指标 | `services/ai_metrics.py` | 质量指标 |
| 文档理解 | `services/multimodal_consultation.py` | 多模态咨询 |
| 关键词提取 | `services/keyword_extraction_service.py` | 关键词提取 |

### 5.3 社区服务

| 服务模块 | 路径 | 描述 |
|----------|------|------|
| 论坛核心 | `services/forum_service.py` | 论坛核心 |
| 论坛帖子 | `services/forum/posts.py` | 帖子管理 |
| 论坛评论 | `services/forum/comments.py` | 评论管理 |
| 论坛AI | `services/forum_ai_service.py` | 论坛AI功能 |
| 新闻服务 | `services/news_service.py` | 新闻服务 |
| 新闻核心 | `services/news/core.py` | 新闻核心 |
| 新闻AI | `services/news_ai/core.py` | 新闻AI处理 |
| 新闻推荐 | `services/news_recommendation_service.py` | 新闻推荐 |
| AI内容质量 | `services/content_quality.py` | 内容质量 |

### 5.4 法律服务

| 服务模块 | 路径 | 描述 |
|----------|------|------|
| 律所服务 | `services/lawfirm_service.py` | 律所管理 |
| 律所核心 | `services/lawfirm/firms.py` | 律所核心 |
| 律师管理 | `services/lawfirm/lawyers.py` | 律师管理 |
| 咨询管理 | `services/lawfirm/consultations.py` | 咨询管理 |
| 律师主页 | `services/lawyer_homepage_service.py` | 律师主页 |
| 合同审查 | `services/contract_review_service.py` | 合同审查 |
| 合同历史 | `services/contracts/history_service.py` | 合同历史 |
| 合同服务 | `services/contracts/review_service.py` | 审查服务 |
| 文档核心 | `services/document/core.py` | 文档核心 |
| 文档模板 | `services/document/templates.py` | 文档模板 |
| 文档存储 | `services/document/storage.py` | 文档存储 |
| 知识服务 | `services/knowledge_service.py` | 知识服务 |
| 知识库核心 | `services/knowledge/core.py` | 知识库核心 |
| 知识向量化 | `services/knowledge/vectorize.py` | 向量化 |
| RAG知识 | `services/rag_knowledge.py` | RAG知识库 |

### 5.5 支付与结算

| 服务模块 | 路径 | 描述 |
|----------|------|------|
| 支付服务 | `services/payment_service.py` | 支付核心 |
| 支付核心 | `services/payment/core.py` | 支付核心 |
| 支付宝 | `services/payment/alipay.py` | 支付宝集成 |
| 微信支付 | `services/payment/wechatpay.py` | 微信支付 |
| 结算服务 | `services/settlement_service.py` | 结算核心 |
| 结算核心 | `services/settlement/core.py` | 结算核心 |
| 结算收入 | `services/settlement/income.py` | 收入管理 |
| 结算提现 | `services/settlement/withdrawal.py` | 提现管理 |
| 积分服务 | `services/points_service.py` | 积分核心 |
| 积分管理 | `services/points_manager.py` | 积分管理 |
| 积分DB | `services/points/points_service_db.py` | 积分数据 |
| 积分V2 | `services/points/points_service_v2.py` | 积分V2 |
| 积分商品 | `services/points/product_service.py` | 积分商品 |
| 会员服务 | `services/membership_service.py` | 会员服务 |
| 订单任务 | `services/order_tasks.py` | 订单任务 |

### 5.6 用户服务

| 服务模块 | 路径 | 描述 |
|----------|------|------|
| 用户服务 | `services/user_service.py` | 用户管理 |
| 用户安全 | `services/user_security_service.py` | 用户安全 |
| TOTP服务 | `services/totp_service.py` | 双因素认证 |
| 设备管理 | `services/device_manager.py` | 设备管理 |
| 登录审计 | `services/login_audit_service.py` | 登录审计 |
| 推荐跟进 | `services/referral_service.py` | 推荐服务 |
| 用户分段 | `services/user_segmentation.py` | 用户分段 |
| 用户兴趣 | `services/user_interest_service.py` | 用户兴趣 |
| 通知服务 | `services/notification_service.py` | 通知服务 |
| 统一通知 | `services/unified_notification_service.py` | 统一通知 |
| 反馈服务 | `services/faq_service.py` | 反馈服务 |
| FAQ | `services/faq/core.py` | 常见问题 |

### 5.7 分析与监控

| 服务模块 | 路径 | 描述 |
|----------|------|------|
| 分析服务 | `services/analytics.py` | 数据分析 |
| 分析核心 | `services/analytics/core.py` | 分析核心 |
| 分析API | `services/analytics/api.py` | 分析API |
| 漏斗分析 | `services/funnel_analysis.py` | 漏斗分析 |
| 系统监控 | `services/system_monitor.py` | 系统监控 |
| A/B测试 | `services/ab_testing.py` | A/B测试 |

### 5.8 工具与基础设施

| 服务模块 | 路径 | 描述 |
|----------|------|------|
| 缓存优化 | `services/cache_optimizer.py` | 缓存优化 |
| 存储服务 | `services/storage_service.py` | 存储服务 |
| 邮件服务 | `services/email_service.py` | 邮件发送 |
| 邮件核心 | `services/email/core.py` | 邮件核心 |
| 邮件模板 | `services/email/templates.py` | 邮件模板 |
| 邮件优化 | `services/email/optimizer.py` | 邮件优化 |
| 验证码 | `services/email/verification.py` | 邮箱验证 |
| 密码重置 | `services/email/password_reset.py` | 密码重置 |
| 短信服务 | `services/sms/manager.py` | 短信服务 |
| Redis服务 | `services/redis_service.py` | Redis操作 |
| WebSocket | `services/websocket_service.py` | WebSocket |
| 增强WS | `services/enhanced_websocket.py` | 增强WebSocket |
| 任务调度 | `services/task_scheduler.py` | 任务调度 |
| 周期任务 | `services/periodic_task_service.py` | 周期任务 |
| 报告生成 | `services/report_generator.py` | 报告生成 |

### 5.9 其他服务

| 服务模块 | 路径 | 描述 |
|----------|------|------|
| SEO服务 | `services/seo.py` | SEO优化 |
| 站点地图 | `services/sitemap_cache.py` | 站点地图 |
| 权限服务 | `services/permissions.py` | 权限管理 |
| 配额服务 | `services/quota_service.py` | 用户配额 |
| 推荐API | `services/recommendation/api.py` | 推荐API |
| 冷启动 | `services/recommendation/cold_start.py` | 冷启动推荐 |
| 兴趣图谱 | `services/recommendation/interest_graph.py` | 兴趣图谱 |
| 搜索核心 | `services/search/core.py` | 搜索核心 |
| 搜索历史 | `services/search/history.py` | 搜索历史 |
| 搜索建议 | `services/search/suggestions.py` | 搜索建议 |
| 新闻订阅 | `services/news/subscriptions.py` | 新闻订阅 |
| 新闻评论 | `services/news/comments.py` | 新闻评论 |
| 内容审核 | `services/content_moderation.py` | 内容审核 |
| 内容安全 | `services/content_safety.py` | 内容安全 |
| 法律合规 | `services/enterprise_compliance.py` | 企业合规 |
| 数据安全 | `services/data_security.py` | 数据安全 |
| 入门引导 | `services/onboarding.py` | 新用户引导 |
| 推荐管理 | `services/referral_manager.py` | 推荐管理 |
| 律师工作台 | `services/lawyer_workbench.py` | 律师工作台 |
| 律师积分 | `services/lawyer_points_service.py` | 律师积分 |
| 律师模板 | `services/lawyer_reply_template_service.py` | 律师回复模板 |
| 律师推广 | `services/lawyer_promotion_link_service.py` | 律师推广 |
| 律师名片 | `services/lawyer_share_card_service.py` | 律师名片分享 |
| 行动卡片 | `services/action_cards.py` | 行动卡片 |
| 审核服务 | `services/audit_service.py` | 审核服务 |
| AI ASR | `services/sherpa_asr_service.py` | 语音识别 |
| 声音管理 | `services/voice_manager.py` | 声音配置 |
| 声音配置 | `services/voice_config_service.py` | 声音配置 |
| RSS采集 | `services/rss_ingest_service.py` | RSS订阅 |
| 新闻工作台 | `services/news_workbench_service.py` | 新闻工作台 |
| 免责声明 | `services/disclaimer.py` | 免责声明 |
| 国际化 | `services/i18n.py` | 国际化 |
| 性能列表 | `services/list_performance.py` | 列表性能 |
| 异步优化 | `services/async_optimizer.py` | 异步优化 |
| 接入集成 | `services/integration/module_integration.py` | 模块集成 |
| 推荐增强 | `services/recommendation/enhanced_recommendation.py` | 增强推荐 |
| 积分定时 | `services/points/scheduled_tasks.py` | 积分定时任务 |

---

## 6. 数据库模型清单

### 6.1 用户相关

| 模型 | 描述 |
|------|------|
| User | 用户基本信息 |
| UserProfile | 用户扩展信息 |
| UserSecurity | 用户安全信息（双因素认证） |
| UserConsent | 用户同意记录 |
| UserQuota | 用户配额 |
| UserBehaviorLog | 用户行为日志 |

### 6.2 律师与律所

| 模型 | 描述 |
|------|------|
| Lawfirm | 律所信息 |
| Lawyer | 律师信息 |
| LawyerSchedule | 律师日程 |
| LawyerHomepage | 律师主页 |
| LawyerReplyTemplate | 律师回复模板 |
| LawyerPromotionLink | 律师推广链接 |
| LawyerReview | 律师评价 |

### 6.3 咨询与对话

| 模型 | 描述 |
|------|------|
| Consultation | 咨询记录 |
| ConsultationMessage | 咨询消息 |
| ConsultationReview | 咨询评价 |
| AIChatSession | AI聊天会话 |
| AIChatMessage | AI聊天消息 |

### 6.4 社区与内容

| 模型 | 描述 |
|------|------|
| Forum | 论坛 |
| ForumPost | 论坛帖子 |
| ForumComment | 论坛评论 |
| ForumReaction | 论坛点赞 |
| ForumFavorite | 收藏 |
| News | 新闻资讯 |
| NewsComment | 新闻评论 |
| NewsSubscription | 新闻订阅 |
| NewsTopic | 新闻主题 |
| NewsWorkbench | 新闻工作台 |
| FAQ | 常见问题 |

### 6.5 合同与文档

| 模型 | 描述 |
|------|------|
| Contract | 合同 |
| ContractReviewHistory | 合同审查历史 |
| Document | 文档 |
| DocumentTemplate | 文档模板 |

### 6.6 支付与订单

| 模型 | 描述 |
|------|------|
| Order | 订单 |
| Payment | 支付记录 |
| PaymentCallback | 支付回调 |
| Refund | 退款记录 |
| Settlement | 结算记录 |
| SettlementWithdrawal | 提现记录 |
| SettlementIncome | 收入记录 |
| SettlementBankAccount | 银行账户 |

### 6.7 积分与会员

| 模型 | 描述 |
|------|------|
| PointsAccount | 积分账户 |
| PointsTransaction | 积分流水 |
| PointsProduct | 积分商品 |
| PointsOrder | 积分订单 |
| Membership | 会员信息 |
| MembershipPlan | 会员计划 |

### 6.8 通知与消息

| 模型 | 描述 |
|------|------|
| Notification | 通知消息 |
| Feedback | 用户反馈 |

### 6.9 法律知识

| 模型 | 描述 |
|------|------|
| KnowledgeBase | 知识库 |
| KnowledgeArticle | 知识文章 |
| KnowledgeCategory | 知识分类 |

### 6.10 系统与管理

| 模型 | 描述 |
|------|------|
| SystemConfig | 系统配置 |
| SystemSecret | 系统密钥 |
| ModerationRecord | 审核记录 |
| Channel | 渠道信息 |
| AIChatConfig | AI聊天配置 |
| AIModelConfig | AI模型配置 |
| Analytics | 分析数据 |
| PeriodicTask | 定时任务 |

---

## 7. 版本信息

- 文档版本: 1.0.0
- 创建日期: 2026-02-17
- 项目: 百姓助手