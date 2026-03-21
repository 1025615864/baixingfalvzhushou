# 百姓助手 — 架构升级技术方案

需求名称：architecture-upgrade
更新日期：2026-03-21

## 1. 概述

### 1.1 项目背景

百姓助手当前为**单体FastAPI架构**，包含用户、AI咨询、律师服务、社区论坛、新闻资讯、支付结算等模块。目标用户量达百万级，需要向**领域驱动微服务集群**演进。

### 1.2 服务拆分策略

根据业务边界和独立运营需求，重新划分为**11个核心领域服务**：

| 序号 | 服务名称 | 英文标识 | 独立运营 | 数据敏感性 | 数据库分离 |
|-----|---------|----------|---------|-----------|-----------|
| 1 | 用户服务 | user-service | - | 高 | Citus分片 |
| 2 | 支付通道服务 | payment-channel-service | - | 极高 | Citus分片 |
| 3 | 账务服务 | payment-accounting-service | - | 极高 | Citus分片 |
| 4 | 法律服务 | legal-service | - | 中 | 独立库 |
| 5 | AI服务 | ai-service | - | 中 | 独立库 |
| 6 | 新闻服务 | news-service | 是 | 低 | 独立库+独立SSO |
| 7 | 社区服务 | community-service | 是 | 低 | 独立库+独立SSO |
| 8 | 积分服务 | points-service | - | 中 | Citus分片 |
| 9 | 通知服务 | notification-service | - | 低 | 独立库 |
| 10 | 推荐服务 | recommendation-service | - | 低 | 独立库 |
| 11 | 搜索服务 | search-service | - | 低 | 独立库 |

---

## 2. 目标架构总览

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              统一接入层 (API Gateway)                                 │
│                        Kong/APISIX · 限流 · 认证 · 路由 · 灰度                        │
└────────────────────────────────────┬────────────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   用户服务           │   │ 支付通道服务         │   │ 账务服务            │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │·用户注册/登录  │  │   │  │·支付宝通道    │  │   │  │·订单管理      │  │
│  │·JWT/TOTP认证  │  │   │  │·微信支付通道  │  │   │  │·余额管理      │  │
│  │·用户画像       │  │   │  │·IkunPay通道  │  │   │  │·对账风控      │  │
│  │·会员管理       │  │   │  │·回调处理     │  │   │  │·律师结算      │  │
│  │·用户安全       │  │   │  │·签名验签     │  │   │  └───────────────┘  │
│  │·用户额度       │  │   │  └───────────────┘  │   │        │             │
│  └───────────────┘  │   │        │             │   │  ┌─────▼─────┐      │
│        │             │   │  ┌─────▼─────┐      │   │  │  PostgreSQL│      │
│  ┌─────▼─────┐      │   │  │  PostgreSQL│      │   │  │  (Citus)   │      │
│  │  PostgreSQL│      │   │  │  (Citus)   │      │   │  └────────────┘      │
│  │  (Citus)   │      │   │  └────────────┘      │   └─────────────────────┘
│  └────────────┘      │   └─────────────────────┘
└─────────────────────┘   └─────────────────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   法律服务           │   │   AI服务             │   │   新闻服务            │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │·AI法律咨询    │  │   │  │·AI对话/咨询   │  │   │  │·新闻管理       │  │
│  │·律师/律所管理 │  │   │  │·法律助手Agent │  │   │  │·新闻专题       │  │
│  │·咨询预约      │  │   │  │·RAG知识检索   │  │   │  │·订阅管理       │  │
│  │·合同审查      │  │   │  │·模型路由/熔断 │  │   │  │·独立SSO       │  │
│  │·法律知识库    │  │   │  │·会话管理      │  │   │  │·采编工作流     │  │
│  │·法律文书      │  │   │  └───────────────┘  │   │  └───────────────┘  │
│  └───────────────┘  │   │        │             │   │        │             │
│        │             │   │  ┌─────▼─────┐      │   │  ┌─────▼─────┐      │
│  ┌─────▼─────┐      │   │  │  PostgreSQL│      │   │  │  PostgreSQL│      │
│  │  PostgreSQL│      │   │  │ + ChromaDB│      │   │  │ + News SSO │      │
│  │  (独立库)   │      │   │  └────────────┘      │   │  └────────────┘      │
│  └────────────┘      │   └─────────────────────┘   └───────────────────────┘
└─────────────────────┘                                                   │
         │                                                                 │
         ┌───────────────────────────┼───────────────────────────┐         │
         │                           │                           │         │
         ▼                           ▼                           ▼         │
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐│
│   社区服务           │   │   积分服务           │   │   通知服务            ││
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  ││
│  │·论坛帖子       │  │   │  │·积分管理       │  │   │  │·站内通知       │  ││
│  │·评论互动       │  │   │  │·积分兑换       │  │   │  │·邮件通知       │  ││
│  │·收藏/点赞      │  │   │  │·会员等级       │  │   │  │·短信通知       │  ││
│  │·版主管理       │  │   │  └───────────────┘  │   │  └───────────────┘  ││
│  │·独立SSO       │  │   │        │             │   │        │             ││
│  └───────────────┘  │   │  ┌─────▼─────┐      │   │  ┌─────▼─────┐      ││
│        │             │   │  │  PostgreSQL│      │   │  │  PostgreSQL│      ││
│  ┌─────▼─────┐      │   │  │  (Citus)   │      │   │  └────────────┘      ││
│  │  PostgreSQL│      │   │  └────────────┘      │   └─────────────────────┘│
│  │ + Forum SSO │      │   └─────────────────────┘                           │
│  └────────────┘      │                                                     │
└─────────────────────┘                                                     │
                                                                             │
         ┌───────────────────────────────────────────────────────────────────┤
         │                                                                   │
         ▼                                                                   ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐│
