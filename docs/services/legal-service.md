# 法律服务 (Legal Service)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | legal-service |
| 端口 | 8008 |
| 基础路径 | /api/v1/legal |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis |
| 数据库 | legal_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |
| 存活检查 | GET /health/live |
| gRPC 端口 | 50052 |

## 服务描述

法律服务是平台核心业务服务，提供律师管理、法律咨询、预约排班、律所管理、文书模板、评价系统等完整法律业务链。支持律师认证、智能匹配、gRPC 跨服务调用等高级特性。

## API 端点

### 咨询路由 (consultation_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | / | 创建咨询 | 是 |
| GET | / | 获取咨询列表 | 是 |
| GET | /{consultation_id} | 获取咨询详情 | 是 |
| PATCH | /{consultation_id}/status | 更新咨询状态 | 是 |
| GET | /{consultation_id}/messages | 获取消息列表 | 是 |
| POST | /{consultation_id}/messages | 添加消息 | 是 |
| POST | /{consultation_id}/complete | 完成咨询 | 是 |
| POST | /{consultation_id}/cancel | 取消咨询 | 是 |
| POST | /{consultation_id}/assign | 分配律师 | 是 |
| GET | /pending | 获取待匹配咨询 | 是 |
| GET | /me/stats | 我的咨询统计 | 是 |

### 律师路由 (lawyer_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | / | 获取律师列表 | 否 |
| GET | /search | 搜索律师 | 否 |
| GET | /{lawyer_id} | 获取律师详情 | 否 |
| PATCH | /me/profile | 更新律师档案 | 是 |
| GET | /me/consultations | 我的咨询列表 | 是 |
| POST | /{lawyer_id}/verify | 认证律师 | 是 |
| GET | /me/pending | 我的待处理 | 是 |
| GET | /me/stats | 我的统计 | 是 |
| GET | /me/schedule | 我的排班 | 是 |
| GET | /recommended | 推荐律师 | 否 |
| GET | /matching/{consultation_id} | 匹配律师 | 是 |

### 律所路由 (firm_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | / | 申请入驻律所 | 是 |
| GET | / | 获取律所列表 | 否 |
| GET | /{firm_id} | 获取律所详情 | 否 |
| PATCH | /{firm_id} | 更新律所信息 | 是 |
| POST | /{firm_id}/verification | 提交资质审核 | 是 |
| GET | /{firm_id}/verification | 获取审核状态 | 是 |
| GET | /{firm_id}/lawyers | 获取律所律师 | 否 |
| POST | /{firm_id}/invitations | 邀请律师加入 | 是 |
| GET | /{firm_id}/invitations | 获取邀请列表 | 是 |
| DELETE | /{firm_id}/lawyers/{lawyer_id} | 移除律师 | 是 |

### 邀请路由 (invitation_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /{invitation_id}/accept | 接受邀请 | 是 |
| POST | /{invitation_id}/reject | 拒绝邀请 | 是 |
| GET | /me | 我的邀请列表 | 是 |

### 预约路由 (appointment_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | / | 创建预约 | 是 |
| GET | / | 获取预约列表 | 是 |
| GET | /{appointment_id} | 获取预约详情 | 是 |
| PATCH | /{appointment_id}/status | 更新预约状态 | 是 |
| POST | /{appointment_id}/cancel | 取消预约 | 是 |
| GET | /lawyer/{lawyer_id}/available-slots | 获取可用时段 | 否 |

### 排班路由 (schedule_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | / | 创建排班 | 是 |
| POST | /bulk | 批量创建排班 | 是 |
| GET | / | 获取排班列表 | 是 |
| GET | /date/{target_date} | 按日期获取排班 | 否 |
| PATCH | /{schedule_id}/availability | 更新排班可用性 | 是 |
| DELETE | /{schedule_id} | 删除排班 | 是 |
| DELETE | /date/{target_date} | 按日期删除排班 | 是 |

