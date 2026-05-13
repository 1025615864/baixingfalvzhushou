# 用户服务 (User Service)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | user-service |
| 端口 | 8001 |
| 基础路径 | /api/v1/users |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis |
| 数据库 | user_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |

## 服务描述

用户服务是系统的核心身份认证与用户管理服务，负责用户注册登录、JWT Token 签发与验证、用户画像管理、会员体系以及账号生命周期管理。支持 Kafka 事件驱动和 gRPC 双协议通信，通过 Outbox 模式确保事件可靠发布。

## API 端点

### 认证 (auth.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/auth/login | 用户登录（手机号+密码），连续5次失败锁定15分钟 | 否 |
| POST | /api/v1/auth/register | 用户注册，密码需至少8位含大小写字母和数字 | 否 |
| POST | /api/v1/auth/refresh | 刷新Token，旧refresh_token被撤销 | 否 |
| GET | /api/v1/auth/me | 获取当前登录用户信息 | 是 |
| GET | /api/v1/auth/.well-known/jwks.json | 获取JWKS公钥，供其他服务验证Token | 否 |

### 邮箱验证 (email_verification.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/auth/email/send-verification | 发送邮箱验证链接 | 否 |
| POST | /api/v1/auth/email/verify | 使用令牌验证邮箱 | 否 |
| GET | /api/v1/auth/email/status | 获取当前用户邮箱验证状态 | 是 |
| POST | /api/v1/auth/email/resend | 重新发送验证邮件（需登录） | 是 |

### 密码重置 (password_reset.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/auth/password/reset | 请求密码重置，发送验证码到手机 | 否 |
| POST | /api/v1/auth/password/reset/confirm | 确认密码重置，使用令牌和新密码完成 | 否 |

### 用户管理 (user.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/users/me | 获取当前用户详情（含Profile） | 是 |
| PATCH | /api/v1/users/me | 更新当前用户核心字段 | 是 |
| GET | /api/v1/users/ | 获取用户列表（分页，仅管理员） | 管理员 |
| GET | /api/v1/users/uid/{uid} | 根据UID获取用户详情（对外唯一标识） | 否 |
| GET | /api/v1/users/{user_id} | 根据ID获取用户详情（内部使用） | 否 |
| DELETE | /api/v1/users/{user_id} | 删除用户（仅管理员） | 管理员 |

### 用户画像 (profile.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/profiles/{user_id} | 获取用户画像 | 否 |
| POST | /api/v1/profiles/ | 创建用户画像 | 是 |
| PATCH | /api/v1/profiles/{user_id} | 更新用户画像 | 是 |
| DELETE | /api/v1/profiles/{user_id} | 删除用户画像 | 是 |
| POST | /api/v1/profiles/avatar/validate | 验证头像URL格式 | 是 |
| POST | /api/v1/profiles/avatar/default | 获取默认头像URL | 是 |

### 会员管理 (membership.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/membership/info | 获取当前用户会员信息 | 是 |
| GET | /api/v1/membership/permissions | 获取当前用户权限列表 | 是 |
| POST | /api/v1/membership/upgrade | 升级会员（VIP/SVIP，1-365天） | 是 |
| POST | /api/v1/membership/cancel | 取消会员资格 | 是 |
| GET | /api/v1/membership/check/{permission} | 检查是否有特定权限 | 是 |

### 账号注销 (account.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/account/deletion/request | 请求账号注销，进入7天冷静期 | 是 |
| POST | /api/v1/account/deletion/cancel | 取消账号注销，恢复账号 | 是 |
| POST | /api/v1/account/deletion/confirm | 确认立即注销（跳过冷静期） | 是 |
| GET | /api/v1/account/deletion/status | 获取注销状态 | 是 |

### 数据导出 (data_export.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/account/data/export | 创建异步数据导出任务（符合个人信息保护法） | 是 |
| GET | /api/v1/account/data/export/{task_id} | 查询导出任务状态和结果 | 是 |
| GET | /api/v1/account/data/export-quick | 快速同步导出个人数据 | 是 |
| GET | /api/v1/account/data/export/preview | 数据导出预览（摘要） | 是 |