│   推荐服务           │   │   搜索服务           │   │   Kafka             │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │   事件总线          │
│  │·律师推荐      │  │   │  │·全局搜索      │  │   │                    │
│  │·新闻推荐      │  │   │  │·搜索建议      │  │   │                    │
│  │·帖子推荐      │  │   │  └───────────────┘  │   │                    │
│  └───────────────┘  │   │        │             │   │                    │
│        │             │   │  ┌─────▼─────┐      │   │                    │
│  ┌─────▼─────┐      │   │  │  PostgreSQL│      │   │                    │
│  │  PostgreSQL│      │   │  └────────────┘      │   │                    │
│  └────────────┘      │   └─────────────────────┘   └─────────────────────┘│
└─────────────────────┘
```

---

## 3. 服务详细设计

### 3.1 用户服务 (user-service)

**职责边界**：用户身份、认证授权、安全合规

| 模块 | 功能 | 数据模型 |
|-----|------|---------|
| 账号管理 | 注册、登录、手机号/邮箱 | User, UserConsent |
| 认证授权 | JWT RS256/HS256、TOTP 2FA | UserSecuritySettings |
| 用户画像 | 兴趣标签、行为数据 | UserProfile, UserInterestHistory |
| 会员体系 | 会员等级、权益管理 | Membership |
| 额度管理 | 每日额度、配额控制 | UserQuotaDaily, UserQuotaPackBalance |
| 安全审计 | 设备管理、登录日志 | UserDevice, LoginAudit |

**API接口**：
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/2fa/verify
GET    /api/v1/users/me
PATCH  /api/v1/users/me
GET    /api/v1/users/me/profile
PUT    /api/v1/users/me/security
GET    /api/v1/membership/current
```

**数据分片策略**：Citus按user_id哈希分片

**技术要点**：
- 密码BCrypt加密 + 盐值
- 登录失败计数（Redis，5次后锁定30分钟）
- 设备指纹识别（新设备异地登录告警）
- JWT短期令牌（15min）+ Refresh令牌（7天）

---

### 3.2 支付服务 (payment-service)

**职责边界**：支付交易、资金安全、合规对账

> **二次拆分设计**：将支付服务拆分为**支付通道层**和**账务层**，实现关注点分离

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Payment Service                                  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    支付通道层 (Payment Channel)                    │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │ │
│  │  │  支付宝   │  │  微信支付 │  │ IkunPay  │  │ (可扩展) │       │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘       │ │
│  │       │             │             │                             │ │
│  │  ┌────▼─────────────▼─────────────▼─────┐                      │ │
│  │  │          通道适配器 (Adapter)          │                      │ │
│  │  │   统一抽象 · 签名验签 · 回调处理        │                      │ │
│  │  └────────────────────┬──────────────────┘                      │ │
│  └───────────────────────┼─────────────────────────────────────────┘ │
│                          │                                           │
│  ┌───────────────────────▼─────────────────────────────────────────┐ │
│  │                    账务层 (Accounting)                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │ │
│  │  │  订单管理    │  │  余额管理    │  │  结算管理    │            │ │
│  │  │  ·创建订单   │  │  ·用户余额   │  │  ·律师结算  │            │ │
│  │  │  ·状态流转   │  │  ·钱包管理   │  │  ·对账风控  │            │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │ │
│  │                                                                   │ │
│  │  ┌────────────────────────────────────────────────────────────┐ │ │
│  │  │                    财务引擎 (Finance Engine)                │ │ │
│  │  │   借贷记账 · 事务一致性 · 幂等控制 · 异常恢复               │ │ │
│  │  └────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

