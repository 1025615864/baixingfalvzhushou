# 通知服务

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | notification-service |
| 端口 | 8011 |
| 基础路径 | /api/v1/notifications |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis |
| 数据库 | notification_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |

## 服务描述

通知服务负责管理平台内所有消息通知的创建、推送和管理。支持多渠道通知（邮件、短信、推送），提供用户通知偏好设置，并通过 Kafka 消费其他服务的事件消息自动触发通知。

## API 端点

### 通知管理 (notification.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /notifications | 获取用户通知列表（支持未读筛选、分页） | 否 |
| GET | /notifications/{notification_id} | 获取通知详情 | 否 |
| POST | /notifications | 创建通知 | 否 |
| PUT | /notifications/{notification_id}/read | 标记通知已读 | 否 |
| PUT | /notifications/read-all | 标记用户所有通知已读 | 否 |
| DELETE | /notifications/{notification_id} | 删除通知 | 否 |

## 数据模型

### Notification

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID（索引） |
| type | String(50) | 通知类型 |
| title | String(200) | 通知标题 |
| content | Text | 通知内容 |
| is_read | Boolean | 是否已读 |
| sent_at | DateTime | 发送时间 |
| created_at | DateTime | 创建时间（索引） |

索引：`idx_notifications_user_read` (user_id, is_read)

### NotificationSettings

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID（唯一） |
| email_enabled | Boolean | 邮件通知开关 |
| sms_enabled | Boolean | 短信通知开关 |
| push_enabled | Boolean | 推送通知开关 |
| quiet_hours_start | String(5) | 免打扰开始时间 |
| quiet_hours_end | String(5) | 免打扰结束时间 |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| user-service | Kafka | 消费用户注册、登录等事件 |
| order-service | Kafka | 消费订单状态变更事件 |
| legal-service | Kafka | 消费法律咨询相关事件 |
| community-service | Kafka | 消费社区互动事件 |
| backend-bff | HTTP | 通过 BFF 代理层对外提供 API |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DATABASE_URL | sqlite+aiosqlite:///./notification_service.db | 数据库连接URL |
| DB_POOL_SIZE | 10 | 数据库连接池大小 |
| DB_MAX_OVERFLOW | 20 | 数据库连接池最大溢出 |
| EMAIL_ENABLED | false | 邮件通知开关 |
| SMS_ENABLED | false | 短信通知开关 |
| PUSH_ENABLED | false | 推送通知开关 |
| OTEL_EXPORTER_OTLP_ENDPOINT | - | OpenTelemetry 链路追踪端点 |
| CONSUL_ENABLED | - | Consul 服务注册开关 |

## 部署信息

- Dockerfile: services/notification-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