### AI会话 (ai_session.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/ai/sessions | 创建新会话 | 否 |
| GET | /api/v1/ai/sessions/{session_id} | 获取会话详情 | 否 |
| PUT | /api/v1/ai/sessions/{session_id} | 更新会话 | 否 |
| DELETE | /api/v1/ai/sessions/{session_id} | 删除会话（软删除） | 否 |
| GET | /api/v1/ai/sessions | 获取用户会话列表（分页） | 否 |
| POST | /api/v1/ai/sessions/{session_id}/messages | 创建新消息 | 否 |
| GET | /api/v1/ai/sessions/{session_id}/messages | 获取会话消息列表 | 否 |
| GET | /api/v1/ai/sessions/{session_id}/history | 获取会话历史（简化格式，用于AI上下文） | 否 |
| GET | /api/v1/ai/users/{user_id}/stats | 获取用户会话统计 | 否 |

### 设备管理 (device.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/devices/register | 注册或更新设备（最多5个） | 是 |
| GET | /api/v1/devices/list | 获取设备列表 | 是 |
| DELETE | /api/v1/devices/{device_id} | 移除指定设备 | 是 |
| DELETE | /api/v1/devices/all | 移除所有设备（可选保留当前设备） | 是 |
| GET | /api/v1/devices/{device_id} | 获取设备信息 | 是 |
| PUT | /api/v1/devices/fcm-token | 更新FCM推送令牌 | 是 |

## 数据模型

| 模型 | 表名 | 说明 |
|------|------|------|
| User | users | 用户主表，含uid/phone/email/role/status/vip过期时间等 |
| UserProfile | user_profiles | 用户画像，含昵称/头像/简介/性别/生日/地区 |
| LoginAudit | login_audits | 登录审计日志，记录IP/设备/位置/成功失败 |
| UserDevice | user_devices | 用户设备绑定，含FCM Token |
| AuditLog | audit_logs | 操作审计日志（仅追加），记录用户操作 |
| ExportTask | export_tasks | 异步数据导出任务，含进度/状态/结果 |
| OutboxEvent | outbox_events | Outbox事件表，确保Kafka事件可靠发布 |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| notification-service | Kafka | 用户注册、密码重置等事件通知 |
| points-service | Kafka | 会员升级、签到等积分事件 |
| backend | HTTP | 前端网关转发请求 |
| ai-service | HTTP/gRPC | AI会话管理、用户验证 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| USER_DATABASE_URL | postgresql+asyncpg://postgres:postgres@localhost:5433/user_service | 数据库连接 |
| REDIS_URL | redis://localhost:16379/0 | Redis连接 |
| REDIS_PASSWORD | (空) | Redis密码 |
| JWT_SECRET_KEY | (随机生成) | JWT签名密钥 |
| JWT_ALGORITHM | HS256 | JWT算法 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30 | Access Token过期时间（分钟） |
| REFRESH_TOKEN_EXPIRE_DAYS | 7 | Refresh Token过期时间（天） |
| KAFKA_BOOTSTRAP_SERVERS | localhost:9092 | Kafka地址 |
| ENABLE_KAFKA | false | 是否启用Kafka |
| CORS_ALLOWED_ORIGINS | http://localhost:3000,http://localhost:5173 | CORS允许来源 |
| ENABLE_GRPC_SERVER | false | 是否启用gRPC服务端 |
| ENABLE_GRPC_CLIENT | false | 是否启用gRPC客户端 |
| ENABLE_OUTBOX | true | 是否启用Outbox事件发布 |
| ENABLE_MEMBERSHIP_EXPIRY_CHECK | true | 是否启用会员过期检查任务 |
| CONSUL_ENABLED | false | 是否启用Consul服务注册 |

## 部署信息

- Dockerfile: services/user-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