| 模块 | 功能 | 数据模型 |
|-----|------|---------|
| **通道适配器** | 统一支付接口、签名验签、回调处理 | - |
| **通道配置** | 支付宝/微信/ IkunPay 通道管理 | PaymentConfig |
| **订单管理** | 订单创建、状态流转、幂等控制 | PaymentOrder |
| **余额管理** | 用户余额、律师钱包、资金变动流水 | UserBalance, LawyerWallet, BalanceTransaction |
| **退款服务** | 退款申请、审核、退款处理 | PaymentRefund |
| **银行卡** | 银行卡绑定、解绑、实名验证 | BankCard |
| **律师结算** | 收入记录、提现申请、结算周期 | LawyerIncomeRecord, WithdrawalRequest |
| **对账风控** | 每日对账、差异检测、异常告警 | ReconciliationRecord |

**API接口**：
```
# 支付通道层
POST   /api/v1/payment/channels/alipay/pay
POST   /api/v1/payment/channels/wechat/pay
POST   /api/v1/payment/channels/ikunpay/pay
POST   /api/v1/payment/callbacks/{channel}
GET    /api/v1/payment/channels/config

# 账务层
POST   /api/v1/payment/orders
POST   /api/v1/payment/orders/{id}/pay
GET    /api/v1/payment/orders
GET    /api/v1/payment/orders/{id}
POST   /api/v1/payment/refunds
GET    /api/v1/payment/refunds/{id}
GET    /api/v1/balance
GET    /api/v1/balance/history
GET    /api/v1/settlement/wallet
POST   /api/v1/settlement/withdraw
GET    /api/v1/settlement/records
GET    /api/v1/settlement/reconciliation
```

**数据分片策略**：Citus按user_id或lawyer_id哈希分片

**技术要点**：
- **通道解耦**：新增支付通道只需实现适配器，不影响账务逻辑
- **幂等设计**：分布式锁 + 幂等键，同一订单不会重复扣款
- **回调验签**：RSA-2048签名验证，防止伪造回调
- **金额校验**：精确到分，阈值告警（如单笔>10000元）
- **T+1对账**：每日核对本地订单 vs 渠道流水，差异自动告警
- **事件驱动**：支付成功 → 账务层更新余额 → 发布余额变动事件

---

### 3.3 法律服务 (legal-service)

**职责边界**：法律咨询、律师服务、律所支撑、文书合同

| 模块 | 功能 | 数据模型 |
|-----|------|---------|
| AI咨询 | 文字咨询、律师转接 | Consultation, ChatMessage |
| 律师管理 | 律师入驻、认证、主页 | Lawyer, LawyerVerification |
| 律所管理 | 律所入驻、团队管理 | LawFirm |
| 咨询预约 | 图文咨询、视频咨询 | LawyerConsultation, VideoConsultation |
| 律师评价 | 评分、标签、案例展示 | LawyerReview |
| 合同审查 | 合同上传、AI审查 | ContractReviewHistory |
| 法律文书 | 文书模板、文书生成 | LegalDocument, DocumentTemplate |
| 知识库 | 法律知识库维护 | LegalKnowledge |

**API接口**：
```
# AI咨询
POST   /api/v1/legal/consultations
GET    /api/v1/legal/consultations/{id}
POST   /api/v1/legal/consultations/{id}/messages

# 律师/律所
GET    /api/v1/legal/lawyers
GET    /api/v1/legal/lawyers/{id}
POST   /api/v1/legal/lawyers/verify
GET    /api/v1/legal/firms
GET    /api/v1/legal/firms/{id}

# 预约
POST   /api/v1/legal/appointments
GET    /api/v1/legal/appointments
POST   /api/v1/legal/video/booking

# 合同/文书
POST   /api/v1/legal/contracts/review
GET    /api/v1/legal/documents/templates
POST   /api/v1/legal/documents/generate

# 知识库
GET    /api/v1/legal/knowledge
GET    /api/v1/legal/knowledge/{id}
```

**技术要点**：
- AI咨询调用AI服务，保留完整会话历史
- 律师认证多级审核（材料提交 → 资质审核 → 实名认证）
- 视频咨询使用外部SDK（腾讯云/声网）
- 合同审查结果需律师二次确认

---

### 3.4 AI服务 (ai-service)

**职责边界**：AI能力中台、法律助手Agent、模型管理

> **核心设计原则**：法律助手Agent必须独立、可迭代、可维护，与外部AI API解耦

| 模块 | 功能 | 数据模型 |
|-----|------|---------|
| 对话引擎 | 多轮对话、会话管理 | AISession, ChatMessage |
| 法律助手Agent | 专用法律咨询Agent | AgentConfig, AgentSession |
| RAG知识检索 | 向量检索、混合检索、重排序 | LegalKnowledge |
| 模型路由 | 多模型调度、熔断降级 | ModelConfig |
| Prompt管理 | Prompt模板版本管理 | PromptTemplate |
| 质量监控 | 响应质量评估、幻觉检测 | AIQualityMetrics |
| 缓存优化 | 结果缓存、防重复调用 | - |