### 文书路由 (document_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | / | 创建文书 | 是 |
| GET | /{document_id} | 获取文书详情 | 是 |
| GET | /consultation/{consultation_id} | 获取咨询的文书 | 是 |
| PATCH | /{document_id} | 更新文书 | 是 |
| DELETE | /{document_id} | 删除文书 | 是 |
| GET | /templates/ | 获取文书模板 | 否 |

### 评价路由 (review_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | / | 创建评价 | 是 |
| GET | /consultation/{consultation_id} | 获取咨询评价 | 否 |
| GET | /lawyer/{lawyer_id} | 获取律师评价列表 | 否 |
| GET | /lawyer/{lawyer_id}/stats | 获取律师评价统计 | 否 |

### 管理路由 (admin_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /stats | 管理统计 | 是 |
| GET | /lawyers | 律师列表 | 是 |
| POST | /lawyers/{lawyer_id}/verify | 审核通过律师 | 是 |
| POST | /lawyers/{lawyer_id}/reject | 审核拒绝律师 | 是 |
| GET | /consultations | 咨询列表 | 是 |
| POST | /consultations/{consultation_id}/assign | 分配咨询 | 是 |
| GET | /lawyer-consultations | 律师咨询列表 | 是 |

### 律所管理路由 (firm_admin_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /firms | 律所列表 | 是 |
| GET | /firms/pending | 待审核律所 | 是 |
| GET | /firms/reviewing | 审核中律所 | 是 |
| POST | /firms/{firm_id}/approve | 审核通过 | 是 |
| POST | /firms/{firm_id}/reject | 审核拒绝 | 是 |
| GET | /firms/{firm_id}/stats | 律所统计 | 是 |
| GET | /firms/{firm_id}/lawyer-stats | 律师统计 | 是 |

### 缓存管理路由 (cache_admin_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /stats | 缓存统计 | 是 |
| POST | /lawyer/{lawyer_id}/invalidate | 清除律师缓存 | 是 |
| POST | /lawyer-list/invalidate | 清除律师列表缓存 | 是 |
| POST | /firm/{firm_id}/invalidate | 清除律所缓存 | 是 |
| POST | /flush | 清空所有缓存 | 是 |
| GET | /key/{key} | 获取缓存键值 | 是 |

### 指标路由 (metrics_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /metrics | Prometheus 指标 | 否 |
| GET | /metrics/counters | 计数器指标 | 否 |

## 数据模型

| 模型 | 说明 |
|------|------|
| Lawyer | 律师（姓名、专业、城市、评分、状态） |
| Consultation | 咨询（分类、标题、描述、状态、律师ID） |
| Appointment | 预约（律师ID、时间、类型、价格、状态） |
| Firm | 律所（名称、地址、执照号、认证状态） |
| Document | 文书（类型、标题、内容、AI生成标记） |
| Review | 评价（评分、内容、匿名标记） |
| Schedule | 排班（律师ID、日期、时段、可用性） |
| Invitation | 邀请（律所ID、律师ID、角色、状态） |
| OutboxEvent | Outbox 事件（用于可靠消息投递） |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| user-service | HTTP + gRPC | 获取用户信息、验证律师身份 |
| ai-service | HTTP | AI 辅助咨询、文书生成 |
| notification-service | Kafka | 咨询/预约/审核通知事件 |
| search-service | HTTP | 律师/律所搜索聚合 |
| backend-bff | HTTP | BFF 聚合法律接口 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| SERVICE_PORT | 8008 | 服务端口 |
| DATABASE_URL | - | PostgreSQL 连接串 |
| REDIS_URL | - | Redis 连接串 |
| KAFKA_BOOTSTRAP_SERVERS | kafka:9092 | Kafka 地址 |
| GRPC_PORT | 50052 | gRPC 端口 |

## 部署信息

- Dockerfile: services/legal-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
- 详细 API 文档: [services/legal-service/API.md](../../services/legal-service/API.md)