**Agent架构**：
```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Service                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Agent Framework                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │   Router    │  │   Agent     │  │   Monitor       │   │  │
│  │  │  (意图识别) │  │ (法律助手)  │  │  (质量监控)     │   │  │
│  │  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘   │  │
│  │         │                  │                   │            │  │
│  │  ┌──────▼────────────────▼───────────────────▼────────┐   │  │
│  │  │              RAG Pipeline                          │   │  │
│  │  │  Query → 改写 → 混合检索 → 重排序 → Context        │   │  │
│  │  └─────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                   │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐         │
│  │  OpenAI    │    │  DeepSeek  │    │  本地模型   │         │
│  │  GPT-4o    │    │  (备选)    │    │  (离线/敏感)│         │
│  └────────────┘    └────────────┘    └────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

**API接口**：
```
POST   /api/v1/ai/chat
POST   /api/v1/ai/consultation
GET    /api/v1/ai/sessions
GET    /api/v1/ai/sessions/{id}
POST   /api/v1/ai/sessions/{id}/feedback
GET    /api/v1/ai/knowledge/search
POST   /api/v1/ai/admin/config
GET    /api/v1/ai/admin/prompts
PUT    /api/v1/ai/admin/prompts/{id}
GET    /api/v1/ai/admin/metrics
```

**技术要点**：
- **Agent独立性**：法律助手Agent有独立配置、版本控制、AB测试能力
- **RAG优化**：查询改写、混合检索（向量+BM25）、重排序、幻觉检测
- **熔断降级**：连续失败触发熔断，自动切换备选模型
- **结果缓存**：相同问题24小时缓存，减少API调用
- **质量回溯**：记录完整对话，支持人工复核

---

### 3.5 新闻服务 (news-service)

**职责边界**：新闻资讯、**独立运营**、内容严谨

> **独立运营体系**：新闻服务拥有独立的SSO、管理员体系和运营权限

```
┌─────────────────────────────────────────────────────────────────────┐
│                      News Service 独立运营体系                        │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     独立 SSO (News SSO)                         │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │ │
│  │  │ 采编账号  │  │ 编辑账号  │  │ 审核账号  │                     │ │
│  │  └──────────┘  └──────────┘  └──────────┘                     │ │
│  │        │              │             │                          │ │
│  │  ┌─────▼──────────────▼──────────────▼─────┐                   │ │
│  │  │         统一身份认证 (News Identity)      │                   │ │
│  │  │   独立于主系统 · 权限隔离 · 操作审计      │                   │ │
│  │  └────────────────────────────────────────┘                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     新闻管理员体系                                 │ │
│  │                                                                   │ │
│  │   角色层级: 超级编辑 → 编辑 → 采编 → 实习生                       │ │
│  │                                                                   │ │
│  │   权限划分:                                                       │ │
│  │   · 发布权限: 超级编辑、编辑                                      │ │
│  │   · 审核权限: 超级编辑、编辑                                      │ │
│  │   · 采编权限: 采编、编辑、超级编辑                                │ │
│  │   · 管理权限: 超级编辑                                            │ │
│  │                                                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

| 模块 | 功能 | 数据模型 |
|-----|------|---------|
| 新闻管理 | 新闻CRUD、上下架、置顶 | News |
| 新闻专题 | 专题策划、内容聚合 | NewsTopic, NewsTopicItem |
| 新闻订阅 | 分类订阅、推送管理 | NewsSubscription |
| 新闻评论 | 评论管理、敏感词过滤 | NewsComment |
| AI辅助 | AI摘要生成、AI标注 | NewsAIAnnotation |
| 质量控制 | 新闻工作台、版本管理 | NewsVersion, NewsAIGeneration |
| **采编工作流** | 采编 → 编辑 → 审核 → 发布 | NewsWorkflow |
| **独立SSO** | 采编账号、编辑账号、审核账号 | NewsUser, NewsRole |
| **运营统计** | 阅读量、分享量、收藏量 | NewsAnalytics |

**API接口**：
```
# C端接口
GET    /api/v1/news
GET    /api/v1/news/{id}
GET    /api/v1/news/topics
GET    /api/v1/news/topics/{id}
POST   /api/v1/news/subscriptions
DELETE /api/v1/news/subscriptions/{id}
GET    /api/v1/news/{id}/comments
POST   /api/v1/news/{id}/comments

# 运营后台接口 (独立SSO)
POST   /api/v1/news (role: editor+)
PUT    /api/v1/news/{id} (role: editor+)
DELETE /api/v1/news/{id} (role: admin)
POST   /api/v1/news/{id}/publish (role: editor+)
POST   /api/v1/news/{id}/recall (role: editor+)
GET    /api/v1/news/stats (role: editor+)

# 采编接口
GET    /api/v1/news/drafts (role: reporter+)
POST   /api/v1/news/drafts (role: reporter+)
PUT    /api/v1/news/drafts/{id} (role: reporter+)
POST   /api/v1/news/drafts/{id}/submit (role: reporter+)
GET    /api/v1/news/review (role: editor+)
POST   /api/v1/news/review/{id}/approve (role: editor+)
POST   /api/v1/news/review/{id}/reject (role: editor+)
```

**技术要点**：
- 内容审核：**发布前AI预审 + 编辑审核 + 敏感词过滤**
- 版本管理：所有修改留痕，支持**版本对比和回滚**
- 独立运营：**独立SSO体系**，与主系统用户隔离
- 权限分层：采编 → 编辑 → 审核 → 发布，四级权限
- 运营统计：独立的数据分析面板

---

### 3.6 社区服务 (community-service)

**职责边界**：法律论坛、**独立运营**、内容合规

> **独立运营体系**：社区服务拥有独立的SSO、版主体系和运营权限

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Community Service 独立运营体系                      │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    独立 SSO (Forum SSO)                         │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │ │
│  │  │  版主账号  │  │  律师账号  │  │  普通账号  │                     │ │
│  │  └──────────┘  └──────────┘  └──────────┘                     │ │
│  │        │              │             │                          │ │
│  │  ┌─────▼──────────────▼──────────────▼─────┐                   │ │
│  │  │        统一身份认证 (Forum Identity)       │                   │ │
│  │  │   独立于主系统 · 版主权限 · 操作审计        │                   │ │
│  │  └────────────────────────────────────────┘                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     版主管理体系                                  │ │
│  │                                                                   │ │
│  │   角色层级: 超级版主 → 版主 → 实习版主                            │ │
│  │                                                                   │ │
│  │   版主权限:                                                       │ │
│  │   · 内容管理: 删帖、删评、隐藏、置顶、精华                        │ │
│  │   · 用户管理: 禁言、解禁、警告                                    │ │
│  │   · 专题管理: 创建专题、推荐内容                                  │ │
│  │   · 数据查看: 帖子统计、用户统计                                   │ │
│  │                                                                   │ │
│  │   律师特权:                                                       │ │
│  │   · 实名认证标识 · 专业领域标签 · 优先推荐                        │ │
│  │                                                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

| 模块 | 功能 | 数据模型 |
|-----|------|---------|
| 论坛帖子 | 发帖、删改、敏感词过滤 | Post |
| 评论互动 | 评论、回复、@提及 | Comment |
| 收藏点赞 | 收藏、点赞、表情反应 | PostFavorite, PostReaction |
| 律师入驻 | 律师认证、邀请码、专业标签 | ForumLawyerInvitation |
| 内容审核 | AI预审、人工复核、申诉 | ModerationTask |
| 版主管理 | 禁言、删帖、精华推荐 | ForumModerator, ModerationLog |
| **独立SSO** | 版主账号、律师账号 | ForumUser, ForumRole |
| **运营统计** | 帖子统计、用户活跃、违规统计 | ForumAnalytics |

**API接口**：
```
# C端接口
GET    /api/v1/community/posts
POST   /api/v1/community/posts
GET    /api/v1/community/posts/{id}
PUT    /api/v1/community/posts/{id}
DELETE /api/v1/community/posts/{id}
GET    /api/v1/community/posts/{id}/comments
POST   /api/v1/community/posts/{id}/comments
POST   /api/v1/community/posts/{id}/favorite
POST   /api/v1/community/posts/{id}/react
GET    /api/v1/community/users/{id}/posts

# 律师接口
GET    /api/v1/community/lawyers/invitations
POST   /api/v1/community/lawyers/verify
GET    /api/v1/community/lawyers/profile

# 版主后台接口 (独立SSO)
GET    /api/v1/community/moderation/tasks (role: moderator+)
POST   /api/v1/community/moderation/posts/{id}/delete (role: moderator+)
POST   /api/v1/community/moderation/posts/{id}/hide (role: moderator+)
POST   /api/v1/community/moderation/posts/{id}/pin (role: moderator+)
POST   /api/v1/community/moderation/posts/{id}/essence (role: moderator+)
POST   /api/v1/community/moderation/users/{id}/ban (role: moderator+)
POST   /api/v1/community/moderation/users/{id}/unban (role: moderator+)
POST   /api/v1/community/moderation/appeals/{id} (role: moderator+)
GET    /api/v1/community/stats (role: moderator+)

# 专题管理 (role: admin)
GET    /api/v1/community/sections
POST   /api/v1/community/sections
PUT    /api/v1/community/sections/{id}
```

**技术要点**：
- 内容合规：**发帖AI预审 + 关键词过滤 + 人工抽检**
- 敏感操作：删除需记录原因，支持**用户申诉**
- 独立运营：**独立SSO体系**，与主系统用户隔离
- 权限分层：超级版主 → 版主 → 实习版主，三级权限
- 律师特权：实名认证、专业标签、优先推荐

---

### 3.7 积分服务 (points-service)

**职责边界**：用户激励、积分体系、兑换商城

| 模块 | 功能 | 数据模型 |
|-----|------|---------|
| 积分管理 | 积分增减、流水查询 | PointsUser, PointsHistory |
| 积分规则 | 积分任务、积分策略 | PointsDailyCount |
| 积分商城 | 商品兑换、订单管理 | PointsProduct, PointsExchangeOrder |
| 会员等级 | 等级计算、权益管理 | Membership |

**API接口**：
```
GET    /api/v1/points/balance
GET    /api/v1/points/history
POST   /api/v1/points/exchange
GET    /api/v1/points/products
GET    /api/v1/points/orders
```

**技术要点**：
- 原子操作：Redis + DB双写，保证并发安全
- 幂等设计：Lua脚本扣减，防止超扣
- 事件驱动：支付成功 → 积分增加（Kafka消费）

---

### 3.8 通知服务 (notification-service)

**职责边界**：消息推送、通知触达

| 模块 | 功能 | 数据模型 |
|-----|------|---------|
| 站内通知 | 消息通知、系统通知 | Notification |
| 邮件通知 | 邮件模板、发送队列 | - |
| 短信通知 | 短信模板、发送控制 | - |
| 推送配置 | 免打扰时段、渠道偏好 | - |

**API接口**：
```
GET    /api/v1/notifications
PUT    /api/v1/notifications/{id}/read
POST   /api/v1/notifications/settings
```

**技术要点**：
- 消息聚合：同类型消息合并推送
- 异步发送：Kafka队列削峰
- 发送限制：单用户日发送上限

---

### 3.9 推荐服务 (recommendation-service)

**职责边界**：个性化推荐、精准触达

| 模块 | 功能 |
|-----|------|
| 律师推荐 | 基于用户画像、律师专业度、评分 |
| 新闻推荐 | 基于用户兴趣、热点、时效性 |
| 帖子推荐 | 基于用户兴趣、互动率 |
| 首页推荐 | 综合推荐、个性化排序 |

**技术要点**：
- 特征工程：用户特征 + 物品特征 + 上下文特征
- 实时更新：用户行为实时反馈
- A/B测试：推荐算法在线实验

---

### 3.10 搜索服务 (search-service)

**职责边界**：全局搜索、结果聚合

| 模块 | 功能 |
|-----|------|
| 全局搜索 | 用户、律师、帖子、新闻、法律知识 |
| 搜索建议 | 热门搜索、联想词 |
| 搜索排序 | 相关性、时效性、权威性 |

**技术要点**：
- 全文检索：PostgreSQL全文搜索 + 向量检索
- 结果聚合：多源结果合并、去重
- 性能优化：搜索结果缓存

---

## 4. 数据架构

### 4.1 Citus分片策略

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Citus Coordinator Node                       │
│                                                                       │
│  用户服务分片 ───────────────────→ Shard 1, 2, 3 (by user_id)        │
│  支付服务分片 ───────────────────→ Shard 4, 5, 6 (by user_id)       │
│  积分服务分片 ───────────────────→ Shard 7, 8, 9 (by user_id)        │
│                                                                       │
│  独立服务 ─────────────────────────────────→ 独立PostgreSQL实例      │
│  (法律/AI/新闻/社区/通知/推荐/搜索)                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 服务间数据隔离

| 服务 | 数据库 | 分片方式 | 敏感级别 |
|-----|-------|---------|---------|
| user-service | postgres-user | Citus (user_id) | 极高 |
| payment-channel | postgres-payment-channel | Citus (order_id) | 极高 |
| payment-accounting | postgres-payment-accounting | Citus (user_id) | 极高 |
| legal-service | postgres-legal | 独立实例 | 高 |
| ai-service | postgres-ai + chromadb | 独立实例 | 中 |
| news-service | postgres-news + news-sso | 独立实例 + 独立SSO | 低 |
| community-service | postgres-forum + forum-sso | 独立实例 + 独立SSO | 低 |
| points-service | postgres-points | Citus (user_id) | 中 |
| notification-service | postgres-notification | 独立实例 | 低 |
| recommendation-service | postgres-recommendation | 独立实例 | 低 |
| search-service | postgres-search | 独立实例 | 低 |

### 4.3 独立SSO数据库设计

```
┌─────────────────────────────────────────────────────────────────────┐
│                      独立SSO数据库架构                                 │
│                                                                       │
│  ┌──────────────────────┐    ┌──────────────────────┐               │
│  │    News SSO DB       │    │   Forum SSO DB      │               │
│  │  ┌────────────────┐  │    │  ┌────────────────┐  │               │
│  │  │  NewsUser      │  │    │  │  ForumUser     │  │               │
│  │  │  NewsRole      │  │    │  │  ForumRole     │  │               │
│  │  │  NewsPermission│  │    │  │  ForumPermission│ │               │
│  │  │  NewsAuditLog  │  │    │  │  ForumAuditLog │  │               │
│  │  └────────────────┘  │    │  └────────────────┘  │               │
│  └──────────────────────┘    └──────────────────────┘               │
│                                                                       │
│  与主系统用户隔离，仅供运营人员使用                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.4 支付服务数据隔离

```
┌─────────────────────────────────────────────────────────────────────┐
│                      支付服务数据隔离                                  │
│                                                                       │
│  ┌────────────────────────┐    ┌────────────────────────┐           │
│  │   Payment Channel DB   │    │  Payment Accounting DB│           │
│  │  ┌──────────────────┐  │    │  ┌──────────────────┐  │           │
│  │  │  PaymentOrder    │  │    │  │  UserBalance     │  │           │
│  │  │  ChannelConfig   │  │    │  │  LawyerWallet    │  │           │
│  │  │  ChannelCallback  │  │    │  │  BalanceTx       │  │           │
│  │  │  RefundRequest    │  │    │  │  Settlement      │  │           │
│  │  └──────────────────┘  │    │  └──────────────────┘  │           │
│  └────────────────────────┘    └────────────────────────┘           │
│                                                                       │
│  通道库: 专注交易流程                                                  │
│  账务库: 专注资金变动、余额、对账                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. 消息队列架构 (Kafka)

### 5.1 主题设计

```
Topic: domain.user.*
├── domain.user.registered          # 用户注册
├── domain.user.login              # 用户登录
└── domain.user.profile_updated     # 用户信息更新

Topic: domain.payment.*
├── domain.payment.completed       # 支付完成
├── domain.payment.refunded        # 退款完成
└── domain.payment.settled         # 结算完成

Topic: domain.legal.*
├── domain.legal.consultation.created   # 咨询创建
├── domain.legal.consultation.completed # 咨询完成
├── domain.legal.lawyer.verified       # 律师认证通过
└── domain.legal.contract.reviewed     # 合同审查完成

Topic: domain.points.*
├── domain.points.changed          # 积分变动
└── domain.points.expired         # 积分过期

Topic: domain.notification.*
├── domain.notification.push      # 推送通知
└── domain.notification.email     # 邮件通知
```

### 5.2 事件流设计

```
【支付成功事件流】
Payment Completed
      │
      ├──→ [Order Service] 更新订单状态
      ├──→ [Points Service] 增加积分 (1元=1积分)
      ├──→ [Notification Service] 发送通知
      └──→ [Recommendation Service] 更新用户画像

【律师认证通过事件流】
Lawyer Verified
      │
      ├──→ [Search Service] 更新搜索索引
      ├──→ [Notification Service] 通知律师
      ├──→ [Legal Service] 生成律师主页
      └──→ [Recommendation Service] 更新推荐权重

【AI咨询完成事件流】
Consultation Completed
      │
      ├──→ [Points Service] 扣减积分/次数
      ├──→ [AI Service] 记录对话质量
      └──→ [Legal Service] 更新咨询统计
```

---

## 6. API Gateway设计

### 6.1 路由配置

```yaml
# Kong/APISIX 配置示例
services:
  - name: user-service
    url: http://user-service:8000
    routes:
      - name: user-auth route
        paths: ["/api/v1/auth"]
      - name: user route
        paths: ["/api/v1/users"]

  - name: payment-service
    url: http://payment-service:8000
    routes:
      - name: payment route
        paths: ["/api/v1/payment", "/api/v1/balance", "/api/v1/settlement"]

  - name: legal-service
    url: http://legal-service:8000
    routes:
      - name: legal route
        paths: ["/api/v1/legal"]

  - name: ai-service
    url: http://ai-service:8000
    routes:
      - name: ai route
        paths: ["/api/v1/ai"]
```

### 6.2 全局限流

| 限流维度 | 阈值 | 说明 |
|---------|------|------|
| 全局 | 10000 req/s | 保护整体系统 |
| IP限流 | 100 req/min | 防爬虫/刷接口 |
| 用户限流 | 60 req/min | 正常用户使用 |
| AI接口 | 10 req/min | 成本控制 |

---

## 7. 安全架构

### 7.1 敏感数据保护

```
┌─────────────────────────────────────────────────────────────────────┐
│                         安全防护层次                                 │
├─────────────────────────────────────────────────────────────────────┤
│  传输层: TLS 1.3 + HSTS                                              │
│  认证层: JWT RS256 + TOTP 2FA                                        │
│  授权层: RBAC + 资源级权限                                           │
│  加密层: 敏感字段 AES-256 加密 (身份证、银行卡号)                      │
│  审计层: 操作日志全记录 + 异常行为检测                                 │
│  防护层: WAF + DDoS防护                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 支付安全

- 回调验签：RSA-2048签名
- 幂等锁：Redis分布式锁
- 金额校验：精确到分，阈值报警
- 对账：每日T+1对账，差异告警

### 7.3 用户信息安全

- 密码：BCrypt + 随机盐
- 身份证：加密存储，脱敏展示
- 手机号：掩码展示
- 登录日志：完整记录，支持溯源

---

## 8. AI Agent架构（法律助手）

### 8.1 Agent设计原则

```
1. 独立性: Agent逻辑与外部API解耦，可独立测试和部署
2. 可迭代: 支持Prompt版本管理，AB测试，灰度发布
3. 可观测: 完整日志记录，质量指标监控，异常告警
4. 可维护: 配置驱动，规则引擎，易于调整
```

### 8.2 Agent核心组件

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Legal Agent Framework                           │
│                                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │   Intent    │───→│   Action    │───→│   Response  │              │
│  │   Router    │    │   Engine    │    │   Generator │              │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
│         │                  │                  │                       │
│         ▼                  ▼                  ▼                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │   Context   │    │   Rules     │    │   RAG       │              │
│  │   Manager   │    │   Engine    │    │   Pipeline  │              │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Config Center                             │    │
│  │  Prompt版本 | 规则配置 | 阈值参数 | AB分组                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 Agent版本管理

```python
class AgentVersion:
    version: str          # v1.0.0
    prompt_template: str # Prompt模板
    rules: list          # 规则配置
    rag_config: dict     # RAG配置
    enabled: bool        # 是否启用
    ab_group: str        # AB分组

# 运行时动态加载
agent_config = await config_center.get("legal_agent", version="latest")
```

### 8.4 质量保障

| 环节 | 措施 |
|-----|------|
| 输入校验 | 问题分类，敏感词过滤 |
| RAG质量 | 检索结果相关性过滤，置信度阈值 |
| 输出审核 | 幻觉检测，法律条文引用校验 |
| 事后复核 | 高风险咨询人工抽检 |
| 反馈闭环 | 用户评价 → 模型优化 |

---

## 9. 实施计划

### Phase 1：稳固地基（1-2月）

| 任务 | 服务 | 优先级 |
|-----|------|-------|
| 数据库连接池优化 | 所有服务 | P0 |
| Redis多级缓存 | 法律/新闻/社区 | P0 |
| API限流中间件 | API Gateway | P0 |
| JWT Token刷新机制 | 用户服务 | P0 |
| 支付通道幂等处理 | 支付通道服务 | P0 |
| 账务余额原子操作 | 账务服务 | P0 |
| 敏感数据加密存储 | 用户/支付 | P1 |
| CI/CD完善 | 所有服务 | P1 |
| 熔断降级框架 | AI服务 | P1 |

### Phase 2：服务拆分（2-3月）

| 任务 | 服务 | 依赖 |
|-----|------|-----|
| 用户服务拆分 | user-service | Phase 1完成 |
| 支付通道服务拆分 | payment-channel-service | Phase 1完成 |
| 账务服务拆分 | payment-accounting-service | Phase 1完成 |
| 法律服务拆分 | legal-service | Phase 1完成 |
| AI服务拆分 | ai-service | Phase 1完成 |
| Kafka消息队列引入 | 所有服务 | 服务拆分 |
| 分布式事务方案 | 支付+积分 | Kafka |
| K8s HPA弹性伸缩 | 所有服务 | 服务拆分 |

### Phase 3：深度优化（2-3月）

| 任务 | 服务 | 说明 |
|-----|------|-----|
| Citus分库分表 | 用户/支付/积分 | 数据层 |
| 新闻服务独立SSO | news-service | 独立身份体系 |
| 社区服务独立SSO | community-service | 独立身份体系 |
| 新闻服务独立运营后台 | news-service | 采编/编辑/审核工作流 |
| 社区服务版主体系 | community-service | 版主权限体系 |
| AI Agent精细化 | ai-service | 法律助手优化 |
| 多可用区部署 | 所有服务 | 容灾 |
| 全链路追踪 | 所有服务 | OpenTelemetry |

---

## 10. 技术选型汇总

| 类别 | 技术选型 | 说明 |
|-----|---------|-----|
| API网关 | Kong / APISIX | 限流、认证、路由 |
| 微服务框架 | FastAPI (各服务独立) | 异步、高性能 |
| 数据库 | PostgreSQL + Citus | 分片支持 |
| 消息队列 | Kafka | 高吞吐 |
| 缓存 | Redis Cluster | 多级缓存 |
| 向量数据库 | ChromaDB | AI服务 |
| 容器编排 | Kubernetes (Helm) | 弹性伸缩 |
| CI/CD | GitHub Actions | 自动化 |
| 可观测性 | Prometheus + Grafana + Jaeger | 全链路 |
| 支付通道 | 支付宝 / 微信支付 / IkunPay | 第三方支付 |
| 独立SSO | 自建 | 新闻/社区独立身份体系 |
